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
  - `TOOLCHANGE_FILAMENT_SWAP` (40 mm, M217)
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

## Estado / pendiente
- PlatformIO no está disponible en el entorno de Claude. Igual se compila y enlaza todo con `pruebas/compilacion-manual/` (ver etapa 6). El firmware oficial lo compila GitHub Actions.
- Los perfiles no se abrieron en los slicers reales; solo se validaron el formato y la coherencia con el firmware.
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
