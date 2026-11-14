# CLAUDE.md — Marlin para Hellbot Magna 2 230

## Proyecto
Firmware Marlin 2.1.3-beta3 configurado para Hellbot Magna 2 230: MKS Robin Nano V1.3 (STM32F407VE), pantalla MKS TFT35 v1 con interfaz MKS LVGL, doble extrusor con hotend 2 en 1. Incluye perfiles de Cura, PrusaSlicer y OrcaSlicer.

## Historial de etapas
### Etapa 1 (2026-11-13) — configuración base
- `Marlin/Configuration.h` y `Marlin/Configuration_adv.h`: cada línea tocada lleva `// Magna2-230`.
- Los valores salen del binario de charlieburgos V2.1.2.1, desensamblado con llvm-objdump (base 0x08008000). El detalle está en `docs-magna/CONFIGURACION.md`.
- CI: los workflows originales de Marlin se borraron.

### Etapa 2 (2026-11-13) — mejoras + perfiles
- Firmware:
  - `TOOLCHANGE_FILAMENT_SWAP` compilado con largo 0 (desde la etapa 16 el cambio 2 en 1 lo hacen los perfiles; M217 S100 para cambios a mano)
  - `INPUT_SHAPING_X/Y` (40 Hz)
  - `MPCTEMP` en lugar de `PIDTEMP` (40 W)
  - `HOTEND_IDLE_TIMEOUT` (10 min)
  - `CANCEL_OBJECTS`
  - `SET_PROGRESS_MANUALLY`
  - `FILAMENT_RUNOUT_DISTANCE_MM 15`
- Calibración: `docs-magna/CALIBRACION.md`.
- Perfiles en `perfiles-slicer/`, generados por `perfiles-slicer/generar_perfiles.py`. Es la única fuente: editar ahí y regenerar.
- Regla de los perfiles: la retracción de cambio de herramienta del slicer va en 0 (el cambio lo hace el firmware). En PrusaSlicer, `toolchange_gcode` debe empezar con `T[next_extruder]`, porque si no queda vacío Prusa no emite el comando T.

### Etapa 3 (2026-11-13) — compilar desde mm2.zip
- Workflow `compilar-mm2.yml` (copia en `github-workflows/`; en el repo va en `.github/workflows/`). Al subir `mm2.zip` a la raíz: lo descomprime (si trae una carpeta raíz, usa su contenido), copia con rsync `--delete` (sin tocar `.git`/`.github`), commitea con `[skip ci]` y borra el zip. Ver etapa 4 para la compilación.
- `mm2.zip` se arma con el contenido del proyecto en la raíz y SIN `.github` (el GITHUB_TOKEN no puede escribir workflows).

### Etapa 4 (2026-11-13) — mm2.zip liviano
- El zip completo (43 MB) superaba el límite de 25 MB de la subida web de GitHub.
- Se verificó que el zip del usuario es idéntico al tag oficial `2.1.3-b3` (diff -r = 0). Ahora el repo guarda solo los archivos propios: `Marlin/Configuration*.h`, `platformio.ini`, docs, perfiles, pruebas y `MARLIN_VERSION`.
- El workflow clona Marlin (`git clone --depth 1 -b $(cat MARLIN_VERSION)`) en `build/`, copia encima el repo con tar, corre las pruebas y compila ahí. Artefacto: `build/dist/Magna2-230`.
- `pruebas/armar-local.sh` reproduce lo mismo en una PC.
- Simulado localmente: extracción, aplicación sobre Marlin oficial y las 3 pruebas dan OK.

### Etapa 5 (2026-11-13) — fix del primer build en GitHub
- El build falló en `preflight-checks.py` de Marlin: con `NUM_RUNOUT_SENSORS 2`, `FILAMENT_RUNOUT_SCRIPT` debe llevar `%c`. Se cambió a `"M600 T%c"`.
- Ese chequeo no estaba en `sanity-check.sh` (vive en un script de PlatformIO, no en SanityCheck.h). Se agregó `pruebas/preflight.py`, que replica los chequeos de preflight sin PlatformIO (probado: detecta el error viejo). El workflow lo corre antes de compilar.

