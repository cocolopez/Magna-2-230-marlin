#!/usr/bin/env python3
"""Simula las pantallas de menú con y sin la decoración propuesta (subrayado del título, separador entre
filas, líneas de capas abajo y, en Archivos, una división vertical), usando los .bin reales del tema.
Uso: python3 simular_menus.py [carpeta_assets] [salida.png]"""
import os, struct, sys
from PIL import Image, ImageDraw, ImageFont
AQUI = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 'assets')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, 'preview', 'menus_antes_despues.png')
FT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
F = ImageFont.truetype(FT, 15); FT_T = ImageFont.truetype(FB, 15); FG = ImageFont.truetype(FB, 34); FM = ImageFont.truetype(FT, 13)
BL = (238, 238, 238); RJ = (214, 32, 39)
def load(n):
    b = open(os.path.join(A, f'bmp_{n}.bin'), 'rb').read()
    hd = struct.unpack('<I', b[:4])[0]; w, h = (hd >> 10) & 0x7ff, (hd >> 21) & 0x7ff
    px = struct.unpack('<%dH' % (w * h), b[4:4 + w * h * 2]); im = Image.new('RGBA', (w, h))
    im.putdata([(0, 0, 0, 0) if p == 0x07E0 else (((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31, 255) for p in px])
    return im
def fondo():
    sc = Image.new('RGB', (480, 320)); d = ImageDraw.Draw(sc); a, b = (0x14, 0x14, 0x14), (0x5C, 0x0E, 0x14)
    for y in range(320):
        t = y / 319; d.line([(0, y), (480, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return sc
def decorar_b(d, titulo=True, columna_nav=False):
    """Variante B (más marcada): franja de encabezado, línea roja completa, capas más gruesas."""
    if titulo:
        d.rectangle([0, 0, 480, 31], fill=(10, 10, 10))                 # franja oscura del título
        d.rectangle([0, 6, 2, 25], fill=RJ)                             # acento rojo a la izquierda
    d.line([(0, 32), (480, 32)], fill=RJ, width=2)                      # línea roja de lado a lado
    for x in range(0, 480, 12):                                         # separador punteado entre filas
        d.line([(x, 177), (x + 5, 177)], fill=(140, 24, 30), width=1)
    for i, c in enumerate(((0x86, 0x14, 0x1A), (0xAE, 0x1A, 0x20), (0xD6, 0x20, 0x26))):
        d.line([(0, 309 + i * 4), (480, 309 + i * 4)], fill=c, width=2)
    if columna_nav:
        d.line([(356, 40), (356, 304)], fill=(140, 24, 30), width=1)
def decorar(d, titulo=True, columna_nav=False):
    """Variante A (sutil). Lo que agregaría el firmware (mismas coordenadas que el código propuesto)."""
    if titulo:
        d.line([(3, 31), (150, 31)], fill=RJ, width=2)                 # subrayado rojo del título
        d.line([(150, 31), (477, 31)], fill=(70, 70, 70), width=1)     # continúa en gris
    d.line([(0, 177), (480, 177)], fill=(80, 16, 20), width=1)         # separador entre filas
    for i, c in enumerate(((0x4A, 0x0C, 0x10), (0x78, 0x12, 0x18), (0xB0, 0x1A, 0x22))):   # capas abajo
        d.line([(0, 311 + i * 3), (480, 311 + i * 3)], fill=c, width=1)
    if columna_nav:
        d.line([(356, 40), (356, 304)], fill=(90, 18, 22), width=1)    # división archivos / navegación
def grilla(sc, d, items, y0=36):
    for i, (n, lab) in enumerate(items):
        x = 2 + (i % 4) * 119; y = y0 + (i // 4) * 142
        if n: im = load(n); sc.paste(im, (x, y), im)
        if lab: d.text((x + 58, y + 118), lab, font=F, fill=BL, anchor='mm')
def ajustes(dec):
    sc = fondo(); d = ImageDraw.Draw(sc)
    if dec: (decorar_b if dec == "B" else decorar)(d)
    d.text((3, 6), 'Inicio>Ajustes', font=FT_T, fill=BL)
    grilla(sc, d, [('preHeat', 'Precalentar'), ('extruct', 'Extrusor'), ('mov', 'Mover'), ('zero', 'Origen'),
                   ('leveling', 'Leveling'), ('filamentchange', 'Filamento'), ('more', 'Más'), ('return', 'Atrás')])
    return sc
def config(dec):
    sc = fondo(); d = ImageDraw.Draw(sc)
    if dec: (decorar_b if dec == "B" else decorar)(d)
    d.text((3, 6), 'Inicio>Config', font=FT_T, fill=BL)
    grilla(sc, d, [('eeprom_settings', 'Eeprom Set'), ('fan', 'Ventilador'), ('about', 'Acerca'), ('function1', 'Apagar motor'),
                   ('machine_para', 'Config'), ('language', 'Language'), ('wifi', 'WiFi'), ('return', 'Atrás')])
    return sc
def archivos(dec):
    sc = fondo(); d = ImageDraw.Draw(sc)
    if dec: (decorar_b if dec == "B" else decorar)(d, titulo=False, columna_nav=True)
    nombres = [('file', 'wii2hdmi\nxbox.g'), ('file', 'Brillian\nt Bo~.g'), ('file', 'top.g'), ('dir', 'GCODE'), ('dir', 'opcional\n-wifi'), ('dir', 'LOST.g')]
    for i, (n, t) in enumerate(nombres):
        x = 2 + (i % 3) * 119; y = 36 + (i // 3) * 142
        im = load(n); sc.paste(im, (x, y), im); d.multiline_text((x + 58, y + 112), t, font=FM, fill=BL, anchor='ma', align='center')
    for k, n in enumerate(('pageUp', 'pageDown', 'back')):
        im = load(n); sc.paste(im, (359, 36 + k * 94), im)
    return sc
def precalentar(dec):
    sc = fondo(); d = ImageDraw.Draw(sc)
    if dec: (decorar_b if dec == "B" else decorar)(d)
    d.text((3, 6), 'Inicio>Precalentar', font=FT_T, fill=BL)
    grilla(sc, d, [('Add', 'Más'), (None, None), (None, None), ('Dec', 'Menos'),
                   ('extru1', 'Extrusor1:'), (None, '10°C'), ('speed0', 'Apagar'), ('return', 'Atrás')])
    d.text((180, 62), 'ABS', font=F, fill=BL, anchor='mm'); d.text((300, 62), 'PLA', font=F, fill=BL, anchor='mm')
    d.text((240, 110), 'Extrusor1: : 29/0', font=F, fill=BL, anchor='mm')
    d.text((180, 232), '10', font=FG, fill=BL, anchor='mm'); d.text((180, 258), '°C', font=FM, fill=RJ, anchor='mm')
    return sc
pantallas = [('Ajustes', ajustes), ('Config', config), ('Archivos', archivos), ('Precalentar', precalentar)]
W, H = 480, 320; M = 14; ET = 26
hoja = Image.new('RGB', (3 * W + 4 * M, len(pantallas) * (H + ET + M) + ET + M), (45, 45, 45)); dh = ImageDraw.Draw(hoja)
fh = ImageFont.truetype(FB, 18)
for c, (t, col) in enumerate((('ACTUAL', (200, 200, 200)), ('A · SUTIL', (255, 120, 120)), ('B · MARCADA', (255, 70, 70)))):
    dh.text((M + c * (W + M) + W / 2, M + 4), t, font=fh, fill=col, anchor='mt')
for k, (nom, fn) in enumerate(pantallas):
    y = ET + M + k * (H + ET + M)
    dh.text((M, y + 4), nom, font=ImageFont.truetype(FT, 15), fill=(200, 200, 200))
    for c, v in enumerate((False, True, "B")):
        hoja.paste(fn(v), (M + c * (W + M), y + ET))
hoja.save(OUT); print('ok', OUT)
