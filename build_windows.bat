@echo off
setlocal EnableDelayedExpansion
title Compilador de Texto a Voz Studio para Windows
color 0b

echo ========================================================
echo        TEXTO A VOZ STUDIO - COMPILADOR WINDOWS
echo ========================================================
echo.

:: 1. Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python no esta instalado o no se encuentra en el PATH.
    echo Por favor instala Python 3.10, 3.11 o 3.12 desde python.org
    echo asegurandote de marcar la casilla "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo [1/4] Verificando entorno de Python...
if not exist "venv_win\" (
    echo Creando entorno virtual 'venv_win'...
    python -m venv venv_win
)

call venv_win\Scripts\activate.bat

:: 2. Instalar dependencias
echo.
echo [2/4] Instalando dependencias necesarias (esto puede tardar un momento)...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 3. Compilar con PyInstaller
echo.
echo [3/4] Compilando aplicacion con PyInstaller...
pyinstaller --clean -y TextoAVoz.spec

if not exist "dist\TextoAVoz\TextoAVoz.exe" (
    color 0c
    echo.
    echo [ERROR] La compilacion con PyInstaller fallo.
    pause
    exit /b 1
)

echo.
echo [EXITO] Compilacion completada: dist\TextoAVoz\TextoAVoz.exe

:: 4. Compilar instalador con Inno Setup (si esta disponible)
echo.
echo [4/4] Buscando Inno Setup para crear el instalador .exe...

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    where ISCC.exe >nul 2>&1
    if !errorlevel! equ 0 (
        set "ISCC=ISCC.exe"
    )
)

if defined ISCC (
    echo Inno Setup detectado en: "!ISCC!"
    echo Creando instalador final...
    "!ISCC!" installer.iss
    echo.
    color 0a
    echo ========================================================
    echo      INSTALADOR CREADO CON EXITO!
    echo ========================================================
    echo Ubicacion del instalador:
    echo   dist\Instalador_TextoAVoz_v1.0.0.exe
    echo.
) else (
    color 0e
    echo [AVISO] Inno Setup 6 no esta instalado.
    echo Tu aplicacion ya esta lista en la carpeta:
    echo   dist\TextoAVoz\
    echo.
    echo Si deseas generar el archivo unico instalador (.exe de instalacion),
    echo descarga gratis Inno Setup 6 desde:
    echo   https://jrsoftware.org/isdl.php
    echo y vuelve a ejecutar este archivo.
    echo.
)

pause