### Etapa 6 (2026-11-13) — fix de compilación de la UI MKS + compilación local real
- Error de GitHub: `draw_dialog.cpp` / `draw_pause_message.cpp` usaban `pause_menu_response` y `PAUSE_RESPONSE_*`, que no existen. En 2.1.3-b3, `M600_PURGE_MORE_RESUMABLE` solo se define con MarlinUI, ExtUI o `EMERGENCY_PARSER`+`HOST_PROMPT_SUPPORT` (no contempla la UI MKS). Además, `draw_dialog.cpp` solo incluye `pause.h` si `PARK_HEAD_ON_PAUSE` está activo.
- Solución solo con configuración: `HOST_ACTION_COMMANDS` + `HOST_PROMPT_SUPPORT` + `PARK_HEAD_ON_PAUSE` en `Configuration_adv.h`. No se tocó el código de Marlin.
- Se armó la compilación sin PlatformIO (`pruebas/compilacion-manual/`): xPack GCC 13.3, núcleo STM32 1.9.0, CMSIS 5.7, LVGL 6.1.2 MKS y QRCode MKS, todo bajado de GitHub. Reproduce el error de GitHub y, con la solución, compila y enlaza el firmware completo: 351.328 bytes (71 % de 480 KB), RAM 80 KB de 128 KB, vector table en 0x08008000.

### Etapa 7 (2026-11-13) — primera compilación OK en GitHub; revisión de warnings
- La build de GitHub salió bien: 345.616 bytes, RAM 59 % (PlatformIO calcula el % de flash sobre 1 MB, pero el F407VE tiene 512 KB menos 32 KB de bootloader, o sea que el uso real es ~72 %).
- Warning `PRINTCOUNTER auto-save`: en STM32F4 con EEPROM emulada en flash, guardar las estadísticas cada 60 min pausa el movimiento (`PRINTCOUNTER_SYNC`). Se puso `PRINTCOUNTER_SAVE_INTERVAL 0`, así se guardan al terminar la impresión.
- Warning `-Wformat` en `mks_ui/draw_printing.cpp:249` (`%02d` con `uint32_t`): es de Marlin; en ARM los dos tipos son de 32 bits, sin efecto.
- Avisos de Node 20 en las actions y DeprecationWarning de node: son de GitHub/PlatformIO, sin efecto.

### Etapa 8 (2026-11-13) — tema visual propio "Negro y Rojo"
- `assets-tema/`: `generar_assets.py` dibuja con Pillow (sobremuestreo x4) los 138 assets de la UI MKS con el mismo nombre, tamaño y encabezado LVGL que los originales (verificado archivo por archivo), más el logo de arranque de 480×320 RGB565 sin encabezado (fondo propio: pieza en capas en perspectiva). Estilo: fondo #1A1A1A, trazo blanco #EEEEEE, acento rojo #D62027, franja `_sel` en las filas 100-139.
- `aplicar_colores.py`: reemplazos exactos de 9 colores fijos en `mks_ui` (draw_ui.h/.cpp, draw_keyboard.cpp). Es idempotente y avisa si no encuentra alguno. Probado: compila (351.304 bytes).
- Workflow: después de aplicar la configuración corre `aplicar_colores.py`; en "Preparar archivos para la SD" copia `assets-tema/assets/*.bin` encima de los assets de Makerbase (se conservan `FontUNIGBK.bin` y `bmp_preview.bin`). Simulado OK.
- La pantalla carga la carpeta `assets` de la SD al arrancar y la renombra a `_assets`.

### Etapa 9 (2026-11-13) — ajustes de la pantalla de arranque
- El usuario pidió el logo de Marlin como pieza impresa. No se dibujó, por ser una marca registrada. Primero se puso una "M" y después, a pedido del usuario, un pez espada genérico de diseño propio (dorsal en hoz, cola en media luna; `pez_espada_mask()`). El usuario mandó una ilustración de banco de imágenes (Dreamstime) como referencia: NO se copió. Solo se tomó la idea genérica de "saltando": la silueta propia se curva por código (radio 135, giro 58°) y se encaja en la columna derecha (x 285-472, y 12-248), con soporte y base sobre la cama. Va 55 % impreso, con el resto en contorno gris.
- Texto: "MAGNA" con un "2" grande rojo detrás de la N y la A; "MARLIN 2.1.3-BETA3", que sale de `MARLIN_VERSION`; "DUAL EXTRUSION". Se quitaron "230" y las medidas de la cama.

