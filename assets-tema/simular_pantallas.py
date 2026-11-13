#!/usr/bin/env python3
"""Simula la pantalla principal y otras pantallas de la UI MKS con el tema: degradé de fondo, íconos
transparentes (verde puro = transparente) y la decoración que agrega aplicar_colores.py.
Uso: python3 simular_pantallas.py <carpeta_assets> <salida.png>"""
import struct, sys, os
from PIL import Image, ImageDraw, ImageFont
A, out = sys.argv[1], sys.argv[2]
FT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def load(n):
    b = open(os.path.join(A, f'bmp_{n}.bin'), 'rb').read()
    if n == 'logo':
        w, h, o = 480, 320, 0
    else:
        hd = struct.unpack('<I', b[:4])[0]; w, h, o = (hd >> 10) & 0x7ff, (hd >> 21) & 0x7ff, 4
    px = struct.unpack('<%dH' % (w * h), b[o:o + w * h * 2])
    im = Image.new('RGBA', (w, h))
    im.putdata([(0, 0, 0, 0) if p == 0x07E0 else (((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31, 255) for p in px])
    return im
def fondo():
    sc = Image.new('RGB', (480, 320)); d = ImageDraw.Draw(sc)
    a, b = (0x14, 0x14, 0x14), (0x2E, 0x0A, 0x0D)
    for y in range(320):
        t = y / 319; d.line([(0, y), (480, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return sc
F = ImageFont.truetype(FT, 14)
def principal():
    sc = fondo(); d = ImageDraw.Draw(sc)
    f = ImageFont.truetype(FB, 26)
    d.text((24, 24), 'M A G N A', font=f, fill=(238, 238, 238)); w = d.textlength('M A G N A', font=f)
    d.text((24 + w + 10, 24), '2', font=f, fill=(214, 32, 39))
    d.line([(20, 72), (460, 72)], fill=(214, 32, 39), width=2)
    for i in range(5):
        d.line([(0, 236 + i * 4), (480, 236 + i * 4)], fill=(0x50 + i * 0x18, 0x0C + i * 3, 0x10 + i * 3), width=2)
    for x, n, t in ((20, 'tool', 'Ajustes'), (180, 'set', 'Config'), (340, 'printing', 'Imprimir')):
        im = load(n); sc.paste(im, (x, 90), im); d.text((x + 58, 210), t, font=F, fill=(238, 238, 238), anchor='mm')
    for x, n, t in ((20, 'ext1_state', '28 -> 0'), (210, 'bed_state', '26 -> 0')):
        im = load(n); sc.paste(im, (x, 260), im); d.text((x + 52, 282), t, font=F, fill=(238, 238, 238), anchor='lm')
    return sc
def menu(items, titulo):
    sc = fondo(); d = ImageDraw.Draw(sc)
    d.text((3, 5), titulo, font=F, fill=(238, 238, 238))
    for i, (n, lab) in enumerate(items):
        x = 2 + (i % 4) * 119; y = 36 + (i // 4) * 142
        im = load(n); sc.paste(im, (x, y), im); d.text((x + 58, y + 120), lab, font=F, fill=(238, 238, 238), anchor='mm')
    return sc
m1 = principal()
m2 = menu([('preHeat', 'Precalentar'), ('extruct', 'Extrusor'), ('mov', 'Mover'), ('zero', 'Home'),
           ('leveling', 'Nivelar'), ('filamentchange', 'Filamento'), ('more', 'Más'), ('return', 'Atrás')], 'Ajustes')
lg = load('logo').convert('RGB')
hoja = Image.new('RGB', (1455, 330), (70, 70, 70))
for im, x in zip([lg, m1, m2], (5, 490, 975)): hoja.paste(im, (x, 5))
hoja.save(out)
