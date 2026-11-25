# CLAUDE.md — Marlin para Hellbot Magna 2 230 (y 300/400/500 sin probar)

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
- Capturas en `docs-magna/capturas/`: desde la etapa 36 salen del render real (`pruebas/render-lvgl`, ver etapa 36); `assets-tema/generar_capturas.py` (simulación vieja) ya no se usa para el README.
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

### Etapa 18 (2026-11-13) — botones propios, letra grande en los mensajes y barras del tema
- **Botones en Ajustes → Más:** `CUSTOM_MENU_MAIN`, `MAIN_MENU_ITEM_1..6`. La interfaz MKS los muestra en `draw_more.cpp` con `bmp_custom1..6` y los ejecuta con `queue.inject`, sin confirmar.
  - Calib. hotend: `M306 T` + `M500`.
  - Calib. cama: `M303 E-1 S60 C8 U1` + `M500`.
  - Estacionar 1/2 (E-100) y Cargar 1/2 (E+100 y purga de 20), a 210 °C con `M217 S0`.
- **Íconos nuevos en `generar_assets.py`:**
  - `g_calibrar` (objeto + curva de temperatura) para custom1-2;
  - `g_dos_en_uno_flecha` para custom3-6;
  - custom7 queda genérico.
- **Letra grande:**
  - `assets-tema/generar_fuente.py` genera `fuente_grande.inc`: Roboto 26 px, 4 bpp, ASCII + Latin-1, 191 caracteres, ~25 KB. Es formato `lv_font_fmt_txt` de LVGL 6.1 con inicializadores posicionales (vale en C y C++). Se commitea generada.
  - `aplicar_colores.py` crea `mks_ui/magna_fuente_grande.cpp` con ese contenido.
  - Solo se usa si el idioma es latino (`magna_idioma_latino()`: EN/DE/FR/SP/IT/PT).
- **Mensajes (`draw_dialog.cpp`):**
  - Al final de `lv_draw_dialog`, `magna_texto_grande(labelDialog)`: letra grande, salto de línea a 460 px, centrado, mantiene la altura y queda por encima de los botones.
  - En los mensajes de calentar, la temperatura también va grande, a -95 en vez de -50.
  - `BTN_OK_Y`/`BTN_CANCEL_Y` pasan de 180 a 250.
  - Barra de carga/descarga: 400×34 en y=160, con `magna_estilo_barra`.
- **Barras:** `estilo_dialogos.inc` → `magna_estilo_barra(barra, letra)`: fondo #222→#161616 redondeado con borde #6A1418 y relleno rojo #E62A30→#9A161C. La de impresión (`draw_printing.cpp`) usa la letra grande para el porcentaje.
- **Prueba de render ampliada:** `render.c` tiene los modos principal, menu, mas, carga, calentando e imprimiendo, con el mismo código .inc. La letra normal se simula con Roboto 16 generada en /tmp.
  - Revisa: botones con ícono, texto grande (≥ 40 filas), barra roja/vacía oscura, Cancelar visible, temperatura y texto sin encimarse, porcentaje visible.
- **Resultado:**
  - Firmware 381.136 bytes (77 %; la letra suma ~28 KB). Preflight y SanityCheck OK.
  - Sin avisos nuevos con -Wall. Los avisos `-Wexpansion-to-defined` de `draw_more.cpp` son de la macro `HAS_USER_ITEM` de Marlin, que ahora se compila.

### Etapa 19 (2026-11-13) — imagen en lugar de la "G" de la pantalla de impresión
- La "G" azul es `bmp_preview.bin` de Makerbase. Es la vista previa por defecto cuando el gcode no trae miniatura MKS: 200×200 RGB565 LE sin encabezado (80.000 bytes), que `draw_default_preview` copia directo a la pantalla en (2,36), sin LVGL ni transparencia.
- `generar_assets.py` → `vista_previa()`: recorte de la pieza del arranque (el tornillo a medio imprimir, centrado en x=385, con el borde derecho espejado porque la pantalla termina), borde gris, franja roja y "SIN VISTA PREVIA". Ahora son 139 assets.
- `verificar-assets.py` acepta `bmp_preview.bin` como imagen sin encabezado de 80.000 bytes.
- La vista previa real de la pieza depende del slicer (miniatura MKS dentro del gcode). El usuario no la quiere: no se hace.

### Etapa 20 (2026-11-13) — versión con BLTouch (dos firmwares por compilación)
- `variantes/bltouch.py <raíz>` aplica reemplazos exactos e idempotentes, marcados `// Magna2-230 BLTouch`. Falla si no encuentra alguno.
  - Configuration.h:
    - BLTOUCH, con `Z_MIN_ENDSTOP_HIT_STATE HIGH` (señal en Z-, servo en PA8 = SERVO0_PIN de pins_MKS_ROBIN_NANO_common.h);
    - AUTO_BED_LEVELING_BILINEAR con GRID 5;
    - ENABLE_LEVELING_AFTER_G28, para no tocar los perfiles;
    - Z_SAFE_HOMING y MULTIPLE_PROBING 2;
    - NOZZLE_TO_PROBE_OFFSET {0,0,0}: Z=0 es seguro, la boquilla queda en el aire;
    - PROBING_MARGIN 45, seguro con soportes de hasta 45 mm, porque el offset del soporte del usuario se desconoce (charlieburgos solo tiene binarios de la 300 BLT y no hay soporte estándar).
  - Configuration_adv.h: PROBE_OFFSET_WIZARD (START_Z -1) y BABYSTEP_ZPROBE_OFFSET.
