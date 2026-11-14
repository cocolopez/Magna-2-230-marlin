#!/usr/bin/env python3
"""
Genera la letra grande del tema (LVGL 6.1, formato "fmt_txt", 4 bits por píxel) para los
mensajes de la pantalla y el porcentaje de impresión.

  * Fuente: Roboto Regular (la misma familia que trae LVGL; licencia Apache 2.0),
    tomada de la librería LVGL que baja la compilación (scripts/built_in_font/Roboto-Regular.woff).
  * Caracteres: ASCII (0x20-0x7E) + Latin-1 (0xA0-0xFF): español, inglés, portugués, italiano,
    francés y alemán con todos sus acentos, ñ, ¿, ¡ y °.
  * Tamaño: 26 px (la letra normal de la pantalla es de 16 px). Es el más grande con el que
    la línea más larga de los mensajes en español ("filamento y luego presione"Confirmar"")
    entra en los 480 px de la pantalla.

Salida: fuente_grande.inc (C puro). aplicar_colores.py lo copia a la carpeta mks_ui de Marlin
dentro de magna_fuente_grande.cpp, y la prueba de render lo compila tal cual.

Uso: python3 generar_fuente.py [Roboto-Regular.woff|.ttf] [tamaño] [salida.inc] [nombre]
(los últimos tres solo los usa la prueba de render, para simular la letra normal de 16 px)
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
TAM = int(sys.argv[2]) if len(sys.argv) > 2 else 26
SALIDA = sys.argv[3] if len(sys.argv) > 3 else os.path.join(AQUI, 'fuente_grande.inc')
NOMBRE = sys.argv[4] if len(sys.argv) > 4 else 'magna_fuente_grande'
RANGOS = [(0x20, 0x7E), (0xA0, 0xFF)]


def buscar_fuente():
    if len(sys.argv) > 1 and sys.argv[1] != '-':
        return sys.argv[1]
    for p in (os.path.join(AQUI, 'Roboto-Regular.woff'),
              os.path.expanduser('~/marlin-tc/lvgl/scripts/built_in_font/Roboto-Regular.woff'),
              '/home/claude/tc/lvgl/scripts/built_in_font/Roboto-Regular.woff'):
        if os.path.exists(p):
            return p
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):   # reserva (solo para la prueba)
        if os.path.exists(p):
            print('aviso: sin Roboto, uso', p)
            return p
    sys.exit('No encuentro Roboto-Regular.woff: pasala como argumento')


def main():
    f = ImageFont.truetype(buscar_fuente(), TAM)
    ascenso, descenso = f.getmetrics()
    bitmap = bytearray()
    dscs = ['    {0, 0, 0, 0, 0, 0} /* id 0 reservado */']
    cmaps = []
    gid = 1
    for a, b in RANGOS:
        cmaps.append((a, b - a + 1, gid))
        for cp in range(a, b + 1):
            ch = chr(cp)
            adv = int(round(f.getlength(ch) * 16))
            x0, y0, x1, y1 = f.getbbox(ch, anchor='ls') if ch.strip() and cp != 0xA0 else (0, 0, 0, 0)
            w, h = x1 - x0, y1 - y0
            idx = len(bitmap)
            if w > 0 and h > 0:
                im = Image.new('L', (w, h), 0)
                ImageDraw.Draw(im).text((-x0, -y0), ch, font=f, fill=255, anchor='ls')
                bits, n = 0, 0
                for v in im.tobytes():          # 4 bpp, filas seguidas sin relleno (como lv_font_conv)
                    bits = (bits << 4) | (v >> 4)
                    n += 1
                    if n == 2:
                        bitmap.append(bits); bits, n = 0, 0
                if n:
                    bitmap.append(bits << 4)
            else:
                w = h = 0
                x0 = 0
                y1 = 0
            # ofs_y: borde de abajo de la caja respecto de la línea base (positivo = arriba)
            dscs.append(f'    {{{idx}, {adv}, {w}, {h}, {x0}, {-y1}}} /* U+{cp:04X} */')
            gid += 1

    hexes = ',\n'.join('    ' + ', '.join(f'0x{x:02x}' for x in bitmap[i:i + 16]) for i in range(0, len(bitmap), 16))
    cm = ',\n'.join(f'    {{{s}, {n}, {g}, NULL, NULL, 0, LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY}}' for s, n, g in cmaps)
    salida = f'''/* Magna2-230 (tema): letra grande para mensajes y porcentaje de impresión.
 * Roboto Regular {TAM} px, 4 bpp, ASCII + Latin-1. Generado por assets-tema/generar_fuente.py:
 * no editar a mano. Es C puro (vale como C y como C++), sin inicializadores con nombre.
 */
static const uint8_t magna_fg_bitmap[] = {{
{hexes}
}};

static const lv_font_fmt_txt_glyph_dsc_t magna_fg_glyph[] = {{
{chr(10).join(d + ',' for d in dscs)}
}};

static const lv_font_fmt_txt_cmap_t magna_fg_cmaps[] = {{
{cm}
}};

static lv_font_fmt_txt_dsc_t magna_fg_dsc = {{
    magna_fg_bitmap, magna_fg_glyph, magna_fg_cmaps, NULL,
    0,      /* kern_scale */
    {len(cmaps)},      /* cmap_num */
    4,      /* bpp */
    0,      /* kern_classes */
    0,      /* bitmap_format: sin comprimir */
    0, 0    /* caché */
}};

lv_font_t {NOMBRE} = {{
    lv_font_get_glyph_dsc_fmt_txt, lv_font_get_bitmap_fmt_txt,
    {ascenso + descenso},     /* line_height */
    {descenso},      /* base_line (desde abajo) */
    0,      /* subpx */
    &magna_fg_dsc
}};
'''
    salida = salida.replace('magna_fg_', NOMBRE + '_')
    open(SALIDA, 'w', encoding='utf-8').write(salida)
    print(f'{os.path.basename(SALIDA)}: {gid - 1} caracteres, {len(bitmap)} bytes de imagen, alto de línea {ascenso + descenso}')


if __name__ == '__main__':
    main()
