# Placa MKS Robin Nano V1.2 (mm12)

> **Sin probar.** Nadie probó estos firmware en una placa V1.2. Solo tengo una Magna 2 230 con placa V1.3.

Las Magna 2 vinieron con dos placas: la **V1.3** (STM32F407, 168 MHz, 192 KB de RAM) y la **V1.2**
(STM32F103, 72 MHz, **64 KB de RAM**). Para saber cuál tenés: el firmware oficial de Hellbot dice "Placa v1.2" o
"Placa v1.3" en el nombre del paquete, y en la placa está impreso "MKS Robin Nano V1.x".

El firmware de la V1.3 (repo mm2) no entra en la V1.2: con Marlin, la pantalla MKS y todo lo que le agregué a la
pantalla usa unos 76 KB de RAM. Marlin solo, con la configuración de la Magna y la pantalla, ya usa ~62 KB. Por eso
mm12 es una versión **recortada**, hecha con el mismo código.

## Qué tiene y qué no

| | V1.3 (mm2) | V1.2 (mm12) |
|---|---|---|
| Tema negro y rojo, íconos | sí | sí |
| Pantalla en castellano | sí | sí |
| Hora | grande en la principal, chica en el resto | chica en todas |
| Fecha e íconos de WiFi/Telegram en la principal | sí | no |
| Línea "capa · faltan · fin" al imprimir | sí | sí |
| Mensajes desde MagnAir y Telegram | sí | sí |
| Aviso de error grave por Telegram | sí | sí |
| Precalentado con las temperaturas de la app | sí | sí |
| Melodías | sí | sí |
| Animaciones (arranque, íconos, ventilador) | sí | no |
| Gráfico de temperaturas | sí | no |
| "Siempre encendida" mientras imprime | sí | no |
| Vista en vivo del recorrido | sí | no |
| Cancelar una pieza desde la pantalla | sí | no (por gcode, `M486`, sí) |
| Resumen al terminar | sí | no |
| Bloqueo de la pantalla | sí | no |
| Nivelación en vivo con mapa (BLTouch) | sí | no (nivela igual) |
| Input shaping (`M593`) | sí | no |
| Movimientos en la cola del planificador | 16 | 8 |
| Código QR de la "nube" de Makerbase | sí | no (el servicio ya no existe) |

Medido compilando acá (sin PlatformIO): la 230 queda con ~60,4 KB de RAM y la 500 (con BLTouch) con ~60,9 KB, sobre
64 KB. Lo que sobra es para la pila del procesador: es poco, por eso se sacó tanto.

## MagnAir

El módulo WiFi es el mismo, y MagnAir también. La pantalla le avisa que es una V1.2 ("MAGNA_PLACA:1.2", junto con
el modelo, en la respuesta a `M115`), y con eso:

- el módulo le pregunta el estado cada 5 segundos en lugar de cada 2 (para no cargarla mientras imprime);
- la app y la página no muestran las opciones que no existen en la V1.2 (animaciones, "siempre encendida",
  compensación de vibraciones).

## Cómo se arma

Es el mismo proyecto que mm2. `variantes/placa12.py` cambia la placa y saca lo que no entra, y
`assets-tema/liviano.py` deja vacías las funciones de los extras que no van (el enlazador descarta lo que ya
nadie usa). Los workflows `compilar-mm12.yml` y `publicar-release-mm12.yml` compilan la 230, 300, 400 y 500 con
la placa V1.2 (los mismos modelos de los paquetes oficiales de Hellbot para la V1.2; los valores de cada máquina
son los mismos que en la V1.3).

Para probar la compilación en la compu sin PlatformIO: `pruebas/compilacion-manual/compilar_f103.sh`.

## Si la probás

Seguí `LEEME-SIN-PROBAR.txt` (va adentro de cada paquete). Si la pantalla se reinicia sola o se cuelga, lo más
probable es la memoria: avisame (andreslondero@gmail.com) y recortamos más.

## Estado (2026-11-16)

Probado en una placa V1.2 real: **se reinicia en loop** al arrancar (aparece "Booting...", el logo y vuelve a
empezar). Para encontrar la causa hay una versión de prueba **B**, que es solo el tema, sin ninguno de los extras
ni el castellano: Actions → "Compilar Magna 2 placa V1.2 (mm12.zip)" → Run workflow → prueba = **B**. Si B arranca,
el problema está en los extras; si también se reinicia, está en Marlin con la pantalla MKS en esta placa (la memoria
de B es casi la misma que la de mm12).

Para volver al firmware oficial: copiar a la SD el `Robin_nano35.bin` (y `mks_pic` / `robin_nano35_cfg.txt` si los
trae) del paquete oficial de Hellbot para la V1.2 y prender la impresora; lo instala el bootloader aunque esté en el
loop.
