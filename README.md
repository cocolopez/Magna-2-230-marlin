# Marlin 2.1.3 para Hellbot Magna 2 230

Firmware **Marlin 2.1.3-beta3** configurado para la impresora 3D **Hellbot Magna 2 230**, con placa **MKS Robin Nano V1.3** y pantalla táctil **MKS TFT35**. Incluye un tema visual propio para la pantalla, perfiles para Cura, PrusaSlicer y OrcaSlicer, y compilación automática en GitHub Actions.

<p align="center">
  <img src="docs-magna/capturas/arranque.png" width="48%" alt="Pantalla de arranque">
  <img src="docs-magna/capturas/principal.png" width="48%" alt="Pantalla principal">
</p>

---

## Contenido

- [Qué trae](#qué-trae)
- [Hardware compatible](#hardware-compatible)
- [Firmware](#firmware)
- [Tema de la pantalla](#tema-de-la-pantalla)
- [Perfiles de slicer](#perfiles-de-slicer)
- [Firmware del WiFi](#firmware-del-wifi)
- [Cómo compilar](#cómo-compilar)
- [Cómo instalar en la impresora](#cómo-instalar-en-la-impresora)
- [Calibración después de instalar](#calibración-después-de-instalar)
- [Pruebas automáticas](#pruebas-automáticas)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Créditos y licencia](#créditos-y-licencia)

---

## Qué trae

| | |
|---|---|
| **Firmware** | Marlin oficial 2.1.3-b3 con la configuración de la Magna 2 230 |
| **Pantalla** | Interfaz MKS (LVGL) táctil, en español, con tema propio negro, rojo y blanco |
| **Mejoras** | Linear Advance, Input Shaping, control de temperatura MPC, cambio automático de filamento para el hotend 2 en 1 y más (ver abajo) |
| **Slicers** | Perfiles para Cura 5, PrusaSlicer 2.6+ y OrcaSlicer 2.x |
| **WiFi** | Firmware oficial del módulo MKS Robin WiFi (opcional) |
| **Compilación** | Automática en GitHub Actions: subís `mm2.zip` y te devuelve todo listo para la SD |

## Hardware compatible

| Componente | Modelo |
|---|---|
| Impresora | Hellbot Magna 2 230 (230 × 230 × 250 mm) |
| Placa | MKS Robin Nano **V1.3** (STM32F407VET6, 512 KB) |
| Pantalla | MKS TFT35 táctil (480 × 320) |
| Extrusión | Doble extrusor Dual Drive con hotend **2 en 1** (una boquilla) |
| Drivers | TMC2209 (X/Y) en modo standalone |
| WiFi | MKS Robin WiFi (ESP8266) |

> ⚠️ Este firmware es **solo para la Robin Nano V1.3**. La V1.2 (STM32F103) y la V3 usan otros firmwares.

## Firmware

**Base:** Marlin oficial **2.1.3-b3**, idéntico al release de MarlinFirmware. El repositorio guarda solo los archivos propios de la Magna. La versión de Marlin está en `MARLIN_VERSION` y GitHub Actions la descarga al compilar.

Los valores mecánicos (pasos, direcciones de motores, finales de carrera, termistores, aceleraciones y PID de la cama) se tomaron de un firmware 2.1.2.1 que ya funcionaba en esta máquina. El detalle de cada valor y de dónde sale está en [`docs-magna/CONFIGURACION.md`](docs-magna/CONFIGURACION.md).

### Configuración principal

| Parámetro | Valor |
|---|---|
| Placa (`MOTHERBOARD`) | `BOARD_MKS_ROBIN_NANO_V1_3_F4` |
| Entorno de compilación | `mks_robin_nano_v1_3_f4` |
| Área de impresión | 230 × 230 × 250 mm |
| Pasos/mm X · Y · Z · E0 · E1 | 80 · 80 · 400 · 425 · 423 |
| Velocidad máxima | 300 · 300 · 5 · 25 · 25 mm/s |
| Aceleración máxima | 2000 · 2000 · 100 · 8000 · 8000 mm/s² |
| Aceleración impresión / viaje | 2000 / 2000 mm/s² |
| Jerk X · Y · Z · E | 10 · 10 · 0.3 · 5 |
| Termistores hotend / cama | Tipo 1 (100k NTC) |
| Temperatura máxima hotend / cama | 275 °C / 120 °C |
| Extrusores | 2, con boquilla única (`SINGLENOZZLE`) |
| Sensores de filamento | 2 (uno por extrusor) |
| Puerto serie | UART3, 115200 baudios |

### Funciones activadas

| Función | Para qué sirve |
|---|---|
| **Cambio de filamento automático** (`TOOLCHANGE_FILAMENT_SWAP`) | En el hotend 2 en 1, al pasar de T0 a T1 retira un filamento y carga el otro. Se ajusta con `M217` |
| **Input Shaping** X/Y | Reduce el *ringing* y permite imprimir más rápido. Se ajusta con `M593` |
| **MPC** (control predictivo de temperatura) | Temperatura del hotend más estable que con PID. Se calibra con `M306 T` |
| **Linear Advance** | Compensa la presión en la boquilla: esquinas más limpias. `M900` por extrusor |
| **S-Curve**, jerk clásico, límite de frecuencia XY, suavizado adaptativo de pasos | Movimiento más suave y menos vibración |
| **Sensores de filamento** (2) | Pausa si se acaba el filamento, 15 mm después de detectarlo (`M412`) |
| **Pausa y cambio de filamento** (`M600`) | Aparta el cabezal y espera el cambio, con "purgar más / continuar" en la pantalla |
| **Recuperación ante cortes de luz** | Retoma la impresión desde la SD |
| **Apagado por inactividad** | Si el hotend está caliente y quieto 10 min, apaga los calentadores |
| **Cancelar objetos** (`M486`) | Cancela una pieza que falló sin parar las demás |
| **Tiempo restante del slicer** (`M73`) | La pantalla muestra el tiempo calculado por el slicer |
| **Babystepping** | Ajusta Z en vivo durante la primera capa |
| **Contador de impresiones**, **EEPROM** | Estadísticas y configuración guardada con `M500` |
| **WiFi MKS** | Envío de archivos y control por red |

## Tema de la pantalla

Tema propio, minimalista: fondo oscuro con degradé, íconos de trazo blanco con detalles en rojo, y una pantalla de arranque con una pieza impresa en capas. Todos los íconos y la pantalla de arranque están generados por código en [`assets-tema/`](assets-tema/), sin imágenes de terceros.

<p align="center">
  <img src="docs-magna/capturas/ajustes.png" width="48%" alt="Menú Ajustes">
  <img src="docs-magna/capturas/imprimiendo.png" width="48%" alt="Pantalla de impresión">
</p>
<p align="center">
  <img src="docs-magna/capturas/configuracion.png" width="48%" alt="Menú Configuración">
</p>

<p align="center">
  <img src="docs-magna/capturas/iconos.png" width="96%" alt="Íconos del tema">
</p>

- **138 archivos:** mismo formato y tamaño que los originales de Makerbase, así que reemplazan a los de fábrica sin cambiar el firmware.
- **Íconos transparentes:** dejan ver el fondo de la pantalla.
- **Fondo y colores:** el degradé, los colores de los menús y la decoración de la pantalla principal los aplica [`assets-tema/aplicar_colores.py`](assets-tema/aplicar_colores.py) al compilar.
- **Para volver a los íconos de fábrica:** copiá a la SD la carpeta `assets` original de Makerbase.

> Las capturas son una simulación generada a partir de los mismos archivos que se cargan en la pantalla ([`generar_capturas.py`](assets-tema/generar_capturas.py)).

## Perfiles de slicer

En [`perfiles-slicer/`](perfiles-slicer/), ajustados a esta máquina y a este firmware:

| Slicer | Archivos | Cómo se importa |
|---|---|---|
| **Cura 5.x** | `cura/definitions/` y `cura/extruders/` | Copiarlos a la carpeta de configuración de Cura (Ayuda → Mostrar carpeta de configuración) |
| **PrusaSlicer 2.6+** | `prusaslicer/Magna2-230_PrusaSlicer_bundle.ini` | Archivo → Importar → Importar paquete de configuración |
| **OrcaSlicer 2.x** | `orcaslicer/machine`, `process`, `filament` | Archivo → Importar → Importar configuraciones |

- **Calidades:** 0.12 Fina · 0.20 Normal · 0.28 Borrador.
- **Filamentos:** PLA · PETG · ABS.
- **G-code de inicio:** doble línea de purga. Al terminar, el cabezal se aparta y presenta la pieza.
- **Cambio de extrusor:** lo hace el firmware, así que la retracción de cambio del slicer va en 0.

Todos se generan desde un único script ([`generar_perfiles.py`](perfiles-slicer/generar_perfiles.py)), así quedan coherentes entre sí. Más detalles en [`perfiles-slicer/README.md`](perfiles-slicer/README.md).

## Firmware del WiFi

[`wifi/MksWifi.bin`](wifi/) es el **firmware oficial de Makerbase CS1.0.4_200227** para el módulo MKS Robin WiFi (ESP8266). Es opcional: solo hace falta para actualizar o reparar el WiFi. Ver [`wifi/README.md`](wifi/README.md).

## Cómo compilar

### Con GitHub Actions (recomendado)

1. **Solo la primera vez:** crear `.github/workflows/compilar-mm2.yml` con el contenido de [`github-workflows/compilar-mm2.yml`](github-workflows/compilar-mm2.yml).
2. Subir **`mm2.zip`** a la raíz del repo (Add file → Upload files).
3. El workflow hace todo solo:
   1. descomprime el zip en el repo y guarda los archivos;
   2. descarga Marlin oficial (la versión de `MARLIN_VERSION`);
   3. le aplica la configuración y el tema;
   4. corre las pruebas y compila.
4. En **Actions → Compilar Magna 2 230 (mm2.zip)** se descarga el artefacto **`Magna2-230-firmware`**:

```
Magna2-230-firmware/
├── Robin_nano35.bin      ← firmware
├── assets/               ← íconos, logo y fuente de la pantalla
├── opcional-wifi/        ← firmware del WiFi (solo si se quiere actualizar)
└── COMO-FLASHEAR.md
```

### En una PC

```bash
bash pruebas/armar-local.sh                      # baja Marlin y aplica la configuración en build/
python3 assets-tema/aplicar_colores.py build     # aplica el tema
cd build && pio run -e mks_robin_nano_v1_3_f4    # compila con PlatformIO
```

El firmware queda en `build/.pio/build/mks_robin_nano_v1_3_f4/Robin_nano35.bin`. Para usar los íconos del tema, copiá `assets-tema/assets/*.bin` dentro de la carpeta `assets` generada.

## Cómo instalar en la impresora

1. Guardar los valores actuales: conectar por USB y mandar `M503`.
2. Formatear una microSD en **FAT32** y copiar en la raíz `Robin_nano35.bin` y la carpeta `assets`. Opcional: `MksWifi.bin`.
3. Con la impresora apagada, insertar la SD y encender. **No apagar mientras actualiza**: primero el firmware, después los íconos y después el WiFi.
4. Al terminar, los archivos de la SD quedan renombrados: `ROBIN_NANO35.CUR`, `_assets` y `MKSWIFI.CUR`.
5. Cargar la configuración nueva en la EEPROM: `M502` y después `M500`.

Paso a paso completo: [`docs-magna/COMO-FLASHEAR.md`](docs-magna/COMO-FLASHEAR.md). Para volver al firmware anterior, se repite el proceso con el `.bin` viejo.

## Calibración después de instalar

En orden ([`docs-magna/CALIBRACION.md`](docs-magna/CALIBRACION.md)):

| # | Qué | Comando |
|---|---|---|
| 1 | Temperatura del hotend (MPC) | `M306 T` → `M500` |
| 2 | PID de la cama | `M303 E-1 S60 C8 U1` → `M500` |
| 3 | Largo del cambio de filamento 2 en 1 | `M217 S<mm>` → `M500` |
| 4 | Linear Advance por extrusor | `M900 T0 K..` / `M900 T1 K..` → `M500` |
| 5 | Input Shaping | `M593 X F..` / `M593 Y F..` → `M500` |

Antes de imprimir, hacer las pruebas básicas de [`docs-magna/PRUEBAS-EN-IMPRESORA.md`](docs-magna/PRUEBAS-EN-IMPRESORA.md): temperaturas, finales de carrera, sentido de los ejes y extrusores.

## Pruebas automáticas

GitHub Actions las corre antes de cada compilación:

| Prueba | Qué verifica |
|---|---|
| `pruebas/preflight.py` | Los chequeos previos de PlatformIO: placa/entorno, script del sensor de filamento, ubicación de la configuración |
| `pruebas/sanity-check.sh` | Los *SanityCheck* de Marlin sobre la configuración |
| `pruebas/verificar-valores.sh` | 31 valores clave de la Magna (pasos, direcciones, funciones activadas…) |
| `pruebas/verificar-perfiles.py` | Que los perfiles de slicer estén bien formados y coincidan con el firmware |
| `pruebas/compilacion-manual/` | Compilación y enlazado completos sin PlatformIO, para diagnosticar errores |

## Estructura del repositorio

```
├── MARLIN_VERSION              versión de Marlin que se descarga (2.1.3-b3)
├── platformio.ini              entorno por defecto: mks_robin_nano_v1_3_f4
├── Marlin/
│   ├── Configuration.h         configuración de la Magna (líneas marcadas "// Magna2-230")
│   └── Configuration_adv.h
├── assets-tema/                tema de la pantalla (generador, íconos, colores, capturas)
├── perfiles-slicer/            Cura, PrusaSlicer, OrcaSlicer
├── wifi/                       firmware oficial del módulo WiFi
├── docs-magna/                 configuración, calibración, flasheo, pruebas y capturas
├── pruebas/                    pruebas automáticas y compilación manual
└── github-workflows/           copia del workflow de GitHub Actions
```

## Créditos y licencia

- **[Marlin Firmware](https://github.com/MarlinFirmware/Marlin):** licencia GPL-3.0. Este repositorio solo agrega configuración y archivos propios.
- **Interfaz de pantalla:** MKS UI (LVGL) incluida en Marlin. La fuente `FontUNIGBK.bin` es de [Makerbase](https://github.com/makerbase-mks).
- **Firmware del WiFi:** oficial de [Makerbase MKS-WIFI](https://github.com/makerbase-mks/MKS-WIFI).
- **Valores de la máquina:** tomados del firmware 2.1.2.1 de la comunidad para la Magna 2 de [charlieburgos](https://github.com/charlieburgos/Hellbot-Magna-2).
- **Tema visual, perfiles y scripts:** propios de este repositorio.

> Usalo bajo tu responsabilidad. Antes de la primera impresión, verificá las temperaturas, los finales de carrera y el sentido de los motores.
