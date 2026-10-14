@echo off
cd /d "%~dp0"
set PY=
py -3 --version >nul 2>nul && set PY=py -3
if not defined PY (
  python --version >nul 2>nul && set PY=python
)
if not defined PY (
  echo.
  echo  Python is not installed on this computer.
  echo  1. Install Python 3.12 from https://www.python.org/downloads/
  echo  2. On the FIRST screen of the installer, tick "Add python.exe to PATH"
  echo  3. Close this window and double-click start.bat again.
  echo.
  start https://www.python.org/downloads/
  pause
  exit /b 1
)
if not exist .venv (
  echo First run: setting up, please wait a few minutes...
  %PY% -m venv .venv
  call .venv\Scripts\activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
python run.py
pause
