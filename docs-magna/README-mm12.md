# Marlin 2.1.3 para las Hellbot Magna 2 con placa V1.2 (mm12)

Versión recortada del firmware que hice para mi Magna 2 230 (repo mm2), para las Magna 2 que
vinieron con la placa **MKS Robin Nano V1.2**: 230, 300, 400 y 500.

> ⚠️ **SIN PROBAR (UNTESTED).** Tengo una Magna 2 230 con placa V1.3; nunca probé nada de esto en una placa V1.2.
> Los paquetes se llaman `Magna2-XXX-placaV12-firmware-UNTESTED` y traen `LEEME-SIN-PROBAR.txt`. Si lo probás,
> avisame cómo te fue.

## Por qué recortada

La V1.2 tiene un procesador más lento (72 MHz) y 64 KB de memoria, contra 192 KB de la V1.3. Marlin con la pantalla
MKS ya ocupa casi toda esa memoria, así que de lo que le agregué a la pantalla quedó lo que es liviano:

- el tema negro y rojo con sus íconos, y la pantalla en castellano;
- la hora (chica, arriba) y la línea "capa · faltan · fin" mientras imprime;
- todo lo de MagnAir: mensajes en la pantalla, aviso por Telegram si se detiene por un error, precalentado con las
  temperaturas de la app, datos de calibración;
- melodías y créditos.

No tiene animaciones, gráfico de temperaturas, "siempre encendida", vista en vivo, cancelar piezas desde la pantalla,
resumen al terminar, bloqueo ni input shaping. La tabla completa está en
[docs-magna/PLACA-V12.md](docs-magna/PLACA-V12.md).

## Modelos

| Modelo | Cama | Nivelación |
|---|---|---|
| Magna 2 230 | 230 × 230 × 250 | manual |
| Magna 2 300 | 300 × 300 × 400 | manual |
| Magna 2 400 | 400 × 400 × 400 | BLTouch |
| Magna 2 500 | 500 × 500 × 500 | BLTouch |

Los valores salen de los firmware oficiales de Hellbot para la placa V1.2 (son los mismos que los de la V1.3). Qué
se sacó de ahí y qué no: [docs-magna/MODELOS.md](docs-magna/MODELOS.md).

## MagnAir

El firmware del módulo WiFi es el mismo que en la V1.3 (MagnAir). Cuando ve una placa V1.2 le
pregunta el estado cada 5 segundos en lugar de cada 2, y la app y la página esconden las opciones que esta placa no
tiene.

## Compilar

Es el mismo código que mm2. Con GitHub:

1. Copiá `github-workflows/compilar-mm12.yml` y `github-workflows/publicar-release-mm12.yml` a `.github/workflows/`.
2. Subí `mm12.zip` a la raíz del repo. Se compilan los cuatro modelos en paralelo.
3. Bajá el de tu modelo en Actions: `Magna2-XXX-placaV12-firmware-UNTESTED`.

## Instalar

1. Guardá tu configuración actual con `M503` y tené a mano el firmware oficial para volver atrás.
2. Copiá `Robin_nano35.bin` y la carpeta `assets` a la raíz de una microSD en FAT32.
3. Prendé la impresora con la SD puesta y no la apagues mientras actualiza.
4. `M502` y `M500`.
5. Seguí `LEEME-SIN-PROBAR.txt`: probá el sentido de cada eje antes de hacer home, home de a un eje, calentá sin
   imprimir.

## Autor

Creado por **Andrés Londero** · [andreslondero@gmail.com](mailto:andreslondero@gmail.com)

> Usalo bajo tu responsabilidad.
