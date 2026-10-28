import os
import sys

# Configurar rutas de Tcl/Tk para entorno embebido o empaquetado en Windows
if os.name == "nt":
    base_py = os.path.dirname(sys.executable)
    tcl_cand = os.path.join(base_py, "tcl", "tcl8.6")
    tk_cand = os.path.join(base_py, "tcl", "tk8.6")
    if os.path.exists(tcl_cand):
        os.environ.setdefault("TCL_LIBRARY", tcl_cand)
    if os.path.exists(tk_cand):
        os.environ.setdefault("TK_LIBRARY", tk_cand)

import customtkinter as ctk
import multiprocessing
import asyncio
import edge_tts
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile
import time
import json
import shutil
from scipy import signal as scipy_signal

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def obtener_ruta_config():
    """Retorna la ruta segura donde guardar configuraciones.json (compatible con instalador y PyInstaller)."""
    if os.name == "nt":
        base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        app_dir = os.path.join(base_dir, "TextoAVoz")
    else:
        app_dir = os.path.join(os.path.expanduser("~"), ".textoavoz")

    try:
        os.makedirs(app_dir, exist_ok=True)
    except Exception:
        pass

    ruta_usuario = os.path.join(app_dir, "configuraciones.json")

    # Si no existe en la carpeta del usuario, copiar la semilla si existe
    if not os.path.exists(ruta_usuario):
        posibles = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "configuraciones.json"),
            os.path.join(os.getcwd(), "configuraciones.json")
        ]
        if hasattr(sys, "_MEIPASS"):
            posibles.insert(0, os.path.join(sys._MEIPASS, "configuraciones.json"))

        for p in posibles:
            if os.path.exists(p):
                try:
                    shutil.copy2(p, ruta_usuario)
                    break
                except Exception:
                    return p
    return ruta_usuario

CONFIG_PATH = obtener_ruta_config()

VOCES = {
    # ── México · Mujeres (confirmadas) ───────────────────────────────────────
    "⭐ Dalia    · MX Mujer":    "es-MX-DaliaNeural",
    "Carlota    · MX Mujer":    "es-MX-CarlotaNeural",
    # ── México · Hombres (confirmados) ───────────────────────────────────────
    "Jorge      · MX Hombre":   "es-MX-JorgeNeural",
    "Liberto    · MX Hombre":   "es-MX-LibertoNeural",
    "Luciano    · MX Hombre":   "es-MX-LucianoNeural",
    "Pelayo     · MX Hombre":   "es-MX-PelayoNeural",
}

def obtener_voz_id(nombre_seleccionado):
    if not nombre_seleccionado:
        return "es-MX-DaliaNeural"
    if nombre_seleccionado in VOCES:
        return VOCES[nombre_seleccionado]
    norm_sel = " ".join(nombre_seleccionado.split()).lower()
    for k, v in VOCES.items():
        if " ".join(k.split()).lower() == norm_sel:
            return v
    for k, v in VOCES.items():
        nom = v.replace("es-MX-", "").replace("Neural", "").lower()
        if nom in norm_sel:
            return v
    return "es-MX-DaliaNeural"

VOZ_DEFAULT_KEY = list(VOCES.keys())[0]

