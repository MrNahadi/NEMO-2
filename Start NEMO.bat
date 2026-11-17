@echo off
setlocal
cd /d "%~dp0"
title NEMO - close this window to stop NEMO

if not exist "engine\.venv\Scripts\python.exe" (
  echo.
  echo NEMO is not installed yet. Double-click "Install NEMO.bat" first.
  echo.
  pause
  exit /b 1
)
if not exist "app\dist\index.html" (
  echo.
  echo Some NEMO app files are missing. Double-click "Install NEMO.bat" to repair NEMO.
  echo.
  pause
  exit /b 1
)

echo.
echo Starting NEMO. Your web browser will open in a moment.
echo Keep this window open while you use NEMO. Close it to stop NEMO.
echo.
"engine\.venv\Scripts\python.exe" -m nemo.server
if errorlevel 1 (
  echo.
  echo NEMO stopped with an error. If another NEMO window is already open, use that one.
  pause
)
