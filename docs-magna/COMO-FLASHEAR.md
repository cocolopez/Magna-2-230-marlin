# Cómo flashear la Magna 2 230 (Robin Nano V1.3)

1. Guardá tus valores actuales: conectá por USB (Pronterface, 115200) y mandá `M503`. Copiá la salida a un archivo de texto.
2. Formateá una microSD en FAT32.
3. Copiá a la raíz de la SD:
   - `Robin_nano35.bin`
   - la carpeta `assets` completa
4. Con la impresora apagada, poné la SD y encendé. Vas a ver la barra de actualización (firmware y después las imágenes). Esperá ~1 minuto hasta que aparezca la pantalla principal.
5. Apagá, sacá la SD. En la SD, el archivo debería haberse renombrado a `ROBIN_NANO35.CUR` (eso confirma que se grabó).
6. Encendé y reiniciá la EEPROM a los valores nuevos: `M502` y después `M500` (o desde la pantalla: Configuración → EEPROM → Restablecer).

El WiFi (`MksWifi.bin`) no hace falta volver a cargarlo si ya funcionaba.

**Volver atrás:** si algo no te convence, repetí el proceso con el `Robin_nano35.bin` de charlieburgos que ya tenías.
