"""Motor de voz sin interfaz gráfica: genera WAV a partir de texto/guiones.

Usa las mismas voces, presets y efectos que la app de escritorio (app.py) y lee
los presets guardados en ~/.textoavoz/configuraciones.json, así que "nuestras
propias voces" creadas en la app están disponibles aquí por nombre.
"""
import asyncio
import json
import os
import re
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from math import gcd

import edge_tts
import numpy as np
import soundfile as sf
from scipy import signal as scipy_signal

# ── Voces (mismas que app.py) ────────────────────────────────────────────────
VOCES = {
    "Dalia": "es-MX-DaliaNeural",
    "Carlota": "es-MX-CarlotaNeural",
    "Jorge": "es-MX-JorgeNeural",
    "Liberto": "es-MX-LibertoNeural",
    "Luciano": "es-MX-LucianoNeural",
    "Pelayo": "es-MX-PelayoNeural",
}
VOZ_DEFAULT = "es-MX-DaliaNeural"

# ── Presets (mismos que app.py; voz=None → la que se elija) ──────────────────
PRESETS_DEFAULT = {
    "Normal":         dict(vel=0,   pit=0,   vol=1.0, rob=0,    eco=0,   rev=0,   dist=0,   cho=0,   tel=0),
    "Jarvis IA":      dict(vel=-8,  pit=-8,  vol=1.0, rob=0.35, eco=0.2, rev=0.3, dist=0,   cho=0.1, tel=0),
    "ARIA Futurista": dict(vel=5,   pit=6,   vol=1.0, rob=0.5,  eco=0.4, rev=0.2, dist=0.1, cho=0.3, tel=0),
    "Voz Grave":      dict(vel=-15, pit=-18, vol=1.0, rob=0,    eco=0,   rev=0.2, dist=0,   cho=0,   tel=0),
    "Voz Suave":      dict(vel=-5,  pit=4,   vol=0.9, rob=0,    eco=0.1, rev=0.3, dist=0,   cho=0.2, tel=0),
    "Narrador":       dict(vel=-10, pit=-4,  vol=1.0, rob=0,    eco=0,   rev=0.15, dist=0,  cho=0,   tel=0),
    "Lento y Claro":  dict(vel=-35, pit=0,   vol=1.0, rob=0,    eco=0,   rev=0,   dist=0,   cho=0,   tel=0),
    "Enérgico":       dict(vel=22,  pit=3,   vol=1.2, rob=0,    eco=0,   rev=0,   dist=0.1, cho=0.1, tel=0),
    "Fantasma":       dict(vel=-20, pit=-6,  vol=0.8, rob=0.2,  eco=0.7, rev=0.8, dist=0,   cho=0.4, tel=0),
    "Teléfono Viejo": dict(vel=0,   pit=0,   vol=1.0, rob=0,    eco=0.1, rev=0,   dist=0.2, cho=0,   tel=0.9),
    "Cueva":          dict(vel=-10, pit=-3,  vol=1.0, rob=0,    eco=0.6, rev=0.9, dist=0,   cho=0,   tel=0),
    "Demonio":        dict(vel=-20, pit=-20, vol=1.1, rob=0.6,  eco=0.3, rev=0.5, dist=0.5, cho=0,   tel=0),
}


def _ruta_config():
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "TextoAVoz", "configuraciones.json")
    return os.path.join(os.path.expanduser("~"), ".textoavoz", "configuraciones.json")


def cargar_presets():
    """Presets por defecto + los personalizados guardados desde la app."""
    presets = {k: dict(v) for k, v in PRESETS_DEFAULT.items()}
    ruta = _ruta_config()
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                presets.update(json.load(f).get("personalizados", {}))
        except Exception:
            pass
    return presets


def _norm(s):
    return " ".join(str(s).split()).lower()


def resolver_voz(voz):
    """Acepta 'Dalia', 'es-MX-DaliaNeural' o una etiqueta de la app ('⭐ Dalia · MX Mujer')."""
    if not voz:
        return VOZ_DEFAULT
    if re.match(r"^[a-z]{2}-[A-Z]{2}-\w+Neural$", voz):
        return voz
    n = _norm(voz)
    for nombre, vid in VOCES.items():
        if nombre.lower() in n:
            return vid
    return VOZ_DEFAULT


