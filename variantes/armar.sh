#!/usr/bin/env bash
# Arma el firmware de un modelo, listo para la SD. Lo usan los dos workflows (compilar y publicar).
#
# Uso (desde la carpeta de compilación = Marlin + los archivos de este repo copiados encima):
#   bash variantes/armar.sh MODELO SALIDA [PLACA]
#   MODELO = 230, 230-BLTouch, 300, 400, 400D, 500 o 500D
#   SALIDA = carpeta donde queda Robin_nano35.bin + assets + instrucciones
#   PLACA  = 13 (MKS Robin Nano V1.3, por defecto: mm2) o 12 (V1.2, versión recortada: mm12)
#
# 300, 400, 400D, 500 y 500D: valores de los firmware oficiales de Hellbot, SIN PROBAR en una
# máquina real (solo existe la 230). La carpeta lleva LEEME-SIN-PROBAR.txt y MODELOS.md.
set -euo pipefail
M="$1"
OUT="$2"
PLACA="${3:-13}"
if [ "$PLACA" = 12 ]; then ENV=mks_robin_nano_v1v2; else ENV=mks_robin_nano_v1_3_f4; fi
PB=.pio/build/$ENV

case "$M" in
  230) ;;
  230-BLTouch) python3 variantes/bltouch.py . ;;
  300|400|400D|500|500D) python3 variantes/modelo.py "$M" . ;;
  *) echo "::error::Modelo desconocido: $M"; exit 1 ;;
esac
# Placa V1.2 (mm12): STM32F103, extras recortados (assets-tema/liviano.py). SIN PROBAR.
[ "$PLACA" = 12 ] && python3 variantes/placa12.py .

# Tema, extras de la pantalla, castellano (aplicar_idioma.py) y arreglo de _assets
python3 assets-tema/aplicar_colores.py .

python3 pruebas/preflight.py
bash pruebas/sanity-check.sh
if [ "$M" = 230 ] && [ "$PLACA" = 13 ]; then
  bash pruebas/verificar-valores.sh     # los valores de la 230 contra el firmware original
  python3 pruebas/verificar-perfiles.py
fi

pio run -e $ENV
bash pruebas/verificar-buffer-pantalla.sh $PB/firmware.elf

rm -rf "$OUT"
mkdir -p "$OUT/assets"
cp $PB/Robin_nano35.bin "$OUT/"
[ -d $PB/assets ] && cp -r $PB/assets/. "$OUT/assets/"
# Íconos y logo del tema propio encima de los de Makerbase (se conservan la letra y bmp_preview)
[ -d assets-tema/assets ] && cp assets-tema/assets/*.bin "$OUT/assets/"
# La letra de la pantalla no trae í ú ü Á É Í Ó Ú Ñ ¡ °: se agregan (pantalla en castellano)
[ -f "$OUT/assets/FontUNIGBK.bin" ] && python3 assets-tema/fuente_acentos.py "$OUT/assets/FontUNIGBK.bin"
cp docs-magna/COMO-FLASHEAR.md "$OUT/"
if [ -f wifi/MksWifi.bin ]; then
  mkdir -p "$OUT/opcional-wifi"
  cp wifi/MksWifi.bin wifi/README.md "$OUT/opcional-wifi/"
fi
case "$M" in 230-BLTouch|400|400D|500|500D) cp docs-magna/BLTOUCH.md "$OUT/" ;; esac
if [ "$PLACA" = 12 ]; then
  # mm12: todo sin probar (nadie tiene una placa V1.2)
  cp docs-magna/MODELOS.md docs-magna/PLACA-V12.md "$OUT/"
  sed "s/{MODELO}/$M (placa V1.2)/g" docs-magna/LEEME-SIN-PROBAR.txt > "$OUT/LEEME-SIN-PROBAR.txt"
else
  case "$M" in
    300|400|400D|500|500D)
      cp docs-magna/MODELOS.md "$OUT/"
      sed "s/{MODELO}/$M/g" docs-magna/LEEME-SIN-PROBAR.txt > "$OUT/LEEME-SIN-PROBAR.txt"
      ;;
  esac
fi
echo "Magna 2 $M (placa V1.${PLACA#1}): Robin_nano35.bin = $(stat -c%s "$OUT/Robin_nano35.bin") bytes"
