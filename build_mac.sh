#!/bin/bash
# Compila TextoAVoz.app y crea el instalador .dmg (solo en macOS).
# Uso: ./build_mac.sh   (usa ./venv si existe)
set -euo pipefail
cd "$(dirname "$0")"
[ -d venv ] && source venv/bin/activate

# Icono .icns a partir de assets/icon.png
if [ ! -f assets/icon.icns ] && [ -f assets/icon.png ]; then
  S=$(mktemp -d)/icon.iconset; mkdir -p "$S"
  for n in 16 32 128 256 512; do
    sips -z $n $n assets/icon.png --out "$S/icon_${n}x${n}.png" >/dev/null
    sips -z $((n*2)) $((n*2)) assets/icon.png --out "$S/icon_${n}x${n}@2x.png" >/dev/null
  done
  iconutil -c icns "$S" -o assets/icon.icns
fi

pyinstaller --clean -y TextoAVoz.spec

APP="dist/TextoAVoz.app"
# Firma ad-hoc (necesaria en Apple Silicon; no sustituye a un Developer ID)
codesign --force --deep --sign - "$APP"

python smoke_mcp.py "$APP/Contents/MacOS/TextoAVozMCP"

ARCH=$(uname -m)
DMG="dist/TextoAVoz-macOS-$ARCH.dmg"
rm -f "$DMG"; rm -rf dist/dmg; mkdir dist/dmg
cp -R "$APP" dist/dmg/
ln -s /Applications dist/dmg/Applications
hdiutil create -volname "Texto a Voz Studio" -srcfolder dist/dmg -ov -format UDZO "$DMG"
rm -rf dist/dmg
echo "Listo: $DMG"
