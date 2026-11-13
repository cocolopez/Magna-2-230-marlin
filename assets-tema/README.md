# Tema "Negro y Rojo" para la pantalla MKS TFT35

Íconos y pantalla de arranque propios, de estilo minimalista: fondo negro, trazos blancos y detalles en rojo. Reemplazan a los de Makerbase.

| Archivo | Qué hace |
|---|---|
| `assets/` | Los 138 archivos ya generados (`bmp_*.bin`), listos para la SD. |
| `generar_assets.py` | Genera todos los íconos y el logo (`python3 generar_assets.py assets --preview`). Requiere Pillow, DejaVu Sans y Noto Sans CJK (para 简/繁). |
| `aplicar_colores.py` | Cambia los colores fijos del código de la pantalla (azul y amarillo de Makerbase → rojo y gris). Lo corre el workflow. |
| `simular_pantallas.py` | Arma una simulación de cómo se ven las pantallas a partir de los `.bin`. |
| `preview/` | Imágenes de muestra: logo, todos los íconos y la simulación. |

## Formato (verificado contra los originales)
- **Íconos:** encabezado LVGL 6 de 4 bytes (`cf=4` TRUE_COLOR, ancho y alto), píxeles RGB565 little-endian y 1 byte final `0x0A`. Mismos nombres y tamaños que los de Makerbase:
  - 117×140: íconos de menú. El dibujo va entre las filas 10 y 90; las filas 100 a 139 quedan para el texto. En los `_sel`, esas filas llevan la franja de "seleccionado".
  - 45×45: estados de la pantalla de impresión.
  - 150×80: botones Opciones, Pausa, Reanudar y Detener.
  - 117×92: Volver, Página arriba y Página abajo.
  - 70×40, 70×28, 90×30, 10×17: botones chicos, campos e interruptores.
- **`bmp_logo.bin`:** pantalla completa de 480×320 en RGB565, sin encabezado.
- **No se reemplazan** `FontUNIGBK.bin` (la fuente) ni `bmp_preview.bin`. Se usan los de Makerbase que baja la compilación.
- El fondo de los íconos es `#1A1A1A`, el mismo color que la pantalla (`LV_COLOR_BACKGROUND`), así no se notan los bordes.

## Cómo se instala
La compilación de GitHub ya pone estos archivos en la carpeta `assets` del artefacto. Al flashear (ver `docs-magna/COMO-FLASHEAR.md`), la pantalla los copia a su memoria y renombra la carpeta de la SD a `_assets`.

- **Cambiar solo los íconos, sin reflashear:** poné una carpeta `assets` nueva en la SD y prendé la impresora.
- **Volver a los íconos de Makerbase:** hacé lo mismo con los `assets` originales. Para recuperar también los colores originales, borrá la carpeta `assets-tema` del repo y recompilá.

## Colores (`aplicar_colores.py`)
| Elemento | Antes | Ahora |
|---|---|---|
| Fondo de botones de parámetros | azul `#4A52FF` | rojo oscuro `#7A1216` |
| Texto seleccionado | azul / amarillo | rojo `#E0262C` / `#FF4D4D` |
| Líneas separadoras | azul `#4954FF` | gris `#5A5A5A` |
| Teclado (WiFi) | marrón | gris, y rojo al apretar |

El script usa reemplazos exactos. Si una versión futura de Marlin cambia esas líneas, avisa "NO ENCONTRADO" y deja el color original, sin romper la compilación.

## Pantalla de arranque
Dice "MAGNA" con un "2" grande en rojo por detrás de la N y la A. Debajo va la versión completa de Marlin, leída de `MARLIN_VERSION` (`2.1.3-b3` se muestra como "MARLIN 2.1.3-BETA3"), y "DUAL EXTRUSION". A la derecha, la boquilla imprime un **tornillo de cabeza hexagonal** con la rosca hacia arriba, en capas rojas: un 55 % ya impreso y la parte que falta en contorno gris. La boquilla siempre queda sobre material de la capa actual.

Hay otras formas listas en `FORMAS` (engranaje, tuerca, rodamiento, torre, cohete, faro, jarrón, diamante, pino, montaña). Se elige con `FORMA_ARRANQUE=engranaje python3 generar_assets.py assets`.

El logo de arranque, los íconos y la imagen de fondo son diseño propio generado por código. No usan imágenes ni marcas de terceros.