- **Arreglo de Marlin 2.1.3-b3:** `lcd/menu/menu_probe_offset.cpp` se compila con PROBE_OFFSET_WIZARD aunque no haya MarlinUI (features.ini) y falla con "screenFunc_t does not name a type". Se le agrega `&& HAS_MARLINUI_MENU` en el `#if`; la pantalla MKS usa su `draw_z_offset_wizard.cpp`.
- `aplicar_colores.py`: en `draw_tool.cpp`, el botón de nivelación con ABL inyecta `G28\nG29\nM500`. Antes leía el comando guardado en la flash SPI, que por defecto es "G29N\nM500"; G29 sin home falla con `homing_needed_error`. Solo se compila con BILINEAR.
- **Workflows:**
  - `compilar-mm2.yml` compila la normal y después aplica la variante, corre preflight y SanityCheck, recompila y sube dos artefactos: `Magna2-230-firmware` y `Magna2-230-firmware-BLTouch` (este con BLTOUCH.md).
  - `publicar-release.yml` agrega `Magna2-230-firmware-BLTouch-<v>.zip`.
- **Verificado local:** variante aplicada dos veces (idempotente), preflight y SanityCheck OK, compilación completa de 395.464 bytes (80 %), con G29, M851, LevelingBilinear y BLTouch enlazados.
- **Docs:** `docs-magna/BLTOUCH.md` (conexión, offsets, asistente Z, Autolevel, problemas).

### Etapa 21 (2026-11-13) — apagado automático de la pantalla
- `MAGNA_PANTALLA_APAGADO_MIN 5` (Configuration_adv.h, opción propia; 0 = desactivado).
- `aplicar_colores.py` reemplaza el comienzo de `my_touchpad_read` en `tft_lvgl_configuration.cpp`. Agrega `magna_pantalla_despertar()` y `magna_pantalla_revisar()`, que se llaman en cada lectura del táctil (LVGL lee cada ~30 ms, así que no hace falta otro temporizador).
  - Con el tiempo cumplido: `WRITE(TFT_BACKLIGHT_PIN, LOW)` (PD13).
  - El toque que la prende se "traga": se informa REL hasta que se suelta.
- `lv_screen_create` llama a `magna_pantalla_despertar()`, así cualquier pantalla nueva (diálogos de filamento, fin de impresión, pausa) la prende. `GUI_RefreshPage` solo recrea pantallas en los avisos de WiFi.
- Compilado: 381.352 bytes (77 %). La función queda enlazada y el preprocesado confirma que escribe PD13.

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
- `bash pruebas/verificar-buffer-pantalla.sh <firmware.elf>`: el buffer de imagen de la pantalla tiene que quedar alineado (si no, colores corridos).
- `python3 pruebas/verificar-perfiles.py`: perfiles vs firmware.

### Etapa 22 (2026-11-14) — prender/apagar la pantalla por WiFi (M256)
- Para el botón de pantalla de MagnAir (firmware/página/apps del módulo WiFi, repo aparte).
- `aplicar_colores.py` agrega `magna_pantalla_apagar()` y `magna_pantalla_encendida()` junto al apagado automático (tft_lvgl_configuration.cpp). En `wifi_module.cpp` (función `wifi_gcode_exec`), un `case 256` antes del `case 115`: "M256" responde `M256 B255` o `M256 B0`, "B0" apaga, "B1".."B255" prende. Lo atiende la UI MKS y no pasa por la cola de G-code. Marlin no define M256 con esta pantalla (requiere `HAS_LCD_BRIGHTNESS`). Si se apaga a mano, el primer toque la prende sin apretar nada, y cualquier pantalla nueva (avisos) también la prende.
- Ojo con las comillas: el reemplazo está dentro de un string de Python, por eso en `aplicar_colores.py` se escribe `\\r\\n`. La primera versión metía saltos de línea reales dentro del literal de C y no compilaba.
- Compilación manual completa: 381.476 bytes (77 %).

### Etapa 23 (2026-11-14) — calibración guardada (M257) y carpetas de la SD por WiFi
- Para MagnAir etapa 6. Todo en `aplicar_colores.py`, sobre `wifi_module.cpp`.
- **M257** (`case 257` dentro de `wifi_gcode_exec`, junto al M256): `magna_m257()` manda por WiFi una línea por grupo, `M257 <grupo> K=v ...`, y `M257 fin`. Grupos: `mpc` P C R A F H (o `pidhotend` P I D), `pidcama` P I D, `pasos` X Y Z E0 E1, `avance` K0 K1, `vibraciones` XF XD YF YD, `altura` S Z (S=1 `probe.offset.z`, S=0 `home_offset.z`), `velmax` y `acelmax` X Y Z E, `acel` P R T. Hace falta porque la UI MKS no reenvía al WiFi la salida de M503. Los números con `dtostrf`. Includes nuevos: planner.h, stepper.h, motion.h y probe.h (si `HAS_BED_PROBE`).
- **Carpetas:** `get_file_list` toma la ruta de `M20 L /DIR`, hace `card.cd()` por cada parte, lista y vuelve con `card.cdroot()` (el original ignoraba la ruta). M23/M24 usan la ruta completa (`strchr(name+1,'/')`) en lugar del último `/`, con el comportamiento viejo como respaldo.
- Compilación manual completa: normal 382.612 bytes (77 %), BLTouch 396.880 bytes (80 %).

### Etapa 24 (2026-11-14) — créditos en "Acerca de"
- Pedido del usuario: que la información del sistema de la impresora diga "Creado por Andrés Londero" y su correo.
- `assets-tema/creditos.inc` → `magna_creditos(scr, estilo, latino)`: dos etiquetas abajo a la izquierda (x 12, y 236 y 272), a la izquierda del botón Atrás (x ≥ 359, y ≥ 178). El nombre va con la letra grande (Latin-1, por la "é"); en idiomas no latinos va "Created by Andres Londero" con la letra de la pantalla. El correo en rojo claro con la letra normal. Ojo: `lv_label_create(scr, (lv_obj_t *)NULL)` con el cast, porque MKS tiene una sobrecarga `lv_label_create(scr, const char *texto)` y `NULL` solo sería ambiguo en C++.
- `aplicar_colores.py` pega el `.inc` antes de `lv_draw_about()` en `draw_about.cpp` y llama a `magna_creditos()` después de la línea "Protocol".
- Prueba de render: modo `acerca` en `render.c`; `verificar_render.py` controla que se vean el nombre y el correo y que no se metan en el botón Atrás.
- Compilación manual completa: 382.856 bytes (77 %).

