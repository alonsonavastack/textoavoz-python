"""Prueba de humo del conector MCP: arranca el servidor (script o .exe), pide sus herramientas y llama a listar_voces.

Uso:
    python smoke_mcp.py dist/TextoAVoz/TextoAVozMCP.exe
    python smoke_mcp.py venv/bin/python mcp_server.py
"""
import json
import queue
import subprocess
import sys
import threading

ESPERADAS = {"listar_voces", "generar_voz", "generar_guion"}


def main(cmd):
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    salida = queue.Queue()
    threading.Thread(target=lambda: [salida.put(l) for l in p.stdout], daemon=True).start()
    errores = []
    threading.Thread(target=lambda: [errores.append(l) for l in p.stderr], daemon=True).start()

    def enviar(obj):
        p.stdin.write(json.dumps(obj) + "\n")
        p.stdin.flush()

    def respuesta(id_, timeout=90):
        while True:
            linea = salida.get(timeout=timeout)
            try:
                msg = json.loads(linea)
            except ValueError:
                continue
            if msg.get("id") == id_:
                return msg

    try:
        enviar({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "smoke", "version": "1"}}})
        respuesta(1)
        enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
        enviar({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = {t["name"] for t in respuesta(2)["result"]["tools"]}
        faltan = ESPERADAS - tools
        if faltan:
            print("FALLO: faltan herramientas:", sorted(faltan)); return 1
        enviar({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "listar_voces", "arguments": {}}})
        texto = json.dumps(respuesta(3)["result"], ensure_ascii=False)
        if "Dalia" not in texto:
            print("FALLO: listar_voces no devolvio las voces:", texto[:300]); return 1
        print("OK: herramientas", sorted(tools), "| listar_voces responde")
        return 0
    except Exception as e:
        print("FALLO:", repr(e)); print("".join(errores)[-1500:]); return 1
    finally:
        p.kill()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1:]))