### Etapa 10 (2026-11-13) — pieza final de la pantalla de arranque: tornillo
- Se probaron varias piezas (pez espada recto y saltando, torre, cohete, faro, jarrón, engranaje, diamante, pino, montaña, tuerca, rodamiento). El usuario eligió el **tornillo** (`tornillo_mask()`, forma por defecto en `FORMA`).
- La boquilla se ubica sobre el tramo con material de la capa actual más cercano al centro, así no queda sobre un hueco.
- Todas las formas son diseño propio por código. No se usa ningún logo ni imagen de terceros.

### Etapa 11 (2026-11-13) — primera prueba en la impresora y ajustes
- El usuario flasheó y el tema funciona. Pidió: fondo en la pantalla principal, arreglar la flecha de Atrás (se veía cortada), un ícono de Ajustes entendible, y revisar unas líneas que se ven abajo de la pantalla.
- Fondo: los íconos pasaron a cf=5 con chroma key (verde 0x07E0 = `LV_COLOR_TRANSP`). Una imagen de fondo no entra en el slot de 9 KB (`PER_PIC_MAX_SPACE_TFT35`, con `HAS_SPI_FLASH_COMPRESSION`), así que se dibuja por código: degradé en `tft_style_scr` y decoración en `draw_ready_print.cpp` (insertada por `aplicar_colores.py`, 12 cambios, idempotente). Compila: 351.664 bytes.
- `g_llave` = llave fija y destornillador cruzados; `g_volver` = flecha en U hecha con un solo trazo y punta grande, entera dentro del cuadro.
- Líneas de abajo: NO salen de los assets (filas 83-139 vacías; tamaño comprimido OK). Queda pendiente ver si ya estaban con el firmware anterior (podría ser luz que se filtra por el borde del panel).
- WiFi: `wifi/MksWifi.bin` = oficial de Makerbase CS1.0.4_200227 (ESP8266), lo subió el usuario. El workflow lo copia a `opcional-wifi/` del artefacto.

### Etapa 12 (2026-11-13) — README para GitHub
- `README.md` reescrito para la portada del repo: qué trae, hardware, firmware y configuración, funciones, tema con capturas, slicers, WiFi, compilación, instalación, calibración, pruebas, estructura y créditos. A pedido del usuario no menciona a Claude.
- Capturas en `docs-magna/capturas/` (arranque, principal, ajustes, configuración, imprimiendo, íconos), generadas por `assets-tema/generar_capturas.py` a partir de los `.bin` reales, con el degradé y la decoración del firmware (x2 y con marco).
- El README anterior (específico de la Magna) se reemplazó por este.

### Etapa 13 (2026-11-13) — workflow para publicar versiones
- `github-workflows/publicar-release.yml`: se dispara a mano (con nombre de versión opcional o la fecha, y opción de borrador) o con un tag `v*`. Usa lo que ya está en el repo (requiere haber extraído antes mm2.zip): baja Marlin, aplica la configuración y el tema, corre las 4 pruebas, compila y publica con `softprops/action-gh-release@v2` tres archivos: el zip del firmware (bin + assets + opcional-wifi + instrucciones), el zip de perfiles y el `Robin_nano35.bin` suelto, con notas de la versión en español. Permisos: `contents: write`.
- Simulado localmente el armado de los paquetes y las notas: OK.

### Etapa 14 (2026-11-13) — ERROR en los íconos transparentes y su corrección
- Lo que pasó: en la etapa 11 los íconos se guardaron con cf=5 creyendo que era CHROMA_KEYED. En LVGL 6 el enum es 4=TRUE_COLOR, **5=TRUE_COLOR_ALPHA (3 bytes/px)**, **6=TRUE_COLOR_CHROMA_KEYED**. En la pantalla del usuario se vieron íconos verdes, repetidos y comprimidos.
- Solución: cf=6 en `lvgl_bin()`. 132 íconos con cf 6 y 5 opacos con cf 4.
- Comprobación con la LVGL 6.1.2 de MKS compilada en el host (mismo lv_conf.h; stubs de las funciones de vista previa de gcode que MKS agregó a `lv_draw_map`): reproduce exacto el error con cf=5 y con cf=6 renderiza bien. La emulación de lectura secuencial (seek ignorado) rompe hasta los originales, así que no refleja el equipo; se usa lectura con seek real.
- Pruebas nuevas: `pruebas/verificar-assets.py` (formato) y `pruebas/render-lvgl/` (render real; falla si hay verde o íconos sin trazo/fondo). Ambos workflows corren el render después de compilar, con la LVGL de `.pio/libdeps`, y el artefacto incluye `vista-previa-pantalla.png`.
- Arreglo inmediato para el usuario: `assets_corregidos.zip` (138 del tema + FontUNIGBK.bin y bmp_preview.bin de Makerbase). Se carga solo la carpeta `assets`, sin reflashear.

