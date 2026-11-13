# Marlin 2.1.3-beta3 para Hellbot Magna 2 230

Firmware Marlin configurado para la **Hellbot Magna 2 230** con placa **MKS Robin Nano V1.3 (STM32F407)** y pantalla táctil **MKS TFT35 v1** (interfaz MKS/LVGL, la misma que ya usás).

Base: Marlin oficial **2.1.3-b3**, 

### Qué hay en el repo
| Archivo | Para qué |
|---|---|
| `MARLIN_VERSION` | Versión de Marlin que se baja (`2.1.3-b3`). Para cambiar de versión, editás este archivo. |
| `Marlin/Configuration.h`, `Marlin/Configuration_adv.h`, `platformio.ini` | La configuración de la Magna (líneas marcadas `// Magna2-230`). |
| `docs-magna/` | Configuración, calibración, flasheo y pruebas en la impresora. |
| `perfiles-slicer/` | Cura, PrusaSlicer y OrcaSlicer. |
| `pruebas/` | Chequeos automáticos y `armar-local.sh` para compilar en tu PC. |
| `github-workflows/` | Copia del workflow. |

Para compilar en tu PC: `bash pruebas/armar-local.sh`, después `cd build` y `pio run -e mks_robin_nano_v1_3_f4`.

## Cómo flashear

Ver `docs-magna/COMO-FLASHEAR.md`.

## Pruebas

Las pruebas se corren sobre el proyecto completo (dentro de `build/`, después de `armar-local.sh`). GitHub Actions las corre solo antes de compilar.

- `pruebas/compilacion-manual/`: compila y enlaza el firmware entero sin PlatformIO, para diagnosticar errores (ver su README).
- `python3 pruebas/preflight.py` → repite los chequeos que PlatformIO hace antes de compilar (placa/entorno, script del sensor de filamento).
- `bash pruebas/sanity-check.sh` → corre los SanityCheck de Marlin sobre la configuración (sin PlatformIO).
- `bash pruebas/verificar-valores.sh` → confirma que los valores de la Magna siguen en su lugar.
- `python3 pruebas/verificar-perfiles.py` → valida los perfiles de slicer contra el firmware.
- Después de flashear: lista de pruebas en la impresora en `docs-magna/PRUEBAS-EN-IMPRESORA.md`.

## Qué tiene habilitado

Doble extrusor con hotend 2 en 1 (`SINGLENOZZLE`) y **cambio de filamento automático entre T0/T1**, 2 sensores de filamento (con distancia), pausa / cambio de filamento, **Input Shaping**, **MPC** (temperatura predictiva), Linear Advance, S-Curve, Jerk clásico, XY Frequency Limit, Adaptive Step Smoothing, **apagado por inactividad**, **cancelar objetos (M486)**, **tiempo restante del slicer (M73)**, recuperación por corte de luz, babystepping, contador de impresiones, EEPROM, WiFi MKS.

Calibración de las mejoras: `docs-magna/CALIBRACION.md`.

## Tema visual

Íconos y pantalla de arranque propios, en negro, rojo y blanco. Están en `assets-tema/`; ahí también hay imágenes de muestra en `preview/`. La compilación los pone en la carpeta `assets` del paquete para la SD y cambia los colores de los menús de la pantalla.

## Perfiles de slicer

Cura, PrusaSlicer y OrcaSlicer en `perfiles-slicer/` (instrucciones en su README).

Todas las líneas tocadas en `Marlin/Configuration.h` y `Marlin/Configuration_adv.h` tienen el comentario `// Magna2-230`. El diff completo contra Marlin oficial está en `docs-magna/cambios-config.diff`.
