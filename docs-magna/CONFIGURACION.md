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
| Sensor de filamento | 2 sensores, LOW = sin filamento | Bin + Manual | MT_DET1 (PA4) y MT_DET2 (PE6) |
| Drivers | X/Y TMC2209 standalone; Z/E A4988 | Criterio | Ver nota abajo |
| Cama / altura | 230 × 230 × 250 | Manual | Ver nota abajo |
| ADVANCE_K | { 0.0, 0.0 } | Criterio | Calibrar por extrusor (M900) |
| BED_MAXTEMP | 120 | Criterio | |

## Notas importantes

**Tamaño de cama.** El firmware de charlieburgos estaba compilado con un área de 500 × 500 (la malla UBL iba de 1 a 499 mm), o sea, prácticamente sin límites por software. Acá se usa el tamaño real del manual (230 × 230 × 250) para que los límites protejan la máquina. Si tu Magna tiene recorrido útil algo mayor y querés aprovecharlo, cambiá `X_BED_SIZE`, `Y_BED_SIZE` y `Z_MAX_POS`.

**Drivers.** Hellbot cambió de drivers según la tanda (las primeras traían TMC2209 solo en X/Y; las más nuevas en todos los ejes). El tipo de driver acá solo define los tiempos de pulso: `A4988` en Z/E funciona igual con TMC2209 en modo standalone. Las **direcciones** se tomaron del firmware que ya te funciona, así que deberían coincidir con tu cableado.

**Nivelación.** El bin original tenía UBL activado sin sensor (no se usa en la práctica). Acá se deja la nivelación manual de la pantalla MKS (5 puntos), como dice el manual. Si después ponés un BLTouch, hay que activar `BLTOUCH` y un sistema de nivelación.

## Mejoras agregadas en la versión 2

| Mejora | Opción | Ajuste en la máquina |
|---|---|---|
| Cambio de filamento automático (2 en 1) | `TOOLCHANGE_FILAMENT_SWAP`, 40 mm | `M217 S..` |
| Input Shaping X/Y | `INPUT_SHAPING_X/Y`, 40 Hz | `M593 X F.. / Y F..` |
| Temperatura predictiva | `MPCTEMP` (`PIDTEMP` desactivado) | `M306 T` |
| Apagado por inactividad | `HOTEND_IDLE_TIMEOUT`, 10 min, ≥180 °C | — |
| Cancelar objetos | `CANCEL_OBJECTS` | `M486` desde el slicer |
| Tiempo restante del slicer | `SET_PROGRESS_MANUALLY` | `M73` desde el slicer |
| Distancia del sensor de filamento | `FILAMENT_RUNOUT_DISTANCE_MM 15` | `M412 D..` |

Cómo calibrarlas: `CALIBRACION.md`.

**Linear Advance.** Queda activado con K = 0 (sin efecto) hasta que lo calibres: `M900 T0 K0.xx`, `M900 T1 K0.xx`, `M500`.
