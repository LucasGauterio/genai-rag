import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def print_banner(msg):
    print("\n" + "=" * 50)
    print(f" {msg}")
    print("=" * 50)

def parse_env_file(env_path):
    env_vars = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

def main():
    root_dir = Path(__file__).resolve().parent.parent
    os.chdir(root_dir)

    # 1. Start Docker services (Ollama)
    print_banner("1. Starting Docker Compose Services (Ollama)...")
    
    # Check if docker command is available
    docker_cmd = ["docker", "compose", "up", "-d"]
    try:
        # Try docker compose first
        subprocess.run(docker_cmd, check=True)
    except Exception:
        try:
            # Fallback to docker-compose legacy
            subprocess.run(["docker-compose", "up", "-d"], check=True)
        except Exception as e:
            print(f"Error starting Docker services: {e}")
            print("Please ensure Docker Desktop is running and docker-compose is available.")
            sys.exit(1)

    # 2. Parse environment variables
    root_env_path = root_dir / ".env"
    env_vars = parse_env_file(root_env_path)
    
    # Inherit current process env
    backend_env = os.environ.copy()
    backend_env.update(env_vars)

    provider = backend_env.get("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        gemini_key = backend_env.get("GEMINI_API_KEY") or backend_env.get("GOOGLE_API_KEY")
        if not gemini_key or gemini_key == "your_gemini_api_key_here":
            print("\nWARNING: GEMINI_API_KEY / GOOGLE_API_KEY is not set or is using the default placeholder in your root .env file.")
            print("Flashcard generation and Chat features will fail until you provide a valid API key.")
            print("You can edit the key in the root .env file.\n")
    else:
        if not backend_env.get("OPENROUTER_API_KEY") or backend_env.get("OPENROUTER_API_KEY") == "your_openrouter_api_key_here":
            print("\nWARNING: OPENROUTER_API_KEY is not set or is using the default placeholder in your root .env file.")
            print("Flashcard generation and Chat features will fail until you provide a valid API key.")
            print("You can edit the key in the root .env file.\n")

    # 3. Start Backend Flask Server
    print_banner("2. Starting Backend (Flask Server)...")
    backend_dir = root_dir / "backend" / "app"
    venv_dir = backend_dir / "venv"
    
    if os.name == "nt":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"

    if not python_exe.exists():
        print(f"Python venv not found at {python_exe}.")
        print("Please run setup first: 'python scripts/setup_dev.py'")
        sys.exit(1)

    # We run the flask app by running app.py
    backend_process = subprocess.Popen(
        [str(python_exe), "app.py"],
        cwd=str(backend_dir),
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # 4. Start Frontend Nuxt Server
    print_banner("3. Starting Frontend (Nuxt Dev Server)...")
    frontend_dir = root_dir / "frontend"

    # Start pnpm run dev
    frontend_process = subprocess.Popen(
        ["pnpm", "run", "dev"],
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=True if os.name == "nt" else False
    )

    # Thread/function to stream process output helper
    import threading
    
    def log_streamer(process, prefix):
        for line in iter(process.stdout.readline, ''):
            print(f"[{prefix}] {line.strip()}")
        process.stdout.close()

    # Launch log streaming threads
    backend_thread = threading.Thread(target=log_streamer, args=(backend_process, "BACKEND"), daemon=True)
    frontend_thread = threading.Thread(target=log_streamer, args=(frontend_process, "FRONTEND"), daemon=True)
    
    backend_thread.start()
    frontend_thread.start()

    print_banner("Application Stack Running! Press Ctrl+C to stop.")
    print("Frontend: http://localhost:3000")
    print("Backend:  http://localhost:5000")
    print("Ollama:   http://localhost:11434")
    print("=" * 50 + "\n")

    # Keep script running and monitor subprocesses
    try:
        while True:
            # Check if processes died
            if backend_process.poll() is not None:
                print(f"\nBackend process stopped with exit code {backend_process.returncode}")
                break
            if frontend_process.poll() is not None:
                print(f"\nFrontend process stopped with exit code {frontend_process.returncode}")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print_banner("Stopping all processes...")
    finally:
        # Terminate processes
        try:
            print("Terminating Backend...")
            backend_process.terminate()
            backend_process.wait(timeout=5)
        except Exception:
            backend_process.kill()

        try:
            print("Terminating Frontend...")
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
        except Exception:
            frontend_process.kill()

        print("Stopping Docker services...")
        try:
            subprocess.run(["docker", "compose", "down"], check=True)
        except Exception:
            try:
                subprocess.run(["docker-compose", "down"], check=True)
            except Exception:
                pass

        print_banner("Stack cleanly shut down. Goodbye!")

if __name__ == "__main__":
    main()
