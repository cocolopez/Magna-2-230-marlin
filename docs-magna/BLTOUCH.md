# Versión con BLTouch

GitHub arma dos firmwares cada vez que compila:

| Carpeta / zip | Para qué impresora |
|---|---|
| `Magna2-230-firmware` | La normal: fin de carrera de Z mecánico y nivelación a mano de 5 puntos |
| `Magna2-230-firmware-BLTouch` | Con sensor **BLTouch**: la impresora mide la cama sola y corrige las diferencias mientras imprime |

Las dos traen todo lo demás igual: tema, botones de "Más", letra grande, perfiles, etc. La única diferencia la aplica `variantes/bltouch.py`.

> No uses la versión BLTouch sin el sensor instalado: Z no tendría con qué hacer home.

## 1. Conexión (con la impresora apagada y desenchufada)

En la placa MKS Robin Nano V1.3:
- **Cable de 3 hilos** del BLTouch (marrón, rojo y naranja o amarillo) → conector marcado **BLTouch**. El marrón va a GND.
- **Cable de 2 hilos** (negro y blanco) → conector del fin de carrera **Z-**. Antes desenchufá de ahí el fin de carrera mecánico de Z.

El soporte del BLTouch tiene que dejar la punta retraída **entre 2,3 y 4,3 mm más arriba que la boquilla**.

## 2. Instalar el firmware
1. Usá los archivos de `Magna2-230-firmware-BLTouch`: `Robin_nano35.bin` y la carpeta `assets`.
2. Encendé la impresora con la SD puesta y esperá a que termine.
3. Al prender, el BLTouch tiene que bajar y subir la punta dos veces y quedar con la luz fija.
4. Mandá **Ajustes → Más → Gcode** `M502` y después `M500`, para cargar los valores nuevos.

## 3. Decirle dónde está el sensor (offset X/Y)
El firmware viene con offset 0 y un margen de 45 mm. Así, aunque todavía no lo hayas configurado, la sonda mide siempre dentro de la cama. Igual conviene cargar el valor real, porque mejora la malla:
1. Con una regla, medí cuánto está la punta del BLTouch a la **izquierda o derecha** de la boquilla (X) y **adelante o atrás** (Y).
   - X: a la izquierda es negativo (por ejemplo, -40); a la derecha, positivo.
   - Y: adelante (hacia vos) es negativo; atrás, positivo.
2. Cargalo en **Config → Config → Machine settings → Leveling settings → Nozzle-to-probe offsets settings**, o con el comando `M851 X-40 Y-10` (con tus números).
3. `M500` para guardar.

## 4. Altura de la boquilla (offset Z) — lo más importante
Con offset Z = 0, la boquilla queda unos 2–3 mm en el aire. Es a propósito: así no choca contra la cama antes de calibrar.

**Con el asistente:**
1. Andá a **Config → Config → Machine settings → Leveling settings → Z Offset Wizard**.
2. La máquina hace home, mide con el BLTouch y pone la boquilla en el centro de la cama.
3. Poné un papel debajo y bajá con **Z-** (de a 0,1 y después 0,01) hasta que el papel roce al moverlo.
4. Tocá **Guardar**. Después mandá `M500`.

**Ajuste fino:** mientras imprime la primera capa, el **Babystep** corrige directamente el offset de la sonda. Cuando quede bien, mandá `M500`.

## 5. Nivelar (medir la cama)
1. Tocá **Ajustes → Autolevel** (el botón que antes decía "Leveling"). Hace home, mide 25 puntos (5×5) y guarda la malla solo.
2. Hacelo con la cama caliente (60 °C) para que mida como cuando imprime.
3. Repetilo cada tanto, o cuando cambies o muevas la chapa.

No hace falta cambiar nada en Cura, PrusaSlicer ni Orca: después del `G28` del inicio, el firmware activa solo la malla guardada.

## Si algo falla
- **Luz roja que parpadea:** la punta se trabó. Mandá `M280 P0 S160` (reset) y revisá que el soporte no esté demasiado bajo.
- **La boquilla choca al hacer home:** revisá que el cable de 2 hilos esté en Z- y que el soporte cumpla los 2,3–4,3 mm.
- **Imprime en el aire:** falta el offset Z (punto 4).
