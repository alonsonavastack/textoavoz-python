# 🎙️ Texto a Voz (Edge-TTS Desktop App)

Aplicación de escritorio moderna y minimalista desarrollada en **Python** con **CustomTkinter** y **Edge-TTS** (Microsoft Edge Text to Speech). Permite convertir texto en audio con voces neuronales ultra-realistas, modular velocidad, tono y volumen, además de exportar a audio de alta calidad.

---

## ✨ Características

- 🗣️ **Voces Neuronales Naturales**: Integración con las voces de Microsoft Edge (incluyendo acentos de México, España, Colombia, Argentina, Estados Unidos, etc.).
- 🎛️ **Control en Tiempo Real**: Ajuste fino de velocidad (Rate), tono (Pitch) y volumen.
- 💾 **Exportación de Audio**: Guarda tus locuciones en formato de audio de alta fidelidad.
- 🎨 **Interfaz Moderna**: Diseñada con modo oscuro elegante y responsivo gracias a CustomTkinter.
- 🚀 **Compilación Automática para Windows**: Flujo integrado de GitHub Actions para generar el instalador `.exe` en la nube.

---

## 🛠️ Requisitos e Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/alonsonavastack/textoavoz-python.git
cd textoavoz-python
```

### 2. Crear entorno virtual e instalar dependencias
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
python app.py
```

---

## 📦 Compilar el Instalador para Windows

Para generar el ejecutable `.exe` y el instalador profesional:

- **En la nube (GitHub Actions)**: Cada vez que haces un `push` a la rama `main`, GitHub compila automáticamente el ejecutable en la pestaña **Actions**.
- **En Windows localmente**: Ejecuta el archivo `build_windows.bat`. Para más detalles consulta [INSTRUCCIONES_WINDOWS.md](INSTRUCCIONES_WINDOWS.md).

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