PRESETS_DEFAULT = {
    "Normal":         dict(vel=0,   pit=0,   vol=1.0, rob=0,    eco=0,   rev=0,   dist=0,   cho=0,   tel=0,   voz=VOZ_DEFAULT_KEY),
    "Jarvis IA":      dict(vel=-8,  pit=-8,  vol=1.0, rob=0.35, eco=0.2, rev=0.3, dist=0,   cho=0.1, tel=0,   voz=VOZ_DEFAULT_KEY),
    "ARIA Futurista": dict(vel=5,   pit=6,   vol=1.0, rob=0.5,  eco=0.4, rev=0.2, dist=0.1, cho=0.3, tel=0,   voz=VOZ_DEFAULT_KEY),
    "Voz Grave":      dict(vel=-15, pit=-18, vol=1.0, rob=0,    eco=0,   rev=0.2, dist=0,   cho=0,   tel=0,   voz=VOZ_DEFAULT_KEY),
    "Voz Suave":      dict(vel=-5,  pit=4,   vol=0.9, rob=0,    eco=0.1, rev=0.3, dist=0,   cho=0.2, tel=0,   voz=VOZ_DEFAULT_KEY),
    "Narrador":       dict(vel=-10, pit=-4,  vol=1.0, rob=0,    eco=0,   rev=0.15,dist=0,   cho=0,   tel=0,   voz=VOZ_DEFAULT_KEY),
    "Lento y Claro":  dict(vel=-35, pit=0,   vol=1.0, rob=0,    eco=0,   rev=0,   dist=0,   cho=0,   tel=0,   voz=VOZ_DEFAULT_KEY),
    "Enérgico":       dict(vel=22,  pit=3,   vol=1.2, rob=0,    eco=0,   rev=0,   dist=0.1, cho=0.1, tel=0,   voz=VOZ_DEFAULT_KEY),
    "Fantasma":       dict(vel=-20, pit=-6,  vol=0.8, rob=0.2,  eco=0.7, rev=0.8, dist=0,   cho=0.4, tel=0,   voz=VOZ_DEFAULT_KEY),
    "Teléfono Viejo": dict(vel=0,   pit=0,   vol=1.0, rob=0,    eco=0.1, rev=0,   dist=0.2, cho=0,   tel=0.9, voz=VOZ_DEFAULT_KEY),
    "Cueva":          dict(vel=-10, pit=-3,  vol=1.0, rob=0,    eco=0.6, rev=0.9, dist=0,   cho=0,   tel=0,   voz=VOZ_DEFAULT_KEY),
    "Demonio":        dict(vel=-20, pit=-20, vol=1.1, rob=0.6,  eco=0.3, rev=0.5, dist=0.5, cho=0,   tel=0,   voz=VOZ_DEFAULT_KEY),
}

# ── Persistencia ──────────────────────────────────────────────────────────────
def cargar_configs():
    global CONFIG_PATH
    if not CONFIG_PATH or not os.path.exists(CONFIG_PATH):
        CONFIG_PATH = obtener_ruta_config()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Mezclar con defaults para que siempre existan los predefinidos
                merged = dict(PRESETS_DEFAULT)
                merged.update(data.get("personalizados", {}))
                ultima = data.get("ultima", {})
                return merged, ultima
        except Exception:
            pass
    return dict(PRESETS_DEFAULT), {}

def guardar_configs(configs, ultima, presets_default_keys):
    global CONFIG_PATH
    try:
        if not CONFIG_PATH:
            CONFIG_PATH = obtener_ruta_config()
        # Solo guardar los personalizados (no los default)
        personalizados = {k: v for k, v in configs.items() if k not in presets_default_keys}
        data = {"personalizados": personalizados, "ultima": ultima}
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Aviso] No se pudo guardar configuraciones.json: {e}")

# ── Efectos ───────────────────────────────────────────────────────────────────
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
        data = scipy_signal.fftconvolve(data, impulso, mode='full')[:len(data)]

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
        sos_lo = scipy_signal.butter(4, 3400 / (sr/2), btype='low',  output='sos')
        sos_hi = scipy_signal.butter(4, 300  / (sr/2), btype='high', output='sos')
        fil = scipy_signal.sosfilt(sos_hi, scipy_signal.sosfilt(sos_lo, data))
        data = data * (1 - telefono) + fil * telefono

    data = data * max(0.0, min(2.0, efectos.get("volume", 1.0)))
    mx = np.max(np.abs(data))
    if mx > 0.98:
        data = data / mx * 0.95
    return data.astype(np.float32)

