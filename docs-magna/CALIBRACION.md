# Calibración de las mejoras (hacer una sola vez)

Hacelas en este orden. Al final de cada una, guardá con `M500`.

**Cómo se manda un comando (por ejemplo `M500`):** en la pantalla tocá **Ajustes → Más → Gcode**, escribilo con el teclado y tocá OK. `M500` guarda los ajustes en la memoria de la placa para que no se borren al apagar.

**Botones propios en Ajustes → Más** (se ejecutan apenas se tocan, sin preguntar):

| Botón | Qué hace |
|---|---|
| Calib. hotend | `M306 T` + `M500`: calibra el MPC del hotend. Con la máquina **fría**. Tarda 5–10 min |
| Calib. cama | `M303 E-1 S60 C8 U1` + `M500`: calibra el PID de la cama a 60 °C |
| Estacionar 1 / 2 | Calienta a 210 °C y retira ese filamento 100 mm, arriba de la unión del 2 en 1 |
| Cargar 1 / 2 | Calienta a 210 °C, baja ese filamento 100 mm desde la posición de estacionado y purga 20 mm |

Se configuran en `Marlin/Configuration_adv.h` (`CUSTOM_MENU_MAIN`, `MAIN_MENU_ITEM_1..6`).

## 1. Temperatura del hotend (MPC)
Este firmware usa MPC en vez de PID para el hotend. **Lo más fácil:** botón **Calib. hotend** con la máquina fría. Si lo hacés con comandos:
1. Con la máquina fría, sin filamento colgando de la boquilla: `M306 T`.
2. La máquina hace home, calienta, deja enfriar y mide. Tarda unos minutos.
3. `M500`.

Si tu cartucho calefactor es de 50 W (y no de 40 W), cargalo antes: `M306 P50`.

## 2. Temperatura de la cama (PID)
Botón **Calib. cama**, o `M303 E-1 S60 C8 U1` y después `M500`.

## 3. Largo del cambio de filamento (hotend 2 en 1)
El cambio entre T0 y T1 lo hacen **los perfiles de slicer**, como el perfil de fábrica de Hellbot. Retiran el filamento 100 mm, por encima de la unión en "Y". Por eso el firmware trae `TOOLCHANGE_FS_LENGTH 0` y cada gcode de inicio manda `M217 S0`. Detalles en `perfiles-slicer/README.md`.

Si al cambiar de color el filamento nuevo no entra, o al cargar sale un chorro grande:
1. Ajustá `largo` en `CAMBIO`, dentro de `perfiles-slicer/generar_perfiles.py`. Probá 105–110 si no entra, o 90–95 si sale mucho.
2. Regenerá los perfiles con `python3 generar_perfiles.py` y volvé a instalarlos.

Para un cambio a mano desde la terminal, el firmware todavía puede hacerlo:
1. `M217 S100` (no lo guardes con M500).
2. `T1` / `T0`.

Hacelo siempre con el hotend caliente y con el otro filamento estacionado.

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
