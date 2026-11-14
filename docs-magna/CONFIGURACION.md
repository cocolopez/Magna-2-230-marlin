# Configuración y de dónde sale cada valor

El zip "Magna 2 230_2.1.2.1" no traía `Configuration.h`, solo el binario compilado (`Robin_nano35.bin`, "Marlin Charlieburgos V2.1.2.1", Robin Nano 1.3 + TFT35v1). Los valores se obtuvieron así:

- **Bin** = leído directamente del firmware original (desensamblado / tablas de constantes). Es lo más confiable: es lo que hoy funciona en la máquina.
- **Manual** = manual oficial Hellbot Magna 2 230.
- **Criterio** = elección propia segura; revisar si algo no anda.

| Opción | Valor | Origen | Nota |
|---|---|---|---|
| MOTHERBOARD | BOARD_MKS_ROBIN_NANO_V1_3_F4 | Bin | Variante MARLIN_F4x7Vx, offset 0x8000 |
| Pantalla | MKS_ROBIN_TFT35 + TFT_LVGL_UI + TOUCH_SCREEN | Bin | Misma interfaz MKS |
| SERIAL_PORT / BAUDRATE | 3 / 115200 | Criterio | Estándar MKS (USB por CH340) |
| EXTRUDERS + SINGLENOZZLE | 2, un solo hotend | Bin + Manual | El bin informa EXTRUDER_COUNT:2 y solo lee el termistor TH1 |
| TEMP_SENSOR_0 / BED | 1 / 1 | Bin | Única tabla de termistor en el bin: tipo 1 (100k NTC) |
| Pasos/mm X Y Z E0 E1 | 80, 80, 400, 425, 423 | Bin | `DISTINCT_E_FACTORS` activo |
| Vel. máx. | 300, 300, 5, 25, 25 | Bin | |
| Acel. máx. | 2000, 2000, 100, 8000, 8000 | Bin | |
| Acel. impresión / retracción / viaje | 2000 / 2000 / 2000 | Bin | |
| Jerk X Y Z E | 10, 10, 0.3, 5 | Bin | `CLASSIC_JERK` |
| Control hotend | MPC (40 W) | Criterio (v2) | Reemplaza al PID (32.05 / 2.06 / 124.34 del bin). Calibrar con `M306 T` |
| PID cama Kp Ki Kd | 45.69, 8.65, 160.81 | Bin | Ídem |
| INVERT_X_DIR | false | Bin | Leído de `Stepper::set_directions()` |
| INVERT_Y_DIR | true | Bin | |
| INVERT_Z_DIR | true | Bin | |
| INVERT_E0_DIR / E1 | true / true | Bin | |
| Finales X/Y/Z MIN | se activan en LOW | Bin | Leído del reporte M119; homing a mínimo |
| Sensor de filamento | 2 sensores, LOW = sin filamento, script `M600 T%c` | Bin + Manual | MT_DET1 (PA4) y MT_DET2 (PE6); `%c` = extrusor que se quedó sin filamento |
| Drivers | X/Y TMC2209 standalone; Z/E A4988 | Criterio | Ver nota abajo |
| Cama / altura | 230 × 230 × 250 | Manual | Ver nota abajo |
| ADVANCE_K | { 0.0, 0.0 } | Criterio | Calibrar por extrusor (M900) |
| BED_MAXTEMP | 120 | Criterio | |

## Notas importantes

**Tamaño de cama.** El firmware de charlieburgos estaba compilado con un área de 500 × 500 (la malla UBL iba de 1 a 499 mm), o sea, prácticamente sin límites por software. Acá se usa el tamaño real del manual (230 × 230 × 250) para que los límites protejan la máquina. Si tu Magna tiene recorrido útil algo mayor y querés aprovecharlo, cambiá `X_BED_SIZE`, `Y_BED_SIZE` y `Z_MAX_POS`.

**Drivers.** Hellbot cambió de drivers según la tanda (las primeras traían TMC2209 solo en X/Y; las más nuevas en todos los ejes). El tipo de driver acá solo define los tiempos de pulso: `A4988` en Z/E funciona igual con TMC2209 en modo standalone. Las **direcciones** se tomaron del firmware que ya te funciona, así que deberían coincidir con tu cableado.

**Nivelación.** El bin original tenía UBL activado sin sensor (no se usa en la práctica). Acá se deja la nivelación manual de la pantalla MKS (5 puntos), como dice el manual. Si después ponés un BLTouch, hay que activar `BLTOUCH` y un sistema de nivelación.