### Etapa 15 (2026-11-13) — revisión del log de GitHub
- Build OK en GitHub: 345.444 bytes de flash (~72 % real del F407VE), RAM 59,6 %.
- Se corrigió el aviso `-Wparentheses` del código propio en `draw_ready_print.cpp` (LV_COLOR_MAKE con expresiones): los colores de las líneas de capas ahora se calculan en variables. Verificado con -Wall: 0 avisos en ese archivo.
- Queda solo el aviso de Marlin en `draw_printing.cpp:249` (sin efecto).

### Etapa 16 (2026-11-13) — perfiles de Cura nuevos, cambio 2 en 1 en el slicer, menús "marcados" y degradé más fuerte
- **Cura no mostraba los perfiles.** Hay dos causas:
  1. Cada versión de Cura tiene su carpeta (`cura/5.x`), así que lo copiado en la versión vieja no se ve en la nueva.
  2. `retraction_speed` 40 > `machine_max_feedrate_e` 25 era un error rojo de Cura.
- **Perfiles de Cura nuevos:**
  - Definición `hellbot_magna2_230_marlin` (mismo id), con `has_machine_quality` y la cama `Hellbot_Magna_2_230.obj` que ya trae Cura.
  - 16 calidades `quality/hellbot_magna2_230_marlin/`: 4 globales (0.12/0.16/0.20/0.28) y 4 por cada material (generic_pla, generic_petg, generic_abs). Usan `setting_version` 25, que sirve en Cura 5.10/5.11; 5.12+ las actualiza con VersionUpgrade511to512 y 512to513.
  - Instaladores `instalar-windows.bat` (CRLF) e `instalar-mac-linux.sh`, que copian en la versión más nueva.
- **Investigación (fuentes):**
  - Hellbot: velocidad recomendada 50 mm/s, máximo 80 mm/s, bowden dual drive.
  - Perfil oficial de Cura `hellbot_magna_2_230_dual`: al dejar el extrusor hace `E-5` + `E-100`; al tomarlo, `E+100`.
  - Blog de Hellbot: retracción de cambio de 6 mm por defecto.
  - Rango típico de retracción bowden: 3–6 mm.
- **Error encontrado en el firmware:**
  - Marlin (`tool_change.cpp`) solo retira el extrusor viejo si `extruder_was_primed[old]`. T0 no queda cebado al prender la máquina, así que el primer T0 → T1 no retiraba T0 y se trababa.
  - Además, 40 mm era corto frente a los 100 mm de Hellbot.
  - Cambio: el slicer hace el cambio, `TOOLCHANGE_FS_LENGTH 0` y `M217 S0` en todos los gcode de inicio, por si la EEPROM tiene 40.
- **Protocolo:**
  - Reposo: los dos filamentos estacionados a 100 mm.
  - Cura:
    - `machine_extruders_shared_nozzle_initial_retraction` = 6 y `switch_extruder_retraction_amount` = 6;
    - el gcode de inicio del extrusor (CuraEngine lo emite también para el primero) va a X225 Y5 y hace E+94, Z-1;
    - el gcode de fin del extrusor (también para el último, en `finalize`) hace Z+1, va a la esquina y hace E-94. Los Z se compensan.
  - Prusa/Orca: SEMM con parking_pos_retraction 100, carga inicial E100 + línea de purga y estacionado E-100 al final.
  - `gcode-utiles/estacionar_T0/T1` y `cargar_T0/T1`.