# ── Worker ────────────────────────────────────────────────────────────────────
def _worker(texto, voz_id, rate_offset, efectos_dict, cola):
    try:
        async def generar():
            com = edge_tts.Communicate(texto, voz_id,
                                       rate=f"{rate_offset:+d}%",
                                       pitch=f"{efectos_dict.get('pitch',0):+d}Hz")
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            path = tmp.name; tmp.close()
            await com.save(path)
            return path
        path = asyncio.run(generar())
        for _ in range(40):
            if os.path.exists(path) and os.path.getsize(path) > 500:
                break
            time.sleep(0.1)
        data, sr = sf.read(path)
        if data.ndim > 1:
            data = data.mean(axis=1)
        data = aplicar_efectos(data, sr, efectos_dict)
        os.unlink(path)
        sd.play(data, sr); sd.wait()
        cola.put("done")
    except Exception as e:
        cola.put(f"error:{e}")

# ── App ───────────────────────────────────────────────────────────────────────
class TextoAVozApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Texto a Voz — Studio")
        self.geometry("1200x900")
        self.resizable(True, True)
        self.after(0, lambda: self.state("zoomed"))
        self.configure(fg_color="#080808")
        self.proceso = None
        self.cola_estado = None
        self.configs, self.ultima = cargar_configs()
        self.preset_default_keys = list(PRESETS_DEFAULT.keys())
        self._establecer_icono()
        self._construir_ui()
        if self.ultima:
            self._cargar_estado(self.ultima)
        self._poll_proceso()
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    def _establecer_icono(self):
        try:
            base_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
                os.path.join(os.getcwd(), "assets")
            ]
            if hasattr(sys, "_MEIPASS"):
                base_paths.insert(0, os.path.join(sys._MEIPASS, "assets"))

            ico_file = None
            png_file = None
            for p in base_paths:
                ico_cand = os.path.join(p, "icon.ico")
                png_cand = os.path.join(p, "icon.png")
                if os.path.exists(ico_cand) and not ico_file:
                    ico_file = ico_cand
                if os.path.exists(png_cand) and not png_file:
                    png_file = png_cand

            if os.name == "nt" and ico_file:
                self.iconbitmap(ico_file)
            elif png_file:
                import tkinter as tk
                img = tk.PhotoImage(file=png_file)
                self.iconphoto(False, img)
        except Exception:
            pass

    # ── UI ────────────────────────────────────────────────────────────────────
    def _construir_ui(self):
        ctk.CTkLabel(self, text="🎙️  Texto a Voz  Studio",
                     font=ctk.CTkFont("Segoe UI", 27, "bold"),
                     text_color="#00cfff").pack(pady=(24,2))
        ctk.CTkLabel(self, text="Edge TTS · Voz natural · Efectos · Configuraciones guardadas",
                     font=ctk.CTkFont(size=11), text_color="#333333").pack(pady=(0,12))

        self.texto_input = ctk.CTkTextbox(
            self, height=165, font=ctk.CTkFont(size=14),
            fg_color="#101010", border_color="#1c1c1c", border_width=2,
            text_color="#e0e0e0", corner_radius=10)
        self.texto_input.pack(pady=(0,12), padx=25, fill="x")
        self.texto_input.insert("0.0", "Escribe aquí el texto que deseas escuchar...")

        # ── Voz + Preset ──────────────────────────────────────────────────
        p1 = self._panel()
        ctk.CTkLabel(p1, text="🗣  Voz", **self._ls()).grid(row=0, column=0, padx=20, pady=(12,2), sticky="w")
        self.combo_voz = ctk.CTkComboBox(p1, values=list(VOCES.keys()), width=320, **self._cs())
        self.combo_voz.set(VOZ_DEFAULT_KEY)
        self.combo_voz.grid(row=1, column=0, padx=20, pady=(0,12))

        ctk.CTkLabel(p1, text="🎭  Configuración", **self._ls()).grid(row=0, column=1, padx=20, pady=(12,2), sticky="w")
        frame_load = ctk.CTkFrame(p1, fg_color="transparent")
        frame_load.grid(row=1, column=1, padx=20, pady=(0,12))
        self.combo_preset = ctk.CTkComboBox(
            frame_load, values=list(self.configs.keys()), width=240,
            **self._cs())
        self.combo_preset.set("Normal")
        self.combo_preset.pack(side="left", padx=(0,6))
        ctk.CTkButton(
            frame_load, text="📂 Cargar",
            width=95, height=32, corner_radius=8,
            fg_color="#1a2a1a", hover_color="#2a3a2a",
            border_color="#336633", border_width=1,
            text_color="#00ff99", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._cargar_seleccion
        ).pack(side="left")

        # Botones guardar/eliminar config
        frame_cfg = ctk.CTkFrame(p1, fg_color="transparent")
        frame_cfg.grid(row=1, column=2, padx=10, pady=(0,12))

        self.entry_nombre = ctk.CTkEntry(
            frame_cfg, placeholder_text="Nombre nueva config...",
            width=220, font=ctk.CTkFont(size=12),
            fg_color="#141414", border_color="#2a2a2a", text_color="#fff")
        self.entry_nombre.pack(side="left", padx=(0,6))

        ctk.CTkButton(frame_cfg, text="💾 Guardar",
                      width=90, height=32, corner_radius=8,
                      fg_color="#00cfff", hover_color="#0099cc",
                      text_color="#000", font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._guardar_config).pack(side="left", padx=(0,4))

        ctk.CTkButton(frame_cfg, text="🗑 Borrar",
                      width=80, height=32, corner_radius=8,
                      fg_color="#2a1010", hover_color="#3a1515",
                      border_color="#551111", border_width=1,
                      text_color="#ff5555", font=ctk.CTkFont(size=12),
                      command=self._borrar_config).pack(side="left")

        # ── Velocidad / Volumen / Tono ────────────────────────────────────
        p2 = self._panel()
        self._sc(p2, "🚀 Velocidad", "sv_vel","lv_vel", -50,100,  0, lambda v:f"{int(v):+d}%",  "#00cfff", 0)
        self._sc(p2, "🔊 Volumen",   "sv_vol","lv_vol",   0,  2,  1, lambda v:f"{int(v*100)}%", "#00cfff", 2)
        self._sc(p2, "🎵 Tono",      "sv_pit","lv_pit", -20, 20,  0, lambda v:f"{int(v):+d}Hz", "#00cfff", 4)

        # ── Efectos ───────────────────────────────────────────────────────
        p3 = self._panel()
        ctk.CTkLabel(p3, text="⚡  Efectos de Voz",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#00cfff").grid(row=0, column=0, columnspan=6, padx=20, pady=(12,4), sticky="w")
        self._sc(p3, "🤖 Robot",    "sv_rob", "lv_rob", 0,1,0, lambda v:f"{int(v*100)}%", "#ff4cff", 0, row=1)
        self._sc(p3, "🌀 Eco",      "sv_eco", "lv_eco", 0,1,0, lambda v:f"{int(v*100)}%", "#ff9500", 2, row=1)
        self._sc(p3, "🏛️ Reverb",  "sv_rev", "lv_rev", 0,1,0, lambda v:f"{int(v*100)}%", "#5599ff", 4, row=1)

        p4 = self._panel()
        self._sc(p4, "⚡ Distorsión","sv_dist","lv_dist",0,1,0, lambda v:f"{int(v*100)}%", "#ff3333", 0)
        self._sc(p4, "🎻 Chorus",   "sv_cho", "lv_cho", 0,1,0, lambda v:f"{int(v*100)}%", "#00ffcc", 2)
        self._sc(p4, "📞 Teléfono", "sv_tel", "lv_tel", 0,1,0, lambda v:f"{int(v*100)}%", "#ffdd00", 4)

        # ── Botones reproducción ──────────────────────────────────────────
        fb = ctk.CTkFrame(self, fg_color="transparent")
        fb.pack(pady=(10,6))

        self.btn_hablar = ctk.CTkButton(
            fb, text="▶  Reproducir", width=300, height=52, corner_radius=12,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#00cfff", hover_color="#0099cc", text_color="#000000",
            command=self._hablar)
        self.btn_hablar.grid(row=0, column=0, padx=12)

        ctk.CTkButton(fb, text="⏹  Detener", width=300, height=52, corner_radius=12,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color="#141414", hover_color="#222",
                      border_color="#2a2a2a", border_width=2, text_color="#fff",
                      command=self._detener).grid(row=0, column=1, padx=12)

        ctk.CTkButton(fb, text="🗑  Limpiar", width=300, height=52, corner_radius=12,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color="#141414", hover_color="#222",
                      border_color="#2a2a2a", border_width=2, text_color="#fff",
                      command=self._limpiar).grid(row=0, column=2, padx=12)

        # ── Fila descarga MP3 ─────────────────────────────────────────────
        fd = ctk.CTkFrame(self, fg_color="#0e0e0e", corner_radius=12,
                          border_width=1, border_color="#1a1a1a")
        fd.pack(padx=25, pady=(4, 6), fill="x")

        ctk.CTkLabel(fd, text="💾  Exportar MP3",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#ffaa00").pack(side="left", padx=(18, 10))

        self.entry_mp3 = ctk.CTkEntry(
            fd, placeholder_text="nombre-del-archivo  (sin .mp3)",
            width=340, height=34, font=ctk.CTkFont(size=13),
            fg_color="#141414", border_color="#2a2a2a", text_color="#fff",
            corner_radius=8)
        self.entry_mp3.pack(side="left", padx=(0, 10), pady=10)

        self.btn_descargar = ctk.CTkButton(
            fd, text="⬇  Guardar MP3", width=160, height=34,
            corner_radius=8, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2a1f00", hover_color="#3a2f00",
            border_color="#ffaa00", border_width=1,
            text_color="#ffaa00",
            command=self._guardar_mp3)
        self.btn_descargar.pack(side="left", padx=(0, 18), pady=10)

        self.label_estado = ctk.CTkLabel(
            self, text="Listo para reproducir",
            font=ctk.CTkFont(size=12), text_color="#3a3a3a")
        self.label_estado.pack(pady=(4,0))

        ctk.CTkButton(
            self, text="🔍 Detectar voces disponibles en mi PC",
            width=340, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color="#1a1a1a",
            border_color="#222", border_width=1,
            text_color="#555555",
            command=self._detectar_voces
        ).pack(pady=(6, 0))

    # ── Helpers UI ────────────────────────────────────────────────────────────
    def _panel(self):
        f = ctk.CTkFrame(self, fg_color="#0e0e0e", corner_radius=14,
                         border_width=1, border_color="#1a1a1a")
        f.pack(padx=25, fill="x", pady=(0,8))
        return f

    def _ls(self): return dict(font=ctk.CTkFont(size=12, weight="bold"), text_color="#555555")
    def _cs(self): return dict(font=ctk.CTkFont(size=13), fg_color="#141414",
                                border_color="#2a2a2a", text_color="#ffffff",
                                button_color="#00cfff", dropdown_fg_color="#141414")

    def _sc(self, parent, label, attr_s, attr_l, mn, mx, default, fmt, color, col, row=0):
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="#555555"
                     ).grid(row=row, column=col, padx=(18,4), pady=(12,2), sticky="w", columnspan=2)
        lbl = ctk.CTkLabel(parent, text=fmt(default), width=58,
                           font=ctk.CTkFont(size=12, weight="bold"), text_color=color)
        lbl.grid(row=row+1, column=col+1, padx=(0,14), pady=(0,12))
        setattr(self, attr_l, lbl)
        sld = ctk.CTkSlider(parent, from_=mn, to=mx, width=300,
                            button_color=color, progress_color=color,
                            command=lambda v, f=fmt, l=lbl: l.configure(text=f(v)))
        sld.set(default)
        sld.grid(row=row+1, column=col, padx=(18,4), pady=(0,12))
        setattr(self, attr_s, sld)

    # ── Estado actual ─────────────────────────────────────────────────────────
    def _estado_actual(self):
        return dict(
            voz=self.combo_voz.get(),
            vel=int(self.sv_vel.get()), pit=int(self.sv_pit.get()),
            vol=round(self.sv_vol.get(), 3),
            rob=round(self.sv_rob.get(), 3), eco=round(self.sv_eco.get(), 3),
            rev=round(self.sv_rev.get(), 3), dist=round(self.sv_dist.get(), 3),
            cho=round(self.sv_cho.get(), 3), tel=round(self.sv_tel.get(), 3),
        )

    def _cargar_estado(self, p):
        if "voz" in p:
            self.combo_voz.set(p["voz"])
        self.sv_vel.set(p.get("vel",0));   self.lv_vel.configure(text=f"{p.get('vel',0):+d}%")
        self.sv_pit.set(p.get("pit",0));   self.lv_pit.configure(text=f"{p.get('pit',0):+d}Hz")
        self.sv_vol.set(p.get("vol",1));   self.lv_vol.configure(text=f"{int(p.get('vol',1)*100)}%")
        self.sv_rob.set(p.get("rob",0));   self.lv_rob.configure(text=f"{int(p.get('rob',0)*100)}%")
        self.sv_eco.set(p.get("eco",0));   self.lv_eco.configure(text=f"{int(p.get('eco',0)*100)}%")
        self.sv_rev.set(p.get("rev",0));   self.lv_rev.configure(text=f"{int(p.get('rev',0)*100)}%")
        self.sv_dist.set(p.get("dist",0)); self.lv_dist.configure(text=f"{int(p.get('dist',0)*100)}%")
        self.sv_cho.set(p.get("cho",0));   self.lv_cho.configure(text=f"{int(p.get('cho',0)*100)}%")
        self.sv_tel.set(p.get("tel",0));   self.lv_tel.configure(text=f"{int(p.get('tel',0)*100)}%")

    # ── Gestión de configs ────────────────────────────────────────────────────
    def _aplicar_preset(self, nombre):
        p = self.configs.get(nombre)
        if p:
            self._cargar_estado(p)

    def _cargar_seleccion(self):
        nombre = self.combo_preset.get()
        self._aplicar_preset(nombre)
        self.label_estado.configure(text=f"📂 Configuración '{nombre}' cargada", text_color="#00ff99")

    def _guardar_config(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            self.label_estado.configure(text="⚠ Escribe un nombre para la configuración", text_color="#ff9500")
            return
        self.configs[nombre] = self._estado_actual()
        self._actualizar_combo_preset()
        self.combo_preset.set(nombre)
        guardar_configs(self.configs, self._estado_actual(), self.preset_default_keys)
        self.entry_nombre.delete(0, "end")
        self.label_estado.configure(text=f"✅ Configuración '{nombre}' guardada", text_color="#00ff99")

    def _borrar_config(self):
        nombre = self.combo_preset.get()
        if nombre in self.preset_default_keys:
            self.label_estado.configure(text="⚠ No puedes borrar configuraciones predeterminadas", text_color="#ff6b6b")
            return
        if nombre in self.configs:
            del self.configs[nombre]
            self._actualizar_combo_preset()
            self.combo_preset.set("Normal")
            guardar_configs(self.configs, self._estado_actual(), self.preset_default_keys)
            self.label_estado.configure(text=f"🗑 Configuración '{nombre}' eliminada", text_color="#aaaaaa")

    def _actualizar_combo_preset(self):
        self.combo_preset.configure(values=list(self.configs.keys()))

    # ── Reproducción ─────────────────────────────────────────────────────────
    def _hablar(self):
        texto = self.texto_input.get("0.0", "end").strip()
        if not texto or texto == "Escribe aquí el texto que deseas escuchar...":
            self.label_estado.configure(text="⚠ Escribe algo primero", text_color="#ff6b6b")
            return
        self._matar_proceso()
        efectos = dict(
            pitch=int(self.sv_pit.get()), volume=self.sv_vol.get(),
            robot=self.sv_rob.get(), eco=self.sv_eco.get(),
            reverb=self.sv_rev.get(), distorsion=self.sv_dist.get(),
            chorus=self.sv_cho.get(), telefono=self.sv_tel.get(),
        )
        voz_id = obtener_voz_id(self.combo_voz.get())
        self.cola_estado = multiprocessing.Queue()
        self.proceso = multiprocessing.Process(
            target=_worker,
            args=(texto, voz_id, int(self.sv_vel.get()), efectos, self.cola_estado),
            daemon=True)
        self.proceso.start()
        self.btn_hablar.configure(state="disabled")
        self.label_estado.configure(text="🔊 Generando voz...", text_color="#00cfff")

    def _detener(self):
        self._matar_proceso()
        self.btn_hablar.configure(state="normal")
        self.label_estado.configure(text="⏹ Detenido", text_color="#555555")

    def _matar_proceso(self):
        if self.proceso and self.proceso.is_alive():
            self.proceso.terminate()
            self.proceso.join(timeout=2)
        self.proceso = None; self.cola_estado = None

    def _limpiar(self):
        self.texto_input.delete("0.0", "end")
        self.label_estado.configure(text="Listo para reproducir", text_color="#3a3a3a")

    def _al_cerrar(self):
        self._matar_proceso()
        guardar_configs(self.configs, self._estado_actual(), self.preset_default_keys)
        self.destroy()

    def _guardar_mp3(self):
        texto = self.texto_input.get("0.0", "end").strip()
        if not texto or texto == "Escribe aquí el texto que deseas escuchar...":
            self.label_estado.configure(text="⚠ Escribe texto antes de exportar", text_color="#ff6b6b")
            return

        nombre = self.entry_mp3.get().strip()
        if not nombre:
            self.label_estado.configure(text="⚠ Escribe un nombre para el archivo MP3", text_color="#ff9500")
            return

        # Limpiar caracteres no válidos en nombre de archivo
        for c in r'\/:*?"<>|':
            nombre = nombre.replace(c, "_")
        if not nombre.endswith(".mp3"):
            nombre += ".mp3"

        # Pedir carpeta donde guardar
        from tkinter import filedialog
        carpeta = filedialog.askdirectory(title="Selecciona carpeta para guardar el MP3")
        if not carpeta:
            return

        destino = os.path.join(carpeta, nombre)
        self.btn_descargar.configure(state="disabled")
        self.label_estado.configure(text="⏳ Generando MP3...", text_color="#ffaa00")

        import threading
        threading.Thread(target=self._exportar_worker,
                         args=(texto, destino), daemon=True).start()

    def _exportar_worker(self, texto, destino):
        import asyncio, edge_tts
        try:
            voz_id = obtener_voz_id(self.combo_voz.get())
            rate   = int(self.sv_vel.get())
            efectos = dict(
                pitch      = int(self.sv_pit.get()),
                volume     = self.sv_vol.get(),
                robot      = self.sv_rob.get(),
                eco        = self.sv_eco.get(),
                reverb     = self.sv_rev.get(),
                distorsion = self.sv_dist.get(),
                chorus     = self.sv_cho.get(),
                telefono   = self.sv_tel.get(),
            )

            # 1. Generar audio crudo en MP3 temporal
            async def generar():
                com = edge_tts.Communicate(texto, voz_id,
                                           rate=f"{rate:+d}%",
                                           pitch=f"{efectos['pitch']:+d}Hz")
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                path = tmp.name; tmp.close()
                await com.save(path)
                return path

            tmp_path = asyncio.run(generar())

            for _ in range(40):
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 500:
                    break
                time.sleep(0.1)

            # 2. Aplicar efectos
            data, sr = sf.read(tmp_path)
            if data.ndim > 1:
                data = data.mean(axis=1)
            data = aplicar_efectos(data, sr, efectos)
            os.unlink(tmp_path)

            # 3. Guardar como WAV primero, luego convertir a MP3
            tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_wav_path = tmp_wav.name
            tmp_wav.close()
            sf.write(tmp_wav_path, data, sr)

            # 4. Convertir WAV → MP3 usando pydub si está disponible, si no guardar WAV
            destino_final = destino
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(tmp_wav_path)
                audio.export(destino_final, format="mp3", bitrate="192k")
                os.unlink(tmp_wav_path)
            except Exception:
                # Si no tiene pydub, guardar como WAV cambiando extensión
                destino_final = destino.replace(".mp3", ".wav")
                import shutil
                shutil.move(tmp_wav_path, destino_final)

            nombre = os.path.basename(destino_final)
            if os.path.exists(destino_final) and os.path.getsize(destino_final) > 500:
                self.after(0, lambda: self.label_estado.configure(
                    text=f"✅ Guardado con efectos: {nombre}", text_color="#00ff99"))
            else:
                self.after(0, lambda: self.label_estado.configure(
                    text="⚠ Error al guardar", text_color="#ff6b6b"))

        except Exception as e:
            err = str(e)
            print(f"[Error exportación]: {err}")
            msg_ui = "Error de conexión con el servicio TTS" if "403" in err or "WSServerHandshakeError" in err else ((err[:70] + "...") if len(err) > 70 else err)
            self.after(0, lambda m=msg_ui: self.label_estado.configure(
                text=f"⚠ Error: {m}", text_color="#ff6b6b"))
        finally:
            self.after(0, lambda: self.btn_descargar.configure(state="normal"))

    def _detectar_voces(self):
        self.label_estado.configure(text="🔍 Detectando voces... espera un momento", text_color="#ffdd00")
        self.update()
        import threading
        threading.Thread(target=self._detectar_worker, daemon=True).start()

    def _detectar_worker(self):
        import asyncio, edge_tts
        async def listar():
            voces = await edge_tts.list_voices()
            return [v for v in voces if 'es-MX' in v['ShortName']]
        try:
            mx = asyncio.run(listar())
            nuevas = {}
            for v in mx:
                nombre = v['ShortName'].replace("es-MX-","").replace("Neural","")
                genero = "Mujer" if v['Gender'] == "Female" else "Hombre"
                etiqueta = f"{nombre:12} · MX {genero}"
                if "Dalia" in nombre:
                    etiqueta = "⭐ " + etiqueta
                nuevas[etiqueta] = v['ShortName']

            def actualizar():
                global VOCES
                VOCES = nuevas
                self.combo_voz.configure(values=list(VOCES.keys()))
                mujeres = [k for k in VOCES if "Mujer" in k]
                primera = mujeres[0] if mujeres else list(VOCES.keys())[0]
                self.combo_voz.set(primera)
                self.label_estado.configure(
                    text=f"✅ {len(VOCES)} voces MX detectadas — {len(mujeres)} mujeres, {len(VOCES)-len(mujeres)} hombres",
                    text_color="#00ff99")
            self.after(0, actualizar)
        except Exception as e:
            self.after(0, lambda: self.label_estado.configure(
                text=f"⚠ Error detectando: {e}", text_color="#ff6b6b"))

    def _poll_proceso(self):
        if self.cola_estado is not None:
            try:
                msg = self.cola_estado.get_nowait()
                if msg == "done":
                    self.btn_hablar.configure(state="normal")
                    self.label_estado.configure(text="✅ Listo para reproducir de nuevo", text_color="#00ff99")
                    self.proceso = None; self.cola_estado = None
                elif msg.startswith("error:"):
                    self.btn_hablar.configure(state="normal")
                    err = msg[6:]
                    print(f"[Error reproducción]: {err}")
                    msg_ui = "Error de conexión con el servicio TTS" if "403" in err or "WSServerHandshakeError" in err else ((err[:70] + "...") if len(err) > 70 else err)
                    self.label_estado.configure(text=f"⚠ {msg_ui}", text_color="#ff6b6b")
                    self.proceso = None; self.cola_estado = None
            except Exception:
                pass
        self.after(300, self._poll_proceso)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = TextoAVozApp()
    app.mainloop()
