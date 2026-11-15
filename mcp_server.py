"""Servidor MCP: permite a Claude Code generar voz (WAV) con las voces y presets de TextoAVoz."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

import voz_core

mcp = FastMCP("textoavoz")

SALIDA_DEFAULT = os.path.join(os.path.expanduser("~"), "Desktop", "textoavoz-audios")


def _destino(ruta, nombre_default):
    ruta = ruta or os.path.join(SALIDA_DEFAULT, nombre_default)
    return os.path.expanduser(ruta)


@mcp.tool()
def listar_voces() -> dict:
    """Lista las voces disponibles y los presets (incluye las configuraciones guardadas en la app)."""
    return voz_core.listar()


@mcp.tool()
def generar_voz(texto: str, ruta_wav: str = "", preset: str = "Normal", voz: str = "",
                velocidad: int | None = None, tono: int | None = None, volumen: float | None = None) -> dict:
    """Genera un WAV (mono, 48 kHz) con una voz.

    ruta_wav: ruta completa del .wav (si se omite se guarda en ~/Desktop/textoavoz-audios/voz.wav).
    preset: nombre de una configuración de la app (ej. "Narrador", "Jarvis IA", "Dalia para devhubsharks").
    voz: "Dalia", "Jorge", etc. (si se omite se usa la del preset).
    velocidad/tono/volumen opcionales para pisar el preset.
    Devuelve el archivo y su duración exacta en segundos.
    """
    return voz_core.generar_wav(
        texto, _destino(ruta_wav, "voz.wav"), preset=preset, voz=voz or None,
        vel=velocidad, pit=tono, vol=volumen)


@mcp.tool()
def generar_guion(escenas: list[str | dict], carpeta: str = "", preset: str = "Normal", voz: str = "",
                  pausa_s: float = 0.4) -> dict:
    """Genera un WAV por escena + 'voz_completa.wav' + manifest.json con inicio/fin/duración de cada escena.

    Úsalo para sincronizar un reel/video: cada escena puede ser un texto o un dict
    {"id": "intro", "texto": "...", "preset": "...", "voz": "..."}. Con los tiempos del
    manifest se ajusta la animación a la voz.
    """
    return voz_core.generar_guion(
        escenas, _destino(carpeta, "guion"), pausa_s=pausa_s, preset=preset, voz=voz or None)


if __name__ == "__main__":
    mcp.run()
