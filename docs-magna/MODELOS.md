# Otros modelos: Magna 2 300, 400, 400D, 500 y 500D

> **Sin probar.** Solo tengo la Magna 2 230. Los firmware de los otros modelos están armados con los
> valores de los firmware oficiales de Hellbot, pero nadie los instaló todavía en una máquina real.
> Por eso sus paquetes dicen **UNTESTED** y traen `LEEME-SIN-PROBAR.txt`.

## De dónde salen los valores

Los firmware oficiales de Hellbot para estos modelos ("Marlin-2.0.3-Magna-2-XXX-Placa v1.3") traen
todos el mismo `Robin_nano35.bin`. Lo que cambia es `robin_nano35_cfg.txt`, un archivo de texto que la
impresora lee al instalar. Los paquetes de la 400D y la 500D son idénticos a los de la 400 y la 500.

| | 230 (probada) | 300 | 400 / 400D | 500 / 500D |
|---|---|---|---|---|
| Cama (X × Y × Z) | 230 × 230 × 250 | 300 × 300 × 400 | 400 × 400 × 400 | 500 × 500 × 500 |
| Nivelación | manual (o BLTouch aparte) | manual, 5 puntos | BLTouch | BLTouch |
| Sonda BLTouch | — | — | X −30, Y 0 | X −30, Y 0 |
| Pasos X / Y / Z / E | 80 / 80 / 400 / 425 | 80 / 80 / 400,5 / 400 | 80 / 80 / 400,5 / 415 | 80 / 80 / 400,5 / 415 |
| Motor Z invertido | sí | no | no | no |
| Velocidad máx. XY / Z | 300 / 5 | 200 / 4 | 100 / 5 | 100 / 5 |
| Aceleración máx. XY | 2000 | 800 | 200 | 200 |
| Temperatura máx. cama | 120 | 110 | 95 | 95 |
| Extrusor | bowden | bowden | bowden / directo (D) | bowden / directo (D) |

Todas: doble extrusor con hotend 2 en 1, placa MKS Robin Nano V1.3, pantalla TFT35 y el mismo módulo
WiFi (MagnAir es el mismo para todas).

## Lo que no sale del oficial

`variantes/modelo.py` aplica todo esto sobre la configuración de la 230:

- **Entrada Z máximo apagada.** El oficial de la 300 la usa y no se sabe qué tiene conectado; el tope
  de Z lo controla el firmware con la medida. Así no frena el eje por una entrada vacía.
- **Cama sin PID**, como el oficial. Las de 400 y 500 parecen de 220 V con relé (máximo 95 °C).
- **Protección de temperatura de la cama más larga** (cuánto puede tardar en subir antes de dar
  "Heating failed"): 120 s en la 300, 240 s en la 400 y 300 s en la 500 (en la 230, 60 s).
- **Precalentado ABS de la cama**: lo máximo que deja cada cama (100 °C en la 300, 85 °C en 400/500).
- **BLTouch (400 y 500)**: el mismo armado que la versión BLTouch de la 230, con el offset X/Y del
  oficial. La altura (Z) arranca en 0 y se calibra con el asistente (ver BLTOUCH.md). Malla de 7×7
  (el oficial usa 8×8: 64 toques cada vez).
- **Extrusor**: se mantienen las velocidades del extrusor de la 230 (25 mm/s); los pasos son los del
  oficial.
- **Puntos de nivelación manual**: la pantalla los calcula sola a 30 mm de cada borde. En los
  oficiales de 400 y 500 eran los de la 230 sin cambiar (todos en un rincón).
- **D (extrusor directo)**: al cambiar filamento descarga 50 mm en lugar de 100.

## Perfiles de slicer

Hay perfiles para todos los modelos (`perfiles-slicer/`), con "(sin probar)" en el nombre de los
que no son la 230. Diferencias:

- Medidas de la cama y límites de velocidad y aceleración de cada firmware.
- **D (directo)**: retracción de 1 mm (bowden: 5 mm). En el cambio entre filamentos (hotend 2 en 1),
  cada filamento sube **60 mm** para dejar libre la unión en Y. Ese número **no está medido**: con 100
  (lo de la bowden) el filamento saldría de los engranajes del extrusor, que en la D están arriba del
  hotend. Si tenés una D, medí la distancia de la punta del pico a la unión y a los engranajes y
  cambiá `estacionar` en `generar_perfiles.py`.

## Para el que la pruebe

Ver `LEEME-SIN-PROBAR.txt` (va adentro de cada paquete): guardar `M503`, probar el sentido de cada
eje antes del home, home de a un eje, calentar sin imprimir y calibrar la sonda. Cualquier
diferencia, avisame: andreslondero@gmail.com.