### Etapa 25 (2026-11-14) — revertida
- Se había puesto fondo negro liso y texto en español en el aviso "Updating wifi model firmware" (franjas de colores en una foto del usuario). El usuario pidió volver atrás: **no cambiar nada de la interfaz sin consultarlo antes**. Quedó exactamente como en la etapa 24 (degradé de siempre).

### Etapa 26 (2026-11-14) — CAUSA REAL de los colores corridos en toda la pantalla
- Síntoma (fotos del usuario): todas las pantallas, incluso el logo de arranque, con los colores corridos (rojo → azul/cian, franjas en el degradé). Con el firmware original de Hellbot se veía bien; con el nuestro de anoche (23 hs) también.
- Diagnóstico: simulando la imagen con los 2 bytes de cada píxel invertidos sale idéntica a la foto. Los dos firmwares mandan la misma inicialización ILI9488 (verificado en los binarios). La diferencia está en `bmp_public_buf` (`tft_lvgl_configuration.cpp`), el buffer por donde pasa TODA la imagen: el logo (`lcdDrawLogo`), LVGL (`lv_disp_buf_init`) y las vistas previas. Está declarado `uint8_t bmp_public_buf[16 * 1024]`, sin alineación. En el firmware actual quedaba en **0x2000d625 (impar)**. El DMA del FSMC copia de a media palabra (2 bytes) y con una dirección impar lee corrido un byte → colores corridos. Cada variable nueva mueve el buffer: anoche cayó par por casualidad, y las etapas 21 a 24 lo dejaron impar.
- Arreglo (`aplicar_colores.py`): `__attribute__((aligned(4))) uint8_t bmp_public_buf[16 * 1024];`. Ahora queda en 0x2000d628. No cambia nada de la interfaz.
- Para que no vuelva a pasar: `pruebas/verificar-buffer-pantalla.sh <firmware.elf>` falla si el buffer no queda en un múltiplo de 4. El workflow lo corre después de cada `pio run` (normal y BLTouch).
- Lección: un buffer `uint8_t` que se manda por DMA de 16 bits tiene que estar alineado; un error así aparece y desaparece solo según el tamaño de las otras variables.

### Etapa 27 (2026-11-14) — M257 informa protecciones y estadísticas (para MagnAir 1.1)
- `magna_m257()` agrega dos grupos al final (antes de `M257 fin`):
  - `extras`: `PLR` = recuperación tras corte de luz (`recovery.enabled`, M413), `SF` = sensor de filamento (`runout.enabled`, M412), `SFD` = distancia del sensor en mm. -1 = la función no está compilada.
  - `estadisticas` (con `PRINTCOUNTER`): `N` impresiones, `OK` terminadas, `T` segundos imprimiendo, `L` la más larga (s), `F` filamento total (mm), de `print_job_timer.getStats()` (los datos en RAM, al día aunque `PRINTCOUNTER_SAVE_INTERVAL` sea 0).
- Includes nuevos en `wifi_module.cpp`: printcounter.h, powerloss.h y runout.h (cada uno con su condición).
- MagnAir los usa para: el historial (filamento de cada impresión = diferencia de `F` entre el principio y el final), las estadísticas, y los interruptores de Control → Protecciones.
- La recuperación tras corte de luz sigue apagada de fábrica (`PLR_ENABLED_DEFAULT false`); se prende desde MagnAir (M413 S1 + M500).
- Compilación manual completa: 383.128 bytes (77 %); `bmp_public_buf` sigue alineado (0x2000d628).

### Etapa 28 (2026-11-14) — ventilador del hotend automático (HE1)
- Pedido del usuario: que el ventilador del disipador del hotend no quede siempre prendido.
- Cableado real (fotos del usuario): cable de red de 4 pares hasta el hotend. Marrón/blanco = calentador (HE0 − y HE1 +; los "+" de HE0/HE1 son 24 V fijos y el MOSFET corta el "−"); naranja/blanco = FAN (capa, PB1); azul/blanco = TH1 (termistor); verde/blanco = ventilador del disipador en un conector **+12/24V− fijo** (abajo a la derecha). El rojo/negro de al lado, también fijo, es otro ventilador (no se toca).
- `Configuration_adv.h`: `E0_AUTO_FAN_PIN PB0` (salida HE1; con `SINGLENOZZLE` hay un solo hotend y PB0 era `FAN1_PIN`, que Marlin deja de usar como ventilador M106 cuando coincide con un auto-fan). Se prende arriba de 50 °C (`EXTRUDER_AUTO_FAN_TEMPERATURE`) a velocidad 255.
- **Cambio de cables (lo hace el usuario, después de instalar este firmware, con todo desenchufado):** sacar el verde/blanco del conector +12/24V; el cable del pin "+" a HE0 + (libre) y el del "−" a HE1 −. Probar: calentar a 60 °C → tiene que girar; si no gira, apagar enseguida (sin ventilador el calor sube y tapa el hotend) y revisar la polaridad.
- Con el firmware viejo y los cables ya movidos el ventilador **no** giraría nunca: el orden es firmware primero, cables después.
- Compilación manual completa: 383.168 bytes (77 %); `bmp_public_buf` alineado (0x2000d630).


