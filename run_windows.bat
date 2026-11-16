@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Hay chay setup_windows.bat truoc.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m unittest discover -s tests -v
if errorlevel 1 (
  echo Test that bai.
  pause
  exit /b 1
)
.venv\Scripts\python.exe run_project.py
pause
