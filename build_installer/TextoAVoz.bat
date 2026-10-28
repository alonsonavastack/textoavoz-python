@echo off
setlocal
cd /d "%~dp0"

set "PYW="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    set "PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
) else (
    set "PYW=pythonw.exe"
)

start "" "!PYW!" "%~dp0app.py"
exit /b 0