### Etapa 29 (2026-11-14) — maquetas de ideas visuales (todavía NO están en el firmware)
- El usuario pidió ver todas las ideas visuales antes de elegir. `assets-tema/maquetas_visuales.py <lvgl> <salida>` dibuja con PIL, los íconos reales del tema, el degradé y la Roboto de la UI MKS (posiciones de `draw_printing.cpp`): 00 actual, 1 tiempo restante y hora de fin, 2 capa actual/total, 3 barra más grande, 4 miniatura de Cura (en la etapa 19 el usuario no la quiso; se mostró igual porque pidió ver todo), 5 resumen al terminar, 6 íconos de estado (WiFi, Telegram), 7 reloj, 8 gráfico de temperaturas, 9 mapa de nivelación (solo versión BLTouch), 10 = 1+2+3 juntos. Salida en `assets-tema/preview/propuestas/` (con dos hojas).
- Pendiente: que el usuario elija. Nada de esto se programa sin su aprobación.
- (misma etapa) El usuario aprobó TODO lo de las maquetas: miniatura de Cura si el gcode la trae (si no, el tornillo), íconos WiFi/Telegram y la hora; además pidió la hora chica en todas las pantallas. Preguntó por animaciones y por copiar cosas de otros sistemas: `assets-tema/maquetas_animadas.py` genera GIF (a1 impresión con ventilador girando, brillo en la barra y temperatura que cambia de color/titila; a2 arranque con el tornillo imprimiéndose; a3 nivelación en vivo; a4 recorrido en vivo de la capa) y fijas (b1 siempre encendida atenuada, b2 mensaje desde MagnAir/Telegram, b3 hora en los menús, b4 asistente de tornillos (G35/ASSISTED_TRAMMING), b5 bloqueo de pantalla, b6 cancelar una pieza (M486/CANCEL_OBJECTS)). `generar_assets.logo(progreso)` y `fondo_capas(..., progreso)` aceptan el avance (por defecto 0.55, igual que antes).
- Condición del usuario: que el sistema no quede inútil ni pesado → animaciones chicas, a pocos cuadros por segundo, con opción para apagarlas.

### Etapa 30 (2026-11-14) — pantalla: hora, capas, "faltan / fin" e íconos de estado
- Pedido del usuario: "Hace todo" (las ideas de las maquetas de la etapa 29). Se hace por partes; esta es la primera.
- Código de pantalla en `assets-tema/magna_extras.inc` (C puro; lo compila también la prueba de render) y los cambios en el código de Marlin en `assets-tema/extras_pantalla.py` (lo llama `aplicar_colores.py` al final: archivos nuevos `mks_ui/magna_extras.cpp` y `mks_ui/magna_fuente_chica.cpp`, y 14 reemplazos exactos).
- **Hora:** la manda MagnAir 1.3 con `M258 S.. D.. F.. O.. T..` (case 258 en `wifi_module.cpp`); se cuenta con `millis()`. Hora chica (Roboto 14, `fuente_chica.inc`) arriba a la derecha en todas las pantallas menos la principal: un solo objeto en `lv_layer_top()`, creado en `tft_lvgl_init` y actualizado una vez por segundo por `magna_tick()` (desde `LV_TASK_HANDLER`). En la principal: hora grande (fuente grande), fecha ("sáb 14/11") e íconos dibujados con líneas: WiFi (blanco si `wifi_link_state == WIFI_CONNECTED`, gris si no) y avión de papel si hay bot.
- **Capas:** `M259 L<capa> T<total>` (case 259 en `gcode.cpp`), que agrega Cura con dos "Buscar y reemplazar" (`docs-magna/CURA-PANTALLA.md`). Se ponen en cero en `reset_print_time()`.
- **Pantalla de impresión:** barra en y = 32 (antes 36), línea "Capa 57/210 · faltan 2:15 · fin 23:40" debajo (cada parte solo si se sabe; lo que falta = `M73 R` o estimado con el tiempo y el %, desde el 3 %); el reloj muestra el tiempo transcurrido (antes, con SET_REMAINING_TIME, mostraba "HH:MM R").
- **Vista previa de la pieza:** ya la tenía la UI MKS (miniatura MKS en el gcode; si no, el tornillo). Solo se documentó el plugin de Cura.
- Pruebas: `render.c` modos `textos` (12 pruebas de los textos), `impresion2` y `principal2`, con chequeos en `verificar_render.py`. Compilación completa: 395.464 bytes (80 %); RAM: sin búferes grandes nuevos.
- LVGL de MKS: `LV_USE_ANIMATION 0` y `LV_MEM_SIZE` 16 kB → las animaciones de la etapa siguiente se hacen con `lv_task`/`magna_tick` y pocos objetos. Ojo: `aplicar_colores.py` no es idempotente con el código de los menús (correrlo una sola vez sobre un Marlin limpio).

### Etapa 31 (2026-11-14) — resumen al terminar, mensajes, bloqueo, "siempre encendida" y melodías
- Todo en `magna_extras.inc` (sección "Etapa 31") + unión con Marlin en `extras_pantalla.py` (7 reemplazos nuevos). Usa la capa de arriba de LVGL (`lv_layer_top()`) con un contenedor de 480×320 que tapa y recibe los toques; lo que se cierra con un toque se oculta y se borra en el próximo `magna_tick()` (nunca dentro del evento).
- **Opciones** (llegan en el M258 de MagnAir: `A` bits 1 animaciones, 2 melodías, 4 siempre encendida; `P` precio por kilo; `G` densidad × 100). Sin MagnAir: todo prendido, sin costo.
- **Resumen al terminar:** el mensaje "Impresión terminada" sube el título y agrega Tiempo (print_time), Filamento (gramos y metros: `print_job_timer.getStats().filamentUsed` al terminar menos al empezar; el temporizador lo arranca el M109/M190 del gcode) y Costo (si hay precio). Fórmulas iguales a las de MagnAir (1,75 mm).
- **Mensajes:** `M117 texto` por WiFi → caja con "Mensaje desde MagnAir", el texto en letra grande y "Entendido". Prende la pantalla.
- **Bloqueo:** candado arriba en la pantalla de impresión (x 380–430); tapa con "Pantalla bloqueada" y un deslizador (`lv_slider`) que hay que llevar hasta el final. Se desbloquea sola cuando termina la impresión.
- **Siempre encendida:** cuando la pantalla se iba a apagar sola (MAGNA_PANTALLA_APAGADO_MIN) y está imprimiendo, en vez de apagarse muestra negro con la hora, el porcentaje enorme (Roboto 72 solo "0-9 % :", `fuente_enorme.inc`, `generar_fuente.py ... numeros`), una barra fina y "termina 23:45 · faltan 2:35". El primer toque la saca sin apretar nada (como con la pantalla apagada); una pantalla nueva también.
- **Melodías** (zumbador PC5, `BUZZ`): do-mi-sol-do al terminar; tres pitidos cuando pide poner filamento (PAUSE_MESSAGE_INSERT/WAITING). 4 notas como mucho (la cola del zumbador es de 4).
- **Brillo según la hora: NO se hizo.** La luz de la pantalla (PD13) solo se puede atenuar con PWM del TIM4, y este firmware usa el TIM4 para el puerto serie por software (`-DSS_TIMER=4`): podría romper la comunicación con los drivers. Se dejó prendido/apagado como antes.
- Pruebas: `render.c` modos `resumen`, `mensaje`, `bloqueo`, `ambiente` y 7 textos más (duración, filamento, costo). Compilación: 414.304 bytes (84 %), RAM .bss 80,6 kB.

