# Calibración de las mejoras (hacer una sola vez)

Hacelas en este orden. Al final de cada una, guardá con `M500`.

## 1. Temperatura del hotend (MPC)
Este firmware usa MPC en vez de PID para el hotend.
1. Con la máquina fría, sin filamento colgando de la boquilla: `M306 T`.
2. La máquina hace home, calienta, deja enfriar y mide. Tarda unos minutos.
3. `M500`.

Si tu cartucho calefactor es de 50 W (y no de 40 W), cargalo antes: `M306 P50`.

## 2. Temperatura de la cama (PID)
`M303 E-1 S60 C8 U1` y después `M500`.

## 3. Largo del cambio de filamento (hotend 2 en 1)
Cuando cambia de T0 a T1, el firmware retira el filamento que sale una cierta cantidad de milímetros (40 de fábrica) y después carga el otro.
1. Medí cuánto hay desde la punta de la boquilla hasta la unión en "Y" del hotend 2 en 1, y sumale unos 10 mm.
2. Cargalo: `M217 S<mm>`. Por ejemplo, `M217 S45`.
3. Opcional:
   - `M217 R<mm/min>`: velocidad de retiro (por ejemplo, R2400).
   - `M217 U<mm/min>`: velocidad de carga (por ejemplo, U1200).
   - `M217 B<mm>`: extra al cargar si queda un hueco.
4. Probalo con la boquilla caliente: `T1`, después `T0`, y mirá que el filamento salga y entre bien.
5. `M500`.

Para desactivarlo: `M217 S0`.

## 4. Linear Advance (K)
Usá la calculadora de patrones de K de Marlin, o el `kfactor.gcode` de charlieburgos, con PLA. Después cargás el valor de cada extrusor:
- `M900 T0 K0.xx`
- `M900 T1 K0.xx`
- `M500`

En un bowden, los valores típicos van de 0.3 a 1.0.

## 5. Input Shaping
1. Imprimí una "ringing tower" (torre de resonancia) en modo jarrón, con aceleración alta (3000) y velocidad de unos 100 mm/s. Mientras imprime, el firmware tiene que ir cambiando la frecuencia. Para eso, en el slicer agregá por altura (cambio de capa) `M593 F<valor>`, empezando en 15 Hz y sumando 2,5 Hz cada 5 mm.
2. Al terminar, mirá en qué altura desaparecen las ondas en la cara X y en la cara Y.
3. Cargá cada frecuencia: `M593 X F<hz>` y `M593 Y F<hz>`.
4. `M500`.

Para desactivarlo: `M593 F0`.

En una Magna, la frecuencia de X suele andar entre 40 y 60 Hz y la de Y entre 25 y 40 Hz, porque la cama pesa más. Hasta que lo calibres, queda en 40 Hz en los dos ejes, que suaviza un poco sin hacer daño.

## 6. Ya están activos (sin calibrar)
- **Apagado por inactividad:** si el hotend está a 180 °C o más y pasan 10 minutos sin extruir, apaga el hotend y la cama.
- **Cancelar objetos:** `M486`. PrusaSlicer y OrcaSlicer ya lo emiten.
- **Tiempo restante:** `M73`, mandado desde el slicer.
- **Sensor de filamento:** pausa 15 mm después de detectar la falta de filamento. Se cambia con `M412 D<mm>`.
