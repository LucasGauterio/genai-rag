# PowerShell wrapper to run the Python local runner script
# Run this file to start Docker Compose, the Flask backend, and the Nuxt frontend
# Usage: powershell -ExecutionPolicy Bypass -File .\run_all.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir/run_all.py"
