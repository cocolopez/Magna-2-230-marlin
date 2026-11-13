# Pruebas después de flashear

Hacelas en orden, con la mano cerca del interruptor de corriente.

1. **Temperaturas en reposo:** hotend y cama deben marcar temperatura ambiente (≈ 20–30 °C). Si marca −14 °C o 0, el termistor no coincide: no calientes.
2. **Finales de carrera:** `M119` sin tocar nada → todo `open`. Apretá cada final con la mano y repetí `M119` → ese eje en `TRIGGERED`.
3. **Sensores de filamento:** `M119` con y sin filamento en cada extrusor; tiene que cambiar el estado.
4. **Dirección de ejes** (sin hacer home): mové X +10 desde la pantalla → el cabezal va hacia la derecha. Y +10 → la cama va hacia adelante (el cabezal "se aleja" hacia atrás de la pieza). Z +10 → sube. Si alguno va al revés, cambiá su `INVERT_x_DIR`.
5. **Home:** `G28` y verificá que cada eje vaya hacia su final y frene.
6. **Extrusores:** calentá a 200 °C, extruí 10 mm con E0 y con E1 (`T0` / `T1`): el filamento tiene que entrar, no salir.
7. **Temperatura:** `M306 T` (hotend, MPC) y `M303 E-1 S60 C8 U1` (cama), luego `M500`.
8. **Linear Advance:** calibrá K (por ejemplo con el gcode de `Calibraciones/Lineal Advance` de charlieburgos o la página de calibración de Marlin) y guardá con `M900 T0 K..`, `M900 T1 K..`, `M500`.
9. **Cambio de extrusor:** con el hotend caliente, `T1` y luego `T0`: el filamento tiene que salir y entrar sin trabarse (ajustar con `M217 S`).
10. **Resto de calibraciones:** ver `CALIBRACION.md` (Input Shaping, Linear Advance).
