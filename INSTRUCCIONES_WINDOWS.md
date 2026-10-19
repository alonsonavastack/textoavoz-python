# 🚀 Guía: Cómo Generar el Instalador para Windows (.exe)

Este proyecto está completamente configurado para compilar tanto una **versión ejecutable directa** como un **instalador profesional para Windows** (con acceso directo en el escritorio, menú inicio y desinstalador limpio).

---

## 📁 Archivos creados y configurados

- **`build_windows.bat`**: Script de 1 clic para compilar en cualquier computadora con Windows.
- **`TextoAVoz.spec`**: Configuración optimizada de PyInstaller que empaqueta CustomTkinter, SoundDevice, SoundFile, Edge-TTS, SciPy y los iconos.
- **`installer.iss`**: Script de **Inno Setup** para compilar el instalador profesional en español (`Instalador_TextoAVoz_v1.0.0.exe`).
- **`.github/workflows/build-windows.yml`**: Flujo de GitHub Actions para compilar el `.exe` **gratis y 100% en la nube** (ideal si trabajas desde macOS).
- **`assets/icon.ico` / `assets/icon.png`**: Iconos de alta resolución integrados a la aplicación y al instalador.
- **`requirements.txt`**: Dependencias exactas requeridas para el proyecto.

---

## ⚡ Método 1: Compilar en la Nube con GitHub (Recomendado desde Mac)

Como tu sistema operativo actual es macOS, no necesitas instalar Windows ni máquinas virtuales. Puedes compilarlo con **GitHub Actions** en minutos:

1. **Sube este proyecto a un repositorio en GitHub** (puede ser privado o público):
   ```bash
   git init
   git add .
   git commit -m "Configuracion completa para ejecutable Windows"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
   git push -u origin main
   ```

2. Entra a tu repositorio en GitHub y ve a la pestaña **Actions**.
3. Verás la tarea **Compilar para Windows** ejecutándose automáticamente en un servidor Windows oficial de GitHub.
4. Al terminar (tarda ~3 minutos), entra a la ejecución y en la sección **Artifacts** encontrarás listos para descargar:
   - 📦 **`Instalador-TextoAVoz-Windows`** (El instalador `.exe`)
   - 📁 **`TextoAVoz-Windows-Portable`** (Versión portable comprimida en ZIP)

---

## 💻 Método 2: Compilar Directamente en una PC con Windows

Si tienes acceso a una computadora con Windows o una máquina virtual:

1. **Copia la carpeta del proyecto** a la máquina con Windows.
2. Asegúrate de tener instalado **Python 3.10, 3.11 o 3.12** ([python.org](https://www.python.org/downloads/)) con la casilla **"Add Python to PATH"** activada.
3. *(Opcional pero recomendado)* Descarga e instala **Inno Setup 6** (gratis):
   👉 [https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)
4. Haz **doble clic en `build_windows.bat`**.

El script se encargará automáticamente de:
- Crear el entorno virtual e instalar las librerías necesarias.
- Compilar la aplicación con PyInstaller.
- Generar el instalador `.exe` en la carpeta `dist/Instalador_TextoAVoz_v1.0.0.exe`.

---

## 🛠️ Mejoras aplicadas en el código (`app.py`)

1. **Ruta segura para configuraciones**: Ahora `configuraciones.json` se almacena automáticamente en `%APPDATA%\TextoAVoz\`, evitando errores de permisos en `C:\Program Files\` y asegurando que tus presets personalizados nunca se borren.
2. **Icono nativo**: Se vinculó el icono generado en `assets/icon.ico` a la barra de título de la aplicación.
3. **Cierre seguro**: El subproceso de síntesis y reproducción de audio se finaliza limpiamente al cerrar la ventana.
