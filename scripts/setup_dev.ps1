# PowerShell wrapper to run the Python setup script
# Run this file to prepare your local development environment
# Usage: powershell -ExecutionPolicy Bypass -File .\setup_dev.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir/setup_dev.py"
pause
