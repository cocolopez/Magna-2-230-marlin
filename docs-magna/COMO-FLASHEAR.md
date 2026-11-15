# Cómo flashear la Magna 2 230 (Robin Nano V1.3)

1. Guardá tus valores actuales: conectá por USB (Pronterface, 115200) y mandá `M503`. Copiá la salida a un archivo de texto.
2. Formateá una microSD en FAT32.
3. Copiá a la raíz de la SD:
   - `Robin_nano35.bin`
   - la carpeta `assets` completa
4. Con la impresora apagada, poné la SD y encendé. Vas a ver la barra de actualización (firmware y después las imágenes). Esperá ~1 minuto hasta que aparezca la pantalla principal.
5. Apagá y sacá la SD. La carpeta `assets` se habrá renombrado a `_assets`, lo que confirma que se cargaron los íconos del tema. Si quedaba una `_assets` de una instalación anterior, la pantalla la borra antes (desde la etapa 39); podés borrar `_assets` cuando quieras. Además, el archivo debería haberse renombrado a `ROBIN_NANO35.CUR` (eso confirma que se grabó).
6. Encendé y reiniciá la EEPROM a los valores nuevos: `M502` y después `M500` (o desde la pantalla: Configuración → EEPROM → Restablecer).

El WiFi no hace falta volver a cargarlo si ya funciona. Si querés actualizarlo, copiá también `opcional-wifi/MksWifi.bin` a la raíz de la SD: se graba después de los íconos, se renombra a `MKSWIFI.CUR`, y **no hay que apagar mientras aparece el diálogo del WiFi**.

**Volver atrás:** si algo no te convence, repetí el proceso con el `Robin_nano35.bin` de charlieburgos que ya tenías.

**Idioma:** la pantalla viene en castellano, pero si antes la tenías en inglés queda así (el idioma se guarda en la pantalla). Para cambiarlo: Ajustes → Idioma → Español.

**Magna 2 300, 400 y 500:** sus firmware no están probados en una máquina real. Leé `LEEME-SIN-PROBAR.txt` antes de instalar.