## Opciones necesarias para compilar con la UI MKS (Marlin 2.1.3-b3)

| Opción | Por qué |
|---|---|
| `EMERGENCY_PARSER` | La pausa (`ADVANCED_PAUSE_FEATURE`) lo exige con la UI MKS |
| `HOST_ACTION_COMMANDS` + `HOST_PROMPT_SUPPORT` | Habilitan "Purgar más / Continuar" (`M600_PURGE_MORE_RESUMABLE`), que usa la pantalla MKS |
| `PARK_HEAD_ON_PAUSE` | En pausa o cambio de filamento aparta el cabezal de la pieza (y la pantalla MKS lo necesita para compilar) |
| `PRINTCOUNTER_SAVE_INTERVAL 0` | Las estadísticas se guardan al terminar la impresión. Guardarlas a mitad de impresión en esta placa frena el movimiento un instante |
| `FILAMENT_RUNOUT_SCRIPT "M600 T%c"` | Con 2 sensores, Marlin pide saber qué extrusor se quedó sin filamento |

## Mejoras agregadas en la versión 2

| Mejora | Opción | Ajuste en la máquina |
|---|---|---|
| Cambio de filamento del 2 en 1 | `TOOLCHANGE_FILAMENT_SWAP` compilado, pero con largo 0: el cambio de 100 mm lo hacen los perfiles de slicer | `M217 S100` solo para cambios a mano |
| Input Shaping X/Y | `INPUT_SHAPING_X/Y`, 40 Hz | `M593 X F.. / Y F..` |
| Temperatura predictiva | `MPCTEMP` (`PIDTEMP` desactivado) | `M306 T` |
| Apagado por inactividad | `HOTEND_IDLE_TIMEOUT`, 10 min, ≥180 °C | — |
| Cancelar objetos | `CANCEL_OBJECTS` | `M486` desde el slicer |
| Tiempo restante del slicer | `SET_PROGRESS_MANUALLY` | `M73` desde el slicer |
| Distancia del sensor de filamento | `FILAMENT_RUNOUT_DISTANCE_MM 15` | `M412 D..` |

Cómo calibrarlas: `CALIBRACION.md`.

**Linear Advance.** Queda activado con K = 0 (sin efecto) hasta que lo calibres: `M900 T0 K0.xx`, `M900 T1 K0.xx`, `M500`.

## Botones propios (Ajustes → Más)
`CUSTOM_MENU_MAIN` en `Configuration_adv.h`, con `MAIN_MENU_ITEM_1..6`:
- Calib. hotend: `M306 T`, `M500`.
- Calib. cama: `M303 E-1 S60 C8 U1`, `M500`.
- Estacionar 1 / 2: 210 °C, `T0`/`T1`, retirar 100 mm.
- Cargar 1 / 2: 210 °C, `T0`/`T1`, bajar 100 mm y purgar 20 mm.

Los íconos son `bmp_custom1..6` del tema. En la pantalla MKS se ejecutan sin confirmación.

## Apagado automático de la pantalla
`MAGNA_PANTALLA_APAGADO_MIN 5` en `Configuration_adv.h` (opción propia de este repo; 0 = nunca).
- Lo implementa `aplicar_colores.py` en `tft_lvgl_configuration.cpp` (lectura del táctil) y en `lv_screen_create`.
- Apaga la luz de fondo de la pantalla (PD13, `TFT_BACKLIGHT_PIN`); la placa y la impresión siguen igual.
- El primer toque solo la prende: ese toque no llega a los botones.
- Cualquier pantalla nueva la prende, por ejemplo un aviso de filamento o de impresión terminada.

**Desde el WiFi (MagnAir):** `M256 B0` apaga la pantalla, `M256 B255` la prende y `M256` contesta cómo está. Apagada así, el primer toque la prende sin apretar nada.

**Estadísticas y protecciones (MagnAir):** al final de `M257` van `M257 extras PLR=… SF=… SFD=…` (corte de luz, sensor de filamento y su distancia; -1 = no compilado) y `M257 estadisticas N=… OK=… T=… L=… F=…` (impresiones, terminadas, segundos, la más larga, mm de filamento).

**Calibración y carpetas (MagnAir):** `M257` contesta por WiFi los valores de calibración en uso, una línea por grupo (`M257 mpc P=… C=…`, `M257 pasos X=…`, …) y `M257 fin`. La lista de archivos por WiFi entra a las carpetas (`M20 L /CARPETA`) y `M23 /CARPETA/ARCHIVO.GCO` imprime desde ahí.