def resolver_preset(preset, presets=None):
    presets = presets or cargar_presets()
    if preset in presets:
        return preset, presets[preset]
    n = _norm(preset or "Normal")
    for k, v in presets.items():
        if _norm(k) == n:
            return k, v
    raise ValueError(f"Preset '{preset}' no existe. Disponibles: {', '.join(presets)}")


# ── Efectos (copia de app.py → aplicar_efectos) ──────────────────────────────
def aplicar_efectos(data, sr, efectos):
    semitones = efectos.get("pitch", 0)
    if semitones != 0:
        factor = 2 ** (semitones / 12.0)
        idx = np.round(np.arange(0, len(data), factor)).astype(int)
        idx = idx[idx < len(data)]
        data = data[idx]

    robot = efectos.get("robot", 0.0)
    if robot > 0:
        t = np.arange(len(data)) / sr
        carrier = np.sign(np.sin(2 * np.pi * (80 + robot * 40) * t))
        data = data * (1 - robot * 0.6) + data * carrier * robot * 0.6

    eco = efectos.get("eco", 0.0)
    if eco > 0:
        ds = int(sr * 0.25)
        buf = np.zeros(len(data) + ds)
        buf[:len(data)] += data
        buf[ds:] += data * eco * 0.6
        data = buf[:len(data)]

    reverb = efectos.get("reverb", 0.0)
    if reverb > 0:
        decay = int(sr * reverb * 1.5)
        impulso = np.exp(-np.linspace(0, 8, decay)) * np.random.randn(decay) * 0.3
        data = scipy_signal.fftconvolve(data, impulso, mode="full")[:len(data)]

    dist = efectos.get("distorsion", 0.0)
    if dist > 0:
        data = np.tanh(data * (1 + dist * 8)) / (1 + dist * 0.5)

    chorus = efectos.get("chorus", 0.0)
    if chorus > 0:
        factor2 = 2 ** (0.15 / 12.0)
        idx2 = np.round(np.arange(0, len(data), factor2)).astype(int)
        idx2 = idx2[idx2 < len(data)]
        voz2 = np.zeros(len(data))
        voz2[:len(idx2)] = data[idx2]
        data = data * (1 - chorus * 0.4) + voz2 * chorus * 0.4

    telefono = efectos.get("telefono", 0.0)
    if telefono > 0:
        sos_lo = scipy_signal.butter(4, 3400 / (sr / 2), btype="low", output="sos")
        sos_hi = scipy_signal.butter(4, 300 / (sr / 2), btype="high", output="sos")
        fil = scipy_signal.sosfilt(sos_hi, scipy_signal.sosfilt(sos_lo, data))
        data = data * (1 - telefono) + fil * telefono

    data = data * max(0.0, min(2.0, efectos.get("volume", 1.0)))
    mx = np.max(np.abs(data))
    if mx > 0.98:
        data = data / mx * 0.95
    return data.astype(np.float32)


# ── Síntesis ─────────────────────────────────────────────────────────────────
async def _edge_a_mp3(texto, voz_id, vel, pit, path):
    com = edge_tts.Communicate(texto, voz_id, rate=f"{vel:+d}%", pitch=f"{pit:+d}Hz")
    await com.save(path)


