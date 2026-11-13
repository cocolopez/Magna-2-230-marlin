# Perfiles de slicer — Magna 2 230 (Marlin 2.1)

Pensados para **este firmware**: mismos límites de velocidad y aceleración, cama de 230×230×250, doble extrusor con boquilla única (2 en 1) y cambio de filamento hecho por el firmware.

Qué incluye cada slicer:
- **Máquina:** con gcode de inicio que hace la doble línea de purga y gcode de fin que presenta la pieza.
- **Calidades:** 0.12 Fina, 0.20 Normal y 0.28 Borrador.
- **Filamentos:** PLA, PETG y ABS.

> Si cambiás algo, editá `generar_perfiles.py` (los valores están arriba de todo) y corré `python3 generar_perfiles.py`: regenera los tres slicers de forma coherente. Después corré `python3 ../pruebas/verificar-perfiles.py`.

## Cura (5.x)
1. Cerrá Cura.
2. Abrí la carpeta de configuración de Cura: en Cura, menú **Ayuda → Mostrar carpeta de configuración**. En Windows es `%APPDATA%\cura\<versión>\`.
3. Copiá `cura/definitions/*.def.json` dentro de `definitions` y `cura/extruders/*.def.json` dentro de `extruders` (si las carpetas no existen, creálas).
4. Abrí Cura → **Agregar impresora → No conectada en red → Hellbot → Hellbot Magna 2 230 (Marlin 2.1)**.
5. Los materiales son los genéricos de Cura. Ajustá la temperatura del PLA a 205 °C y la cama a 60 °C.
6. Para que la pantalla muestre el tiempo restante: **Extensiones → Post-procesado → Modificar G-Code → Agregar script → Display Progress On LCD**.

## PrusaSlicer (2.6 o superior)
**Archivo → Importar → Importar paquete de configuración** y elegí `prusaslicer/Magna2-230_PrusaSlicer_bundle.ini`. Ya emite el tiempo restante (M73) y las etiquetas para cancelar objetos (M486).

## OrcaSlicer (2.x)
**Archivo → Importar → Importar configuraciones** y elegí todos los `.json` de `orcaslicer/machine`, `orcaslicer/process` y `orcaslicer/filament`. Empezá por el de la máquina.

## Notas
- **Retracción:** 5 mm a 40 mm/s, que es un valor seguro para un bowden. Cuando calibres Linear Advance, probablemente puedas bajarla a 3–4 mm.
- **Linear Advance:** en cada filamento, el gcode de inicio de filamento trae `;M900 K0.0` comentado. Si querés un K distinto por material, descomentalo y poné tu valor.
- **Torre de purga:** viene activada. Solo se imprime cuando la pieza usa los dos extrusores.
- **Cambio de extrusor:** los perfiles ponen en 0 la retracción de cambio del slicer, porque el firmware ya retira y carga el filamento (`M217`). Así no se retrae dos veces.
- **Comprobación:** se verificó que los archivos estén bien formados y coincidan con el firmware (`pruebas/verificar-perfiles.py`). No pude abrirlos en los programas desde acá, así que si alguno da un aviso al importarlo, avisame qué dice.