- **`pruebas/verificar-perfiles.py` reescrito:**
  - usa la foto `pruebas/datos/cura-5.10-ajustes.json` (710 ajustes, con tipo, opciones y mín./máx.);
  - revisa que cada clave exista, los límites (detectó la retracción de 40), las calidades completas y la suma de carga y retiro = 100;
  - revisa que M217 S0 esté en los tres slicers y que Z se compense.
- **Menús, variante B "marcada" más detalles:**
  - Código en `assets-tema/decoracion_menus.inc` (en la etapa 17 pasó a dibujarse dentro del fondo de la pantalla). Dibuja la franja del título, el acento, la línea roja con marcas de regla, el separador punteado, tres capas y la columna de navegación en archivos.
  - Etiqueta "MAGNA 2" a la derecha del título; se borra si se pisa con el título.
  - `aplicar_colores.py` lo pega en `draw_ui.cpp` con una lista blanca de 15 pantallas de íconos.
  - El render en host compila el mismo .inc (`render menu`) y verifica línea, franja, punteado, capas, degradé e íconos.
  - Build: 352.564 bytes (71 %); -Wall sin avisos nuevos.
- **Degradé:** el usuario lo veía casi negro en la pantalla real.
  - Abajo pasó de #2E0A0D a #5C0E14.
  - Capas más claras: principal 0x80+i·0x14; menús 0x86/0xAE/0xD6.
  - Capturas regeneradas (`generar_capturas.py` dibuja la misma decoración).

### Etapa 17 (2026-11-13) — corrección: pantalla Mover
- **Qué reportó el usuario** (con fotos), en la pantalla Mover:
  - los íconos solo aparecían al tocar;
  - la decoración quedaba cortada a ~380 px;
  - "MAGNA 2" se encimaba con "Z:0.0mm".
- **Causa:**
  - `draw_move_motor.cpp` (y `draw_z_offset_wizard.cpp`) hace `lv_obj_get_child_back(scr)` suponiendo que el primer hijo es el título y le pone ancho 379.
  - La decoración de la etapa 16 era un objeto hijo creado antes del título, así que la achicaba a ella. Además, la etiqueta de posición se dibuja a TFT_WIDTH-100.
- **Solución:**
  - `decoracion_menus.inc` ya no crea objetos: envuelve el `design_cb` del objeto pantalla (primero el fondo original, después los trazos). El título vuelve a ser el primer hijo.
  - "MAGNA 2" no se pone en MOVE_MOTOR_UI ni en BABYSTEP_UI, porque escriben su estado arriba a la derecha.
- **Prueba:** el render en host verifica que `lv_obj_get_child_back(scr)` sea el título y aplica el mismo achicado que Mover.
- **Resultado:** 352.564 bytes (71 %), sin avisos nuevos con -Wall.

## Estado / pendiente
- PlatformIO no está disponible en el entorno de Claude. Igual se compila y enlaza todo con `pruebas/compilacion-manual/` (ver etapa 6). El firmware oficial lo compila GitHub Actions.
- Los perfiles no se abrieron en los slicers reales (no se puede instalar Cura acá). Se validaron contra la foto de ajustes de Cura 5.10 y contra el firmware.
- Sin confirmar en la máquina: el largo de 100 mm del 2 en 1 (sale del perfil oficial de Hellbot).
- Pendiente del usuario: compilar, flashear, correr `docs-magna/PRUEBAS-EN-IMPRESORA.md` y `CALIBRACION.md`, e importar los perfiles.

## Decisiones
- Tamaño 230×230×250 del manual (el bin original usaba 500×500).
- Sin UBL; nivelación manual de la interfaz MKS.
- `EMERGENCY_PARSER` activado (lo exige ADVANCED_PAUSE con la interfaz MKS).
- `SERIAL_PORT_2` desactivado (la placa no tiene USB nativo).
- ADVANCE_K = {0, 0} hasta calibrar.
- Sin control UART de los TMC2209 (la Robin Nano 1.3 no lo cablea).

## Pruebas
- `python3 pruebas/preflight.py`: chequeos de preflight de PlatformIO.
- `bash pruebas/sanity-check.sh`: SanityCheck de Marlin con g++.
- `bash pruebas/verificar-valores.sh`: 31 valores clave.
- `python3 pruebas/verificar-perfiles.py`: perfiles vs firmware.