def sintetizar(texto, preset="Normal", voz=None, vel=None, pit=None, vol=None, sample_rate=48000):
    """Devuelve (audio float32 mono, sample_rate). Los parámetros sueltos pisan al preset."""
    nombre, p = resolver_preset(preset)
    voz_id = resolver_voz(voz or p.get("voz"))
    vel = int(p.get("vel", 0) if vel is None else vel)
    pit = int(p.get("pit", 0) if pit is None else pit)
    vol = float(p.get("vol", 1.0) if vol is None else vol)
    efectos = dict(
        pitch=pit, volume=vol,
        robot=p.get("rob", 0), eco=p.get("eco", 0), reverb=p.get("rev", 0),
        distorsion=p.get("dist", 0), chorus=p.get("cho", 0), telefono=p.get("tel", 0),
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        # En un hilo propio: así funciona también dentro del servidor MCP (que ya tiene un bucle asyncio)
        with ThreadPoolExecutor(max_workers=1) as ex:
            ex.submit(lambda: asyncio.run(_edge_a_mp3(texto, voz_id, vel, pit, tmp.name))).result()
        data, sr = sf.read(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    if data.ndim > 1:
        data = data.mean(axis=1)
    data = aplicar_efectos(data, sr, efectos)

    if sample_rate and sample_rate != sr:
        g = gcd(int(sample_rate), int(sr))
        data = scipy_signal.resample_poly(data, int(sample_rate) // g, int(sr) // g).astype(np.float32)
        sr = int(sample_rate)
    return data, sr


def generar_wav(texto, destino, **kw):
    """Genera un WAV (PCM 16-bit mono) y devuelve info con la duración exacta."""
    data, sr = sintetizar(texto, **kw)
    os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
    sf.write(destino, data, sr, subtype="PCM_16")
    return {"archivo": os.path.abspath(destino), "duracion_s": round(len(data) / sr, 3), "sample_rate": sr}


def generar_guion(escenas, carpeta, pausa_s=0.4, unir=True, **kw):
    """Genera un WAV por escena (+ uno unido) y un manifest.json con tiempos.

    `escenas`: lista de str o de dicts {"texto": ..., "id": ..., "preset": ..., "voz": ...}.
    El manifest da inicio/fin de cada escena para sincronizar la animación con la voz.
    """
    os.makedirs(carpeta, exist_ok=True)
    salida, tiempos, trozos = [], [], []
    cursor, sr_out = 0.0, None
    for i, esc in enumerate(escenas, 1):
        esc = {"texto": esc} if isinstance(esc, str) else dict(esc)
        eid = re.sub(r"[^\w\-]", "_", str(esc.get("id") or f"escena_{i:02d}"))
        args = dict(kw)
        for k in ("preset", "voz", "vel", "pit", "vol"):
            if k in esc:
                args[k] = esc[k]
        data, sr = sintetizar(esc["texto"], **args)
        sr_out = sr
        ruta = os.path.join(carpeta, f"{eid}.wav")
        sf.write(ruta, data, sr, subtype="PCM_16")
        dur = len(data) / sr
        salida.append({
            "id": eid, "texto": esc["texto"], "archivo": os.path.abspath(ruta),
            "duracion_s": round(dur, 3),
            "inicio_s": round(cursor, 3), "fin_s": round(cursor + dur, 3),
        })
        trozos.append(data)
        cursor += dur + pausa_s
        tiempos.append(dur)

    manifest = {"sample_rate": sr_out, "pausa_s": pausa_s, "escenas": salida}
    if unir and trozos:
        silencio = np.zeros(int(sr_out * pausa_s), dtype=np.float32)
        partes = []
        for j, t in enumerate(trozos):
            partes.append(t)
            if j < len(trozos) - 1:
                partes.append(silencio)
        full = np.concatenate(partes)
        ruta_full = os.path.join(carpeta, "voz_completa.wav")
        sf.write(ruta_full, full, sr_out, subtype="PCM_16")
        manifest["voz_completa"] = os.path.abspath(ruta_full)
        manifest["duracion_total_s"] = round(len(full) / sr_out, 3)
    with open(os.path.join(carpeta, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def listar():
    return {"voces": VOCES, "presets": list(cargar_presets().keys())}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Texto a Voz → WAV (mismas voces/efectos que la app)")
    ap.add_argument("--texto", help="Texto a locutar")
    ap.add_argument("--guion", help="Archivo .json (lista de escenas) o .txt (una escena por párrafo)")
    ap.add_argument("--salida", default="voz.wav", help="WAV de salida, o carpeta si usas --guion")
    ap.add_argument("--preset", default="Normal")
    ap.add_argument("--voz")
    ap.add_argument("--pausa", type=float, default=0.4)
    ap.add_argument("--listar", action="store_true")
    a = ap.parse_args()

    if a.listar:
        print(json.dumps(listar(), ensure_ascii=False, indent=2))
    elif a.guion:
        raw = open(a.guion, encoding="utf-8").read()
        escenas = json.loads(raw) if a.guion.endswith(".json") else [p.strip() for p in raw.split("\n\n") if p.strip()]
        print(json.dumps(generar_guion(escenas, a.salida, pausa_s=a.pausa, preset=a.preset, voz=a.voz),
                         ensure_ascii=False, indent=2))
    elif a.texto:
        print(json.dumps(generar_wav(a.texto, a.salida, preset=a.preset, voz=a.voz), ensure_ascii=False, indent=2))
    else:
        ap.print_help()
        sys.exit(1)
