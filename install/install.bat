@echo off
cd /d "%~dp0"

echo Installing Python package dependencies...
python -m pip install -r requirements.txt

echo.
echo Checking Quanser environment (QLabs, QUARC, Quanser Python SDK)...
python check_environment.py

cd /d "%~dp0.."