### Etapa 32 (2026-11-14) — animaciones livianas y arranque animado
- **Pantalla de impresión** (`magna_extras.inc`, sección "Etapa 32"): una sola `lv_task` cada 120 ms (`magna_anim_iniciar`). Ventilador que gira (3 imágenes `bmp_fan_state`, `bmp_fan_state1/2` = girado 40° y 80°; a 100 % cambia cada 120 ms, más lento si el ventilador va más lento), brillo que recorre la parte llena de la barra (objeto de 10 px, 40 % de opacidad, hijo de la barra) y color del número de temperatura del hotend y la cama (`magna_color_temp`: azul frío → blanco → rojo) que titila mientras calienta. Solo redibuja si algo cambió. Se apagan con la opción de MagnAir (A bit 1), con la pantalla apagada o con "siempre encendida".
- `magna_tick` le pasa a las animaciones ventilador, temperaturas y si están activas; los objetos se registran al crear la pantalla de impresión y se olvidan en `lv_clear_printing()`.
- **Arranque animado:** `bmp_logo.bin` ahora es el logo con el tornillo SIN imprimir; `bmp_tornillo1..3.bin` (RGB565 sin encabezado, filas de ABAJO hacia ARRIBA, ~3 kB comprimidas cada una) tienen el tornillo terminado. `magna_arranque_animado()` (`animacion_arranque.cpp.inc`, constantes en `animacion_arranque.inc`, las dos generadas/usadas por `generar_assets.py`) corre en `TFT::lcdInit()` después del logo: 16 pasos de 80 ms copiando filas nuevas con `SPIFlash.readData` (los íconos están comprimidos y solo se leen de corrido) y la boquilla dibujada encima; después espera 0,8 s (antes 2 s fijos). Si faltan las imágenes, logo quieto.
- `assets-tema/simular_arranque.py` hace lo mismo en la compu con los mismos archivos y verifica que la última imagen sea el tornillo terminado (también en el workflow, junto a la prueba de render). `verificar-assets.py` acepta las tiras (sin encabezado, < 9 kB comprimidas).
- **Hay que copiar la carpeta `assets` nueva a la SD** (ventilador y arranque). Con los assets viejos todo funciona, solo sin esas dos animaciones (y el logo viejo queda al 55 %).
- `generar_assets.logo(progreso, boquilla)`; `g_ventilador(giro)`. Compilación: 416.284 bytes (84 %).

### Etapa 33 (2026-11-14) — gráfico de temperaturas, nivelación en vivo, cancelar piezas y vista en vivo
- **Gráfico:** `magna_hist_agregar` guarda una muestra cada 5 s (hotend, objetivo, cama, objetivo; 120 muestras = 10 min, 960 bytes). `magna_grafico_abrir()`: tapa con `lv_chart` (4 series, 0–250 °C) y leyenda; se actualiza cada segundo. Se abre con el botón del gráfico (arriba en la pantalla de impresión, x 330) o abajo a la derecha en la principal.
- **Nivelación en vivo (versión BLTouch):** al tocar Nivelación (G28 + G29 + M500) se abre una tapa con la grilla (GRID_MAX_POINTS, 5×5); `magna_tick` lee `bedlevel.z_values` mientras G29 la llena (idle() corre LV_TASK_HANDLER entre puntos) y pinta cada celda verde (≤ 0,05 mm), amarilla (≤ 0,10) o roja, con el valor; al terminar, "Diferencia máxima" y un consejo.
- **Cancelar piezas:** `M262 <nombre>` (agregado a la lista de códigos con texto en `parser.cpp`) lo pone Cura en cada `;MESH:` (tercer "Buscar y reemplazar", `docs-magna/CURA-PANTALLA.md`). Cada nombre nuevo es una pieza (hasta 12); usa CANCEL_OBJECTS de Marlin (`cancelable.set_active_object` / `cancel_object`). Botón de los dos cuadraditos (x 280) → lista con "Cancelar".
- **Vista en vivo:** cada G1 que extruye (enganche en `G0_G1.cpp` después de `get_destination_from_command()`) se dibuja con Bresenham en un búfer de 1 bit de 200×200 (5 kB, `LV_IMG_CF_INDEXED_1BIT`, `lv_canvas`); una Z nueva con extrusión borra (capa nueva). Tocando la vista previa se alterna con la miniatura (al volver, se pide redibujar la miniatura igual que MKS al volver a la pantalla de impresión).
- Pruebas: render modos `grafico`, `nivel`, `piezas`, `vivo`. Compilación: 425.780 bytes (86 %); versión BLTouch 441.444 (89 %).
- **Pendiente: asistente de tornillos (G35/ASSISTED_TRAMMING)** — necesita la posición de los 4 tornillos de la cama y la rosca (M3/M4); se le preguntó al usuario.

