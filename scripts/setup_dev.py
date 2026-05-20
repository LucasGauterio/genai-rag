import os
import sys
import subprocess
import shutil
from pathlib import Path

# Helper for text coloring
def print_step(msg):
    print(f"\n=== [STEP] {msg} ===")

def print_success(msg):
    print(f"--> [SUCCESS] {msg}")

def print_error(msg):
    print(f"--> [ERROR] {msg}")

def check_command(cmd, name):
    print(f"Checking if {name} is installed...")
    if shutil.which(cmd) is None:
        print_error(f"{name} ({cmd}) is not found in PATH.")
        return False
    print_success(f"{name} is installed.")
    return True

def main():
    root_dir = Path(__file__).resolve().parent.parent
    os.chdir(root_dir)
    print(f"Working directory set to: {root_dir}")

    # Check prerequisites
    prereqs = [
        ("python", "Python"),
        ("node", "Node.js"),
        ("pnpm", "pnpm"),
        ("docker", "Docker"),
        ("docker-compose", "Docker Compose")
    ]
    
    missing = []
    for cmd, name in prereqs:
        if not check_command(cmd, name):
            # docker-compose might be run as "docker compose" (v2 plugin)
            if cmd == "docker-compose":
                try:
                    result = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
                    if result.returncode == 0:
                        print_success("Docker Compose (v2 plugin) is installed.")
                        continue
                except Exception:
                    pass
            missing.append(name)

    if missing:
        print("\nWARNING: Some prerequisites are missing: " + ", ".join(missing))
        print("Please ensure they are installed to run the entire stack successfully.")

    # Create root .env file if it doesn't exist
    print_step("Setting up root .env file")
    root_env = root_dir / ".env"
    root_example = root_dir / ".env.example"
    if not root_env.exists():
        if root_example.exists():
            shutil.copy(root_example, root_env)
            print_success("Copied .env.example to .env")
        else:
            env_content = """# LLM Provider: 'openrouter' or 'gemini'
LLM_PROVIDER=gemini

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Local Embeddings (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
"""
            root_env.write_text(env_content, encoding="utf-8")
            print_success("Created root .env file with default templates.")
    else:
        print("Root .env file already exists.")

    # Create frontend .env file if it doesn't exist
    print_step("Setting up frontend .env file")
    frontend_dir = root_dir / "frontend"
    frontend_env = frontend_dir / ".env"
    frontend_example = frontend_dir / ".env.example"

    if not frontend_env.exists():
        if frontend_example.exists():
            shutil.copy(frontend_example, frontend_env)
            print_success("Copied frontend/.env.example to frontend/.env")
        else:
            frontend_env.write_text("NUXT_BACKEND_API_URL=http://localhost:5000\n", encoding="utf-8")
            print_success("Created frontend/.env with default backend API URL.")
    else:
        print("Frontend .env file already exists.")

    # Set up Backend Python Virtual Environment
    print_step("Setting up backend virtual environment (venv)")
    backend_app_dir = root_dir / "backend" / "app"
    venv_dir = backend_app_dir / "venv"
    
    if not venv_dir.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print_success("Virtual environment created.")
    else:
        print("Virtual environment already exists.")

    # Identify python executable in venv
    if os.name == "nt":
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"

    # Install Python dependencies
    print_step("Installing backend dependencies")
    req_file = backend_app_dir / "requirements.txt"
    if req_file.exists():
        print(f"Running pip install from: {req_file}")
        subprocess.run([str(pip_path), "install", "-r", str(req_file)], check=True)
        print_success("Backend dependencies installed successfully.")
    else:
        print_error("requirements.txt not found inside backend/app/")

    # Install Frontend Node dependencies
    print_step("Installing frontend dependencies")
    if (frontend_dir / "package.json").exists():
        if shutil.which("pnpm") is not None:
            print("Running pnpm install in frontend...")
            subprocess.run(["pnpm", "install"], cwd=str(frontend_dir), check=True, shell=True)
            print_success("Frontend dependencies installed successfully.")
        else:
            print_error("pnpm is not installed. Skipping frontend dependency installation.")
    else:
        print_error("package.json not found inside frontend/")

    print("\n==========================================")
    print("Setup completed successfully!")
    print("Please fill in your OPENROUTER_API_KEY in the root .env file.")
    print("Then run the app using 'python scripts/run_all.py'")
    print("==========================================\n")

if __name__ == "__main__":
    main()
