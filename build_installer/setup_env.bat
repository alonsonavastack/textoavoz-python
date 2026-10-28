@echo off
setlocal EnableDelayedExpansion

echo ========================================================
echo     Configurando entorno de Texto a Voz Studio...
echo ========================================================

:: 1. Detectar si Python ya esta disponible
set "PY_CMD="

where python >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%i in ('where python') do (
        if not defined PY_CMD set "PY_CMD=%%i"
    )
)

:: Buscar en rutas estandar de usuario
if not defined PY_CMD (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    ) else if exist "C:\Python312\python.exe" (
        set "PY_CMD=C:\Python312\python.exe"
    )
)

:: Si no se encuentra, instalar silenciosamente el paquete oficial de Python
if not defined PY_CMD (
    echo [1/2] Instalando Python 3.12 silenciosamente para el usuario...
    if exist "%~dp0python-installer.exe" (
        start /wait "" "%~dp0python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 SimpleInstall=1 Include_test=0 Include_doc=0 Include_tcltk=1
        timeout /t 2 >nul
    )
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else (
        where python >nul 2>&1
        if !errorlevel! equ 0 (
            set "PY_CMD=python"
        )
    )
)

if not defined PY_CMD (
    echo [ERROR] No se pudo encontrar ni instalar Python.
    exit /b 1
)

echo Python detectado en: "!PY_CMD!"

:: 2. Instalar dependencias desde los paquetes locales (rapido y 100% offline)
echo [2/2] Instalando paquetes y dependencias de audio e interfaz...
"!PY_CMD!" -m pip install --no-index --find-links="%~dp0wheels" -r "%~dp0..\requirements.txt"

echo Entorno listo!
exit /b 0