### Etapa 34 (2026-11-14) — M263: mensaje en la pantalla desde el gcode
- `M263 <texto>` (agregado a la lista de códigos con texto de `parser.cpp`, case 263 en `gcode.cpp`, `magna_m263()` en magna_extras.cpp): muestra la caja de mensaje (la misma del M117 por WiFi) y prende la pantalla. Lo agrega el editor de gcode de MagnAir ("Mensaje en la pantalla" en una capa). 425.852 bytes (86 %).

### Etapa 35 (2026-11-15) — arreglos vistos en la impresora
- **Hora chica centrada arriba** en las subpantallas (`magna_reloj_mostrar`): a la derecha se pisaba con "MAGNA" del título. La pantalla principal no cambia. `verificar_render.py` ahora la busca al medio.
- **Íconos en blanco al volver del gráfico** a la pantalla principal: los íconos de MKS se leen comprimidos de la memoria SPI de principio a fin, y al borrar la tapa LVGL redibujaba la pantalla de abajo por pedazos. Ahora, al cerrar una tapa (gráfico, piezas, nivelación), `mg_cerrar_pendientes` llama a `magna_rehacer_pantalla` (glue en `extras_pantalla.py`, se registra con `magna_rehacer_funcion`): limpia la caché de imágenes y vuelve a armar la principal o la de impresión como cuando se vuelve desde un menú; en otras pantallas solo la invalida.
- El usuario vio lo mismo al cerrar un **mensaje** (M117 / `/mensaje`): ahora cualquier cosa que tapa la pantalla pide rehacerla al cerrarse (`mg_pedir_rehacer`: mensaje, bloqueo, "siempre encendida", gráfico, piezas, nivelación) y se hace en el tick (`mg_rehacer_si_hace_falta`, nunca dentro de un evento de LVGL; no mientras sigue "siempre encendida"). En pantallas que no son la principal ni la de impresión se repite la pantalla arriba de la pila y se usa `clear_cur_ui()` + `draw_return_ui()`, como los diálogos de MKS.
- Compila: 426.044 bytes (86 %). Sin probar en la impresora todavía.

### Etapa 36 (2026-11-15) — README nuevo con capturas por sección
- Pedido del usuario: descripciones de GitHub escritas con naturalidad (sin sonar a texto de IA ni sobreexplicar), capturas actualizadas y cada sección con sus capturas.
- `README.md` reescrito: secciones de la pantalla (principal, imprimiendo, al terminar, mensajes/bloqueo/siempre encendida, menús, BLTouch), qué cambia en Marlin, ventilador por HE1 (verde +, blanco −), hardware, perfiles, WiFi, compilar, instalar, calibrar, créditos. Sin referencias a etapas ni a este archivo.
- `docs-magna/capturas/`: PNG 480 × 320 del render real (`verificar_render.py` deja `/tmp/rnd-<modo>.png`: principal2→principal, grafico, piezas→cancelar-pieza, resumen, carga→carga-filamento, mensaje, bloqueo, ambiente→siempre-encendida, menu→menu-ajustes, mas, nivel→nivelacion-bltouch, acerca); `imprimiendo.png` = render impresion2 con la imagen de la pieza pegada (la prueba no carga la vista previa); `arranque.gif` de `simular_arranque.py`; `iconos.png` se mantiene. Las capturas viejas (simuladas) se borraron.
- Al hacer las capturas se vio que la hora chica (ahora al medio) se pisaba con los títulos de las tapas (gráfico, piezas): `mg_tapa_visible()` la esconde mientras algo de 480 × 320 tapa la pantalla. Render: 0 fallas.

### Etapa 37 (2026-11-15) — íconos animados y lectura de íconos desde cualquier fila
- El usuario no veía animaciones (solo el arranque): las de la etapa 32 eran solo de la pantalla de impresión (ventilador si gira, brillo de la barra, color de las temperaturas). Ahora también:
  - **Cuadros nuevos** (`generar_assets.py`, 45 × 45): `bmp_bed_state1/2` (el calor sube y la línea roja pasa de una a otra) y `bmp_ext1_state1/2` (la gota se forma y cae). Agregados a la lista de `pic_manager.cpp` (148 assets; la memoria SPI de 16 MB tiene lugar de sobra).
  - `magna_anim_iconos(hotend, cama)`: en `mg_an_tarea`, un cuadro cada 360 ms mientras tienen temperatura pedida o siguen calientes (cama ≥ 40 °C, hotend ≥ 50 °C); quietos en el primer cuadro si no. Se registra en la pantalla de impresión y en la principal (que además registra sus temperaturas para el color y el titileo); `lv_clear_ready_print` llama a `magna_anim_olvidar`.
  - Siguen dependiendo de la opción "Animaciones" de MagnAir (por defecto prendida) y se frenan con la pantalla apagada o en "siempre encendida".
- **Causa de fondo de las rayas e íconos en blanco**: los íconos están comprimidos (RLE) y `spi_flash_seek_cb` solo sabía volver al principio. Si LVGL redibujaba un pedazo de un ícono (zonas de dos textos que se juntan, algo que lo tapaba, un cambio de cuadro) leía filas corridas. Ahora `tft_lvgl_configuration.cpp` lleva la posición real (`magna_pos_flash`): para adelante saltea descomprimiendo, para atrás vuelve al principio y avanza. El rehacer de la etapa 35 queda igual (no molesta).
- Compila: 426.724 bytes (86 %). Render y assets OK. Sin probar en la impresora.


### Workflows al día (2026-11-15)
- Avisos de GitHub (Node.js 20 obsoleto, setup-java v4, ubuntu-latest pasa a Ubuntu 26): acciones subidas a las versiones que corren en Node 24 (checkout v6, cache v5, setup-java v5, setup-node v5, setup-python v6, upload-artifact v6, download-artifact v7, gradle/actions/setup-gradle v5, softprops/action-gh-release v3) y los trabajos de Linux fijos en `ubuntu-24.04` (el cambio a Ubuntu 26 podría romper PlatformIO o el compilador; se sube a mano cuando convenga).

