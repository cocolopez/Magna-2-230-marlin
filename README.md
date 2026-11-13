# Marlin 2.1.3-beta3 para Hellbot Magna 2 230

Firmware Marlin configurado para la **Hellbot Magna 2 230** con placa **MKS Robin Nano V1.3 (STM32F407)** y pantalla táctil **MKS TFT35 v1** (interfaz MKS/LVGL, la misma que ya usás).

Base: Marlin oficial **2.1.3-b3**, idéntico al `Marlin-release-2.1.3-beta3` que subiste (verificado archivo por archivo). Este proyecto guarda **solo los archivos propios de la Magna**. El código de Marlin lo baja GitHub Actions de la versión que figura en `MARLIN_VERSION`, así `mm2.zip` pesa menos de 1 MB.
Referencia: el firmware "Marlin Charlieburgos V2.1.2.1" (`Robin_nano35.bin` del otro zip). Como ese zip traía solo el binario y no el código fuente, los valores se **extrajeron del binario** (ver `docs-magna/CONFIGURACION.md`).

## Cómo compilar (GitHub Actions con mm2.zip)

1. **Solo la primera vez:** en el repo, creá el archivo `.github/workflows/compilar-mm2.yml` con el contenido de `github-workflows/compilar-mm2.yml` (Add file → Create new file, pegás y guardás).
2. Subí `mm2.zip` a la raíz del repo (Add file → Upload files).
3. El workflow:
   - descomprime el zip en el repo, guarda los archivos y borra `mm2.zip`;
   - baja Marlin y le copia encima la configuración de la Magna;
   - corre las pruebas y compila.
4. En **Actions → Compilar Magna 2 230 (mm2.zip)** descargá el artefacto **Magna2-230-firmware**, que trae `Robin_nano35.bin` y la carpeta `assets`.

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

- `bash pruebas/sanity-check.sh` → corre los SanityCheck de Marlin sobre la configuración (sin PlatformIO).
- `bash pruebas/verificar-valores.sh` → confirma que los valores de la Magna siguen en su lugar.
- `python3 pruebas/verificar-perfiles.py` → valida los perfiles de slicer contra el firmware.
- Después de flashear: lista de pruebas en la impresora en `docs-magna/PRUEBAS-EN-IMPRESORA.md`.

## Qué tiene habilitado

Doble extrusor con hotend 2 en 1 (`SINGLENOZZLE`) y **cambio de filamento automático entre T0/T1**, 2 sensores de filamento (con distancia), pausa / cambio de filamento, **Input Shaping**, **MPC** (temperatura predictiva), Linear Advance, S-Curve, Jerk clásico, XY Frequency Limit, Adaptive Step Smoothing, **apagado por inactividad**, **cancelar objetos (M486)**, **tiempo restante del slicer (M73)**, recuperación por corte de luz, babystepping, contador de impresiones, EEPROM, WiFi MKS.

Calibración de las mejoras: `docs-magna/CALIBRACION.md`.

## Perfiles de slicer

Cura, PrusaSlicer y OrcaSlicer en `perfiles-slicer/` (instrucciones en su README).

Todas las líneas tocadas en `Marlin/Configuration.h` y `Marlin/Configuration_adv.h` tienen el comentario `// Magna2-230`. El diff completo contra Marlin oficial está en `docs-magna/cambios-config.diff`.
