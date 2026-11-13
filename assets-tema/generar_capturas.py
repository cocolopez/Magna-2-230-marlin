#!/usr/bin/env python3
"""Genera las capturas del README (docs-magna/capturas/) a partir de los archivos reales del tema
(assets/*.bin) y del fondo/decoración que aplica aplicar_colores.py. Es una simulación fiel de la
pantalla 480x320 (las fuentes del equipo pueden variar levemente).
Uso: python3 generar_capturas.py [carpeta_assets] [carpeta_salida]"""
import os, struct, sys
from PIL import Image, ImageDraw, ImageFont
AQUI = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 'assets')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, '..', 'docs-magna', 'capturas')
os.makedirs(OUT, exist_ok=True)
FT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
F = ImageFont.truetype(FT, 14); FS = ImageFont.truetype(FT, 13)
BL = (238, 238, 238); RJ = (214, 32, 39)
def load(n):
    b = open(os.path.join(A, f'bmp_{n}.bin'), 'rb').read()
    if n == 'logo': w, h, o = 480, 320, 0
    else: hd = struct.unpack('<I', b[:4])[0]; w, h, o = (hd >> 10) & 0x7ff, (hd >> 21) & 0x7ff, 4
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
def pegar(sc, n, x, y): im = load(n); sc.paste(im, (x, y), im)
def principal():
    sc = fondo(); d = ImageDraw.Draw(sc); f = ImageFont.truetype(FB, 26)
    d.text((24, 24), 'M A G N A', font=f, fill=BL); w = d.textlength('M A G N A', font=f)
    d.text((24 + w + 10, 24), '2', font=f, fill=RJ)
    d.line([(20, 72), (460, 72)], fill=RJ, width=2)
    for i in range(5): d.line([(0, 236 + i * 4), (480, 236 + i * 4)], fill=(0x50 + i * 0x18, 0x0C + i * 3, 0x10 + i * 3), width=2)
    for x, n, t in ((20, 'tool', 'Ajustes'), (180, 'set', 'Config'), (340, 'printing', 'Imprimir')):
        pegar(sc, n, x, 90); d.text((x + 58, 210), t, font=F, fill=BL, anchor='mm')
    for x, n, t in ((20, 'ext1_state', '24 -> 0'), (210, 'bed_state', '23 -> 0')):
        pegar(sc, n, x, 260); d.text((x + 52, 282), t, font=F, fill=BL, anchor='lm')
    return sc
def menu(titulo, items):
    sc = fondo(); d = ImageDraw.Draw(sc); d.text((3, 5), titulo, font=F, fill=BL)
    for i, (n, lab) in enumerate(items):
        x = 2 + (i % 4) * 119; y = 36 + (i // 4) * 142
        pegar(sc, n, x, y); d.text((x + 58, y + 120), lab, font=F, fill=BL, anchor='mm')
    return sc
def imprimiendo():
    sc = fondo(); d = ImageDraw.Draw(sc)
    d.text((3, 5), 'Imprimiendo: soporte_camara.gcode', font=F, fill=BL)
    d.rectangle([12, 40, 200, 228], outline=(70, 70, 70))
    for k in range(12): d.line([(40, 200 - k * 12), (172, 200 - k * 12)], fill=(150, 30, 34) if k < 8 else (70, 70, 70), width=3)
    d.text((106, 214), 'vista previa', font=FS, fill=(110, 110, 110), anchor='mm')
    datos = [('ext1_state', '210 / 210'), ('bed_state', '60 / 60'), ('fan_state', '100%'), ('time_state', '01:24'), ('zpos_state', '12.40'), ('speed_state', '100%')]
    for i, (n, t) in enumerate(datos):
        x = 215 + (i % 2) * 135; y = 40 + (i // 2) * 60
        pegar(sc, n, x, y); d.text((x + 52, y + 22), t, font=F, fill=BL, anchor='lm')
    d.rectangle([12, 236, 468, 246], fill=(45, 45, 45)); d.rectangle([12, 236, 300, 246], fill=RJ)
    d.text((468, 226), '63%', font=FS, fill=BL, anchor='rm')
    for i, (n, t) in enumerate((('operate', 'Opciones'), ('pause', 'Pausa'), ('stop', 'Detener'))):
        x = 5 + i * 158; pegar(sc, n, x, 240); d.text((x + 62, 279), t, font=F, fill=BL, anchor='lm')
    return sc
def iconos():
    nombres = ['printing', 'set', 'tool', 'preHeat', 'mov', 'zero', 'leveling', 'filamentchange', 'extruct', 'fan',
               'speed', 'file', 'dir', 'sd', 'usb_disk', 'wifi', 'language', 'machine_para', 'eeprom_settings', 'about',
               'extru1', 'extru2', 'in', 'out', 'xAdd', 'yAdd', 'zAdd', 'zeroZ', 'step_move1', 'return']
    cols = 10; sc = Image.new('RGB', (cols * 117, 3 * 112)); d = ImageDraw.Draw(sc)
    a, b = (0x14, 0x14, 0x14), (0x2E, 0x0A, 0x0D)
    for y in range(sc.height):
        t = y / (sc.height - 1); d.line([(0, y), (sc.width, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    for i, n in enumerate(nombres):
        im = load(n).crop((0, 6, 117, 104)); sc.paste(im, ((i % cols) * 117, (i // cols) * 112 + 6), im)
    return sc
def marco(im, escala=2):
    """Agranda la captura x2 (sin suavizar) y le pone un marco tipo pantalla."""
    im = im.resize((im.width * escala, im.height * escala), Image.NEAREST)
    m = Image.new('RGB', (im.width + 24, im.height + 24), (12, 12, 12))
    ImageDraw.Draw(m).rounded_rectangle([0, 0, m.width - 1, m.height - 1], radius=14, outline=(55, 55, 55), width=3)
    m.paste(im, (12, 12)); return m
capturas = {
    'arranque.png': load('logo').convert('RGB'),
    'principal.png': principal(),
    'ajustes.png': menu('Ajustes', [('preHeat', 'Precalentar'), ('extruct', 'Extrusor'), ('mov', 'Mover'), ('zero', 'Home'),
                                    ('leveling', 'Nivelar'), ('filamentchange', 'Filamento'), ('more', 'Más'), ('return', 'Atrás')]),
    'configuracion.png': menu('Configuración', [('fan', 'Ventilador'), ('speed', 'Velocidad'), ('wifi', 'WiFi'), ('language', 'Idioma'),
                                                ('machine_para', 'Máquina'), ('eeprom_settings', 'EEPROM'), ('about', 'Acerca de'), ('return', 'Atrás')]),
    'imprimiendo.png': imprimiendo(),
}
for n, im in capturas.items(): marco(im).save(os.path.join(OUT, n))
iconos().save(os.path.join(OUT, 'iconos.png'))
print('capturas en', OUT, sorted(os.listdir(OUT)))