### Etapa 38 (2026-11-15) — aviso de errores y precalentado desde MagnAir
- `M264 P<0..2> H<hotend> B<cama>` (nuevo, `magna_m264` en `extras_pantalla.py`): guarda en RAM los precalentados que manda MagnAir (0 = PLA, 1 = PETG, 2 = ABS). `magna_pre_temp(material, cual, predeterminada)` los devuelve o la de siempre si no llegaron. `draw_preHeat.cpp` (cambio `PRE_CAMBIOS`) los usa en los botones PLA/ABS. No es `M145` porque la UI de MKS no tiene los presets de MarlinUI.
- Errores: `draw_error_message.cpp` llama a `magna_avisar_error(motivo)` (débil, para que compile sin WiFi); `wifi_module.cpp` la define y manda `Error:MAGNA_DETENIDA <motivo>` al módulo con `package_to_wifi` + `flush` (la impresora se queda detenida después, así que tiene que salir ya).
- Compila: 86 % de la flash.

### Etapa 39 (2026-11-15) — otros modelos (sin probar), pantalla en castellano y carpeta _assets
- **Modelos** 300, 400, 400D, 500 y 500D: valores de los firmware oficiales de Hellbot ("Marlin-2.0.3-Magna-2-XXX-Placa v1.3": mismo `.bin` para todos, lo que cambia es `robin_nano35_cfg.txt`; los paquetes D son idénticos a los sin D). `variantes/modelo.py MODELO` hace los reemplazos exactos (marca `// Magna2-XXX`), corre `bltouch.py` en 400/500 y define `MAGNA_SIN_PROBAR`. Decisiones propias y tabla comparada: `docs-magna/MODELOS.md`. **Solo la 230 está probada**: los paquetes se llaman `Magna2-XXX-firmware-UNTESTED`, llevan `LEEME-SIN-PROBAR.txt` y Acerca de muestra "Magna 2 XXX - SIN PROBAR". INVERT_Z_DIR es false en los oficiales (true en la 230).
- `variantes/armar.sh MODELO SALIDA`: variante + tema + pruebas (verificar-valores y perfiles solo en la 230) + `pio run` + carpeta para la SD + letra con acentos. Lo usan los dos workflows, que ahora compilan los 7 (230, 230-BLTouch, 300, 400, 400D, 500, 500D) en una matriz; `publicar-release.yml` junta los paquetes en un tercer trabajo.
- **Castellano** (`assets-tema/aplicar_idioma.py`, lo llama `aplicar_colores.py` al final; textos en `traduccion_es.py`): `tft_Language_sp.h` completo (el de Makerbase traía ~210 de ~380), el bloque de Español de `disp_language_init` es copia del de inglés con `_SP`, `machine_setting_disp` suma un bloque en Español, las asignaciones fijas en inglés usan `MAGNA_ES(k)`. `LCD_LANGUAGE es`. Pantallas con la letra fija ASCII de 16 px (carga de imágenes, error grave) van sin tildes; el motivo del error se pasa a mayúsculas sin tildes. Lo que sale por serie/WiFi sigue en inglés (lo leen Cura, MagnAir, etc.).
- **Letra**: FontUNIGBK.bin no tenía í ú ü Á É Í Ó Ú Ñ ¡ °. `assets-tema/fuente_acentos.py` las arma con la base + el acento de la é / la tilde de la ñ y las agrega al final (tabla xbf: min/max/bpp, posiciones uint32, avance + ancho + bits a 1 bpp en 21 filas). Lo corre `armar.sh` sobre la carpeta assets.
- **_assets**: `UpdateAssets` borra la `_assets` vieja (`rmRfStar`) antes de renombrar; antes el renombre fallaba y cargaba los íconos en cada arranque.
- **Modelo por WiFi**: M115 por WiFi manda además `MACHINE_TYPE:` CUSTOM_MACHINE_NAME (MagnAir 1.6.0 lo usa para el tamaño de la cama).
- Perfiles: `generar_perfiles.py` genera los 6 modelos (`configurar(modelo)`; al importarlo quedan los de la 230). D: retracción 1 mm y estacionado 60 mm (sin medir). Los de la 230 no cambiaron.
- Compila (local): 230 88 %, 230-BLTouch 91 %, 300 87 %, 400/400D/500/500D 90 %.

