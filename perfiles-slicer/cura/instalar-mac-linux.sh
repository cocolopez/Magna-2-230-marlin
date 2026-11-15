#!/bin/sh
# Instala los perfiles "Hellbot Magna 2 ... Marlin 2.1" (230, 300, 400, 400D, 500, 500D) en la version MAS NUEVA de Cura.
# Cerra Cura antes de correrlo. Uso: sh instalar-mac-linux.sh
set -e
cd "$(dirname "$0")"
for base in "$HOME/Library/Application Support/cura" "$HOME/.local/share/cura" \
            "$HOME/.var/app/com.ultimaker.cura/data/cura"; do
  [ -d "$base" ] || continue
  v=$(ls "$base" | grep -E '^[0-9]+\.[0-9]+$' | sort -t. -k1,1n -k2,2n | tail -n 1)
  [ -n "$v" ] || continue
  d="$base/$v"
  echo "Instalando en $d"
  mkdir -p "$d/definitions" "$d/extruders" "$d/quality"
  cp definitions/*.def.json "$d/definitions/"
  cp extruders/*.def.json "$d/extruders/"
  cp -R quality/* "$d/quality/"
  echo "Listo. Abri Cura > Agregar impresora > No conectada en red > Hellbot > Hellbot Magna 2 (tu modelo) Marlin 2.1"
  exit 0
done
echo "No encontre la carpeta de configuracion de Cura. Abri Cura una vez y volve a correr esto."
exit 1
