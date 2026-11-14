#!/usr/bin/env bash
# Verifica que el buffer de imagen de la pantalla MKS (bmp_public_buf) quede en una dirección
# múltiplo de 4. El DMA que copia la imagen a la pantalla mueve de a 2 bytes: con una dirección
# impar todos los colores se ven corridos (rojo -> azul, franjas). El lugar del buffer depende de
# las otras variables del firmware, así que puede cambiar con cualquier agregado.
# Uso: bash pruebas/verificar-buffer-pantalla.sh <firmware.elf> [arm-none-eabi-nm]
set -euo pipefail
ELF=$1
NM=${2:-$(ls ~/.platformio/packages/toolchain-gccarmnoneeabi*/bin/arm-none-eabi-nm 2>/dev/null | head -1)}
DIR=$("$NM" "$ELF" | awk '$3=="bmp_public_buf"{print $1}')
[ -n "$DIR" ] || { echo "No se encontró bmp_public_buf en $ELF"; exit 1; }
if (( 0x$DIR % 4 )); then
  echo "MAL: bmp_public_buf en 0x$DIR (no es múltiplo de 4): la pantalla mostraría los colores corridos"; exit 1
fi
echo "OK: bmp_public_buf en 0x$DIR (alineado)"
