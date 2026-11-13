#!/usr/bin/env bash
# Arma el proyecto completo en tu PC (igual que GitHub Actions) para compilar localmente.
# Requiere git (y PlatformIO para compilar).
# Uso: bash pruebas/armar-local.sh [carpeta_destino]   (por defecto ./build)
set -euo pipefail
cd "$(dirname "$0")/.."
VER=$(tr -d ' \r\n' < MARLIN_VERSION)
DEST=${1:-build}
rm -rf "$DEST"
git clone -q --depth 1 -b "$VER" https://github.com/MarlinFirmware/Marlin "$DEST"
rm -rf "$DEST/.git" "$DEST/.github"
tar cf - --exclude=./.git --exclude=./.github --exclude="./$DEST" . | tar xf - -C "$DEST"
echo "Listo: $DEST  (compilar con: cd $DEST && pio run -e mks_robin_nano_v1_3_f4)"
