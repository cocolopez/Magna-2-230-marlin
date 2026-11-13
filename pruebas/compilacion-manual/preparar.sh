#!/usr/bin/env bash
# Descarga lo necesario para compilar SIN PlatformIO (todo desde GitHub):
#   - GCC ARM (xPack 13.3.1), núcleo STM32 1.9.0 (el de ststm32@12.1), CMSIS 5.7 (headers),
#   - LVGL 6.1.2 de MKS y QRCode de MKS (las dos librerías de la UI MKS / WiFi).
# Uso: TC=$HOME/marlin-tc bash preparar.sh
set -euo pipefail
TC=${TC:-$HOME/marlin-tc}; mkdir -p "$TC"; cd "$TC"
[ -d xpack-arm-none-eabi-gcc-13.3.1-1.1 ] || curl -sSL https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack/releases/download/v13.3.1-1.1/xpack-arm-none-eabi-gcc-13.3.1-1.1-linux-x64.tar.gz | tar xz
[ -d core ] || git clone -q --depth 1 -b 1.9.0 https://github.com/stm32duino/Arduino_Core_STM32 core
[ -d cmsis ] || { git clone -q --depth 1 --filter=blob:none --sparse -b 5.7.0 https://github.com/ARM-software/CMSIS_5 cmsis && (cd cmsis && git sparse-checkout set CMSIS/Core/Include); }
[ -d lvgl ] || git clone -q --depth 1 -b v6.1.2 https://github.com/staff1010/LVGL-6.1.1-MKS lvgl
[ -d qrcode ] || { git clone -q https://github.com/makerbase-mks/QRCode qrcode && (cd qrcode && git checkout -q 261c5a696a); }
echo "Listo en $TC"