### Etapa 40 (2026-11-15) — mm12: placa MKS Robin Nano V1.2 (recortada, sin probar)
- Pedido: versión para las Magna 2 con placa V1.2 (STM32F103VE: 72 MHz, 64 KB de RAM), en otro repo, `mm12.zip`, para 230/300/400/500 (los paquetes oficiales de Hellbot para la V1.2; sus valores de máquina son iguales a los de la V1.3, solo cambian los puntos de nivelación manual y el área del BLTouch).
- **Mismo código**: `mm12.zip` es este proyecto con `README.md` = `docs-magna/README-mm12.md`. Workflows propios: `github-workflows/compilar-mm12.yml` (sube `mm12.zip`, matriz 230/300/400/500) y `publicar-release-mm12.yml`. `variantes/armar.sh MODELO SALIDA 12`.
- `variantes/placa12.py`: MOTHERBOARD BOARD_MKS_ROBIN_NANO (+ `MAGNA_LIVIANO`, `MAGNA_PLACA_12`), sin INPUT_SHAPING ni ADAPTIVE_STEP_SMOOTHING, BLOCK_BUFFER_SIZE 8, `default_envs = mks_robin_nano_v1v2`.
- `assets-tema/liviano.py` (lo llama `aplicar_colores.py` si ve `MAGNA_LIVIANO`): deja vacías las funciones de `magna_extras.cpp` de vista en vivo (5 KB), gráfico, piezas, "siempre encendida", animaciones, arranque animado, bloqueo, resumen, nivelación en vivo y la principal con hora grande (la hora chica va en todas), y `display_qrcode` de la nube de MKS (~2,3 KB). Los cambios en los archivos de MKS no se tocan: llaman a las mismas funciones y el enlazador descarta lo que nadie usa.
- RAM medida (`pruebas/compilacion-manual/compilar_f103.sh`, gcc 13): Marlin sin tema ~62 KB; tema completo ~76 KB (no entraba); mm12 230 = 60.432 bytes, 500 = 60.916 (de 65.536; lo que queda es pila). Flash 80-82 %.
- Ojo: en Marlin la prueba "MKS Robin nano v1.2 LVGL FSMC" está comentada (nadie la verifica en Marlin).
- M115 por WiFi manda también `MAGNA_PLACA:1.3` o `1.2` (aplicar_idioma.py). MagnAir 1.6.0: con "1.2" el módulo consulta cada 5 s y la app y la página esconden animaciones, "siempre encendida" y M593.
- `pruebas/sanity-check.sh`: arreglado (con `pipefail` el resultado de g++ se perdía y siempre decía OK); ahora elige F1 o F4 según la placa. `pruebas/preflight.py` toma el entorno de `platformio.ini`.
- Diagnóstico mm12 (2026-11-16): en una placa V1.2 real, mm12 se reinicia en loop (Booting... → logo → reinicio, ~8 s): se traba al arrancar la pantalla y el watchdog la reinicia. Versión de prueba **B**: `MAGNA_PRUEBA=B` (aplicar_colores.py salta extras_pantalla, castellano y liviano; queda solo el tema). En GitHub: Actions → Compilar Magna 2 placa V1.2 → Run workflow → prueba = B (artefactos `Magna2-XXX-placaV12-PRUEBA-B`). RAM medida de B (230): 62.268 bytes (data+bss) contra 62.940 de mm12: casi igual, porque casi toda la RAM es de Marlin + MKS UI (`bmp_public_buf` 16 KB, que es el buffer de dibujo de LVGL —480×17×2— y el FIFO del WiFi —14 × 1 KB—; heap de LVGL 16 KB). Si B también se reinicia, lo siguiente es achicar `bmp_public_buf` a 8 KB (LVGL de a 8 filas, FIFO de 7 bloques, vista previa de 20 columnas) o pedir el log por USB.

### Etapa 41 (2026-11-24) — subida por WiFi con nombre largo reiniciaba la placa
- Síntoma (230 real): al pasar por WiFi un archivo con nombre largo, la placa se reiniciaba ("Booting...") justo al recibirlo, MagnAir decía que falló y el archivo no quedaba en la SD.
- Causa, en el código de Marlin: `file_first_msg_handle` copia el nombre que manda el módulo (hasta 255 bytes) en `file_writer.saveFileName[30]`, y `utf8_2_unicode` lo pasa por un buffer de pila `FileName_unicode[30]`. Con más de 29 bytes pisa la memoria y la pila. El chequeo contra `saveFilePath` llega tarde (después del memcpy).
- Arreglo (`aplicar_colores.py`, se aplica también en la prueba B y en mm12): `magna_nombre_recortado()` copia como mucho 29 bytes, conservando la extensión (hasta 7 bytes con el punto) y sin cortar una letra UTF-8 a la mitad; `utf8_2_unicode` recibe ese largo. El archivo se guarda con nombre 8.3 (sin LONG_FILENAME_WRITE_SUPPORT), que sale de las primeras letras: queda igual que antes.
- MagnAir 1.6.1 recorta el nombre también del lado del módulo, así anda aunque la impresora tenga un firmware viejo.
- Compilado local (230, V1.3): 433.400 bytes (88 %).

### mm12 descartado (2026-11-24)
- El usuario lo descartó: en la placa V1.2 real no arrancó (loop de reinicio, ver el diagnóstico de arriba). No se sigue armando ni entregando `mm12.zip`.
- Lo de la placa V1.2 que vive en este repo (`variantes/placa12.py`, `assets-tema/liviano.py`, `compilar_f103.sh`, `docs-magna/PLACA-V12.md`, `README-mm12.md`, workflows `*-mm12.yml`) quedó como estaba y no afecta a mm2 (solo se usa con PLACA=12). Si se retoma: Marlin puro con Color UI (sin WiFi de MKS) era la opción con más chances.

### Artefactos de GitHub con vencimiento (2026-11-24)
- Una corrida falló entera con "Artifact storage quota has been hit": los artefactos sin `retention-days` duran 90 días y llenan el espacio gratis de la cuenta (500 MB). Todos los `upload-artifact` de `github-workflows/` tienen ahora `retention-days` (5 días los compilados y las capturas, 3 los reportes de pruebas). Los de publicar-release ya tenían 3 y solo se usan dentro de la misma corrida. Las versiones publicadas (Releases) no cuentan para ese límite.

### Etapa 42 (2026-11-24) — se reiniciaba al terminar cada impresión
- Síntoma (230 real): al terminar, un pitido (la melodía: sin SPEAKER el zumbador solo prende y apaga, las 4 notas suenan como un pitido) y enseguida la placa se reinicia (se oye el pitido del arranque).
- Causa probable: al terminar, `print_job_timer.stop()` guarda las estadísticas (PRINTCOUNTER, `PRINTCOUNTER_SAVE_INTERVAL 0`) en la EEPROM emulada en flash. En el STM32F4 eso borra un sector de 128 KB con las interrupciones apagadas (1-2 s, `HAL/STM32/eeprom/eeprom_flash.cpp`). El watchdog (4 s) se refresca cuando Temperature::task lee temperaturas; al terminar se arma y dibuja el resumen (íconos leídos de la SPI) y la suma se pasaba de 4 s.
- Arreglo: `hal.watchdog_refresh()` antes y después de `eeprom_buffer_flush()` (aplicar_colores.py, etapa 42) y `WATCHDOG_DURATION_8S` en Configuration_adv.h. El IWDG del F4 llega hasta ~32 s, 8 s entra.
- Compilado local (230, V1.3): 433.408 bytes (88 %). Sin probar en la máquina todavía: si sigue, pedir si M500 (Guardar) también la reinicia y probar con melodías apagadas.
