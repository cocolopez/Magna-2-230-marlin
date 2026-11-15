#!/usr/bin/env python3
"""Maquetas de las ideas visuales para la pantalla de la impresora (propuestas, NO están en el firmware).

Dibuja cada pantalla a 480×320 con los mismos íconos del tema (assets/), el degradé de fondo y la
letra Roboto de la UI MKS, para que el usuario elija antes de programar nada. Los números son de
ejemplo.

Uso: python3 assets-tema/maquetas_visuales.py <carpeta_lvgl> <carpeta_salida>
  <carpeta_lvgl>: la LVGL de MKS (para la letra Roboto: scripts/built_in_font/Roboto-Regular.woff).
Genera 00-actual.png … 09-*.png y dos hojas (hoja-impresion.png, hoja-resto.png) con títulos.
"""
import math
import os
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(AQUI, 'assets')
ROBOTO = None  # se define con iniciar(<carpeta_lvgl>)


def iniciar(lv):
    global ROBOTO
    ROBOTO = os.path.join(lv, 'scripts', 'built_in_font', 'Roboto-Regular.woff')
NEGRITA = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


_fuentes = {}


def f(tam):
    if tam not in _fuentes:
        _fuentes[tam] = ImageFont.truetype(ROBOTO, tam)
    return _fuentes[tam]


BLANCO, GRIS, GRIS_OSC = (238, 238, 238), (150, 150, 150), (70, 70, 70)
ROJO, ROJO_CLARO, ROJO_OSC = (214, 32, 39), (255, 77, 77), (122, 18, 22)
VERDE, AMARILLO, NARANJA = (60, 190, 90), (240, 200, 40), (240, 130, 40)


def cargar(n):
    b = open(os.path.join(A, f'bmp_{n}.bin'), 'rb').read()
    if n == 'preview':
        w, h, o = 200, 200, 0
    else:
        hd = struct.unpack('<I', b[:4])[0]
        w, h, o = (hd >> 10) & 0x7ff, (hd >> 21) & 0x7ff, 4
    px = struct.unpack('<%dH' % (w * h), b[o:o + w * h * 2])
    im = Image.new('RGBA', (w, h))
    im.putdata([(0, 0, 0, 0) if p == 0x07E0 else
                (((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31, 255) for p in px])
    return im


def fondo():
    sc = Image.new('RGB', (480, 320))
    d = ImageDraw.Draw(sc)
    a, b = (0x14, 0x14, 0x14), (0x5C, 0x0E, 0x14)
    for y in range(320):
        t = y / 319
        d.line([(0, y), (480, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return sc


def pegar(sc, n, x, y):
    im = cargar(n)
    sc.paste(im, (x, y), im)


def barra(d, x, y, w, h, pct, letra=24):
    """Barra de progreso del tema: canal oscuro con borde rojo y relleno rojo, % en blanco."""
    r = h // 2
    d.rounded_rectangle([x, y, x + w, y + h], r, fill=(22, 22, 22), outline=(110, 20, 26), width=2)
    rell = int((w - 8) * pct / 100)
    if rell > 0:
        d.rounded_rectangle([x + 4, y + 4, x + 4 + max(rell, h - 8), y + h - 4], (h - 8) // 2, fill=(205, 32, 40))
    d.text((x + w / 2, y + h / 2), f'{pct}%', font=f(letra), fill=(255, 255, 255), anchor='mm')


def boton_atras(d):
    d.rounded_rectangle([380, 272, 470, 310], 8, fill=(26, 26, 26), outline=(110, 110, 110), width=2)
    d.text((425, 291), 'Atrás', font=f(16), fill=BLANCO, anchor='mm')


def boton_inferior(sc, d, n, x, texto):
    pegar(sc, n, x, 240)
    d.text((x + 100, 280), texto, font=f(16), fill=BLANCO, anchor='mm')


def pantalla_impresion(tiempo=True, linea=None, barra_grande=False, miniatura=None, titulo='Imprimiendo  ·  soporte_camara.gcode',
                       reloj_chico=False, pct=45, ext='210/210', omitir=()):
    """La pantalla de impresión de la UI MKS con el tema (posiciones de draw_printing.cpp)."""
    sc = fondo()
    d = ImageDraw.Draw(sc)
    d.text((3, 8), titulo, font=f(16), fill=BLANCO)
    if reloj_chico:
        reloj(d)
    if miniatura is None:
        sc.paste(cargar('preview').convert('RGB'), (2, 36))
    else:
        sc.paste(miniatura, (2, 36))
    if barra_grande and linea:
        barra(d, 205, 32, 270, 40, pct, 30)
    elif barra_grande:
        barra(d, 205, 32, 270, 50, pct, 32)
    elif linea:
        barra(d, 205, 34, 270, 30, pct, 20)
    else:
        barra(d, 205, 36, 270, 40, pct, 24)
    if linea:
        d.text((340, 79 if barra_grande else 75), linea, font=f(14 if barra_grande else 15), fill=(255, 205, 205), anchor='mm')
    filas = [('time_state', 206, 86, '01:23:45' if tiempo else ''), ('zpos_state', 350, 86, '12.40'),
             ('ext1_state', 206, 136, ext), ('fan_state', 350, 136, '100%'),
             ('bed_state', 206, 186, '60/60')]
    for n, x, y, t in filas:
        if n in omitir:
            continue
        pegar(sc, n, x, y)
        d.text((x + 50, y + 22), t, font=f(16), fill=BLANCO, anchor='lm')
    boton_inferior(sc, d, 'pause', 5, 'Pausa')
    boton_inferior(sc, d, 'stop', 165, 'Detener')
    boton_inferior(sc, d, 'operate', 325, 'Opciones')
    return sc


def reloj(d, hora='21:05'):
    """Hora chica arriba a la derecha (todas las pantallas menos la principal)."""
    d.text((476, 16), hora, font=f(16), fill=(200, 200, 200), anchor='rm')


def principal(reloj=False, iconos=False):
    """Pantalla principal (igual que simular_pantallas.py) con los agregados opcionales."""
    sc = fondo()
    d = ImageDraw.Draw(sc)
    fb = ImageFont.truetype(NEGRITA, 26)
    d.text((24, 24), 'M A G N A', font=fb, fill=BLANCO)
    w = d.textlength('M A G N A', font=fb)
    d.text((24 + w + 10, 24), '2', font=fb, fill=ROJO)
    d.line([(20, 72), (460, 72)], fill=ROJO, width=2)
    for i in range(5):
        d.line([(0, 236 + i * 4), (480, 236 + i * 4)], fill=(0x80 + i * 0x14, 0x12 + i * 3, 0x18 + i * 3), width=2)
    for x, n, t in ((20, 'tool', 'Ajustes'), (180, 'set', 'Config'), (340, 'printing', 'Imprimir')):
        pegar(sc, n, x, 90)
        d.text((x + 58, 210), t, font=f(16), fill=BLANCO, anchor='mm')
    for x, n, t in ((20, 'ext1_state', '28 -> 0'), (210, 'bed_state', '26 -> 0')):
        pegar(sc, n, x, 260)
        d.text((x + 52, 282), t, font=f(16), fill=BLANCO, anchor='lm')
    if reloj:
        d.text((458, 30), '21:05', font=f(30), fill=BLANCO, anchor='rm')
        d.text((458, 56), 'sáb 14/11', font=f(14), fill=GRIS, anchor='rm')
    if iconos:
        x0 = 300 if reloj else 458
        icono_wifi(d, x0 - 10, 44, BLANCO)
        icono_avion(d, x0 - 50, 44, BLANCO)
        d.text((x0 - 30, 64), '', font=f(12))
    return sc


def icono_wifi(d, cx, cy, color, tachado=False):
    for r in (6, 12, 18):
        d.arc([cx - r, cy - r + 8, cx + r, cy + r + 8], 225, 315, fill=color, width=3)
    d.ellipse([cx - 3, cy + 5, cx + 3, cy + 11], fill=color)
    if tachado:
        d.line([(cx - 16, cy - 8), (cx + 16, cy + 14)], fill=ROJO, width=3)


def icono_avion(d, cx, cy, color):
    """Avión de papel de líneas (genérico), como el de la sección Telegram de las apps."""
    p = [(cx - 14, cy), (cx + 14, cy - 12), (cx + 6, cy + 13), (cx - 2, cy + 4)]
    d.line(p + [p[0]], fill=color, width=2, joint='curve')
    d.line([(cx + 14, cy - 12), (cx - 2, cy + 4)], fill=color, width=2)


def icono_pausa(d, cx, cy, color):
    d.rectangle([cx - 7, cy - 9, cx - 2, cy + 9], fill=color)
    d.rectangle([cx + 2, cy - 9, cx + 7, cy + 9], fill=color)


def miniatura_pieza():
    """Una miniatura de ejemplo como la que guarda Cura (pieza amarilla sobre fondo oscuro)."""
    im = Image.new('RGB', (200, 200), (34, 34, 38))
    d = ImageDraw.Draw(im)
    for i in range(0, 200, 20):
        d.line([(i, 150), (100 + (i - 100) * 1.6, 200)], fill=(55, 55, 60))
    d.line([(0, 150), (200, 150)], fill=(55, 55, 60))
    cx, cy = 100, 110
    # pie de soporte en perspectiva: base, columna y cabeza
    d.polygon([(40, 150), (100, 175), (160, 150), (100, 128)], fill=(200, 160, 30))
    d.polygon([(40, 150), (100, 175), (100, 185), (40, 160)], fill=(150, 115, 20))
    d.polygon([(160, 150), (100, 175), (100, 185), (160, 160)], fill=(175, 135, 25))
    d.rectangle([88, 60, 112, 155], fill=(220, 180, 40))
    d.rectangle([100, 60, 112, 155], fill=(185, 145, 30))
    d.ellipse([70, 35, 130, 75], fill=(235, 195, 50))
    d.ellipse([88, 47, 112, 63], fill=(120, 90, 15))
    return im


def resumen_terminada():
    sc = fondo()
    d = ImageDraw.Draw(sc)
    d.text((240, 34), '¡Impresión terminada!', font=f(30), fill=BLANCO, anchor='mm')
    d.line([(60, 58), (420, 58)], fill=ROJO, width=2)
    d.text((240, 80), 'soporte_camara.gcode', font=f(16), fill=GRIS, anchor='mm')
    datos = [('time_state', 'Tiempo', '3 h 42 min'), ('ext1_state', 'Filamento', '48 g  ·  16,1 m'), (None, 'Costo', '$ 1.250')]
    for i, (n, k, v) in enumerate(datos):
        y = 102 + i * 50
        if n:
            pegar(sc, n, 70, y)
        else:
            d.ellipse([74, y + 4, 110, y + 40], outline=BLANCO, width=3)
            d.text((92, y + 22), '$', font=f(22), fill=ROJO, anchor='mm')
        d.text((128, y + 22), k, font=f(18), fill=GRIS, anchor='lm')
        d.text((410, y + 22), v, font=f(24), fill=BLANCO, anchor='rm')
    for x, t, rojo in ((40, 'Imprimir de nuevo', False), (250, 'Aceptar', True)):
        d.rounded_rectangle([x, 262, x + 190, 306], 8, fill=(26, 26, 26), outline=ROJO if rojo else (110, 110, 110), width=2)
        d.text((x + 95, 284), t, font=f(18), fill=BLANCO, anchor='mm')
    return sc


def grafico_temperaturas():
    sc = fondo()
    d = ImageDraw.Draw(sc)
    d.text((3, 8), 'Temperaturas  ·  últimos 10 min', font=f(16), fill=BLANCO)
    x0, y0, w, h = 50, 40, 410, 190
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(18, 18, 18), outline=GRIS_OSC)
    for t in range(0, 251, 50):
        y = y0 + h - t * h / 250
        d.line([(x0, y), (x0 + w, y)], fill=(48, 48, 48))
        d.text((x0 - 6, y), str(t), font=f(13), fill=GRIS, anchor='rm')
    for m in range(0, 11, 2):
        x = x0 + m * w / 10
        d.text((x, y0 + h + 10), f'-{10 - m}' if m < 10 else 'ahora', font=f(12), fill=GRIS, anchor='mm')

    def curva(objetivo, inicio, tau, ruido, color):
        pts = []
        for i in range(0, w + 1, 3):
            s = i / w * 600
            v = objetivo - (objetivo - inicio) * math.exp(-s / tau) + ruido * math.sin(s / 7) * (1 - math.exp(-s / tau))
            if s > 90 and objetivo > 100:
                v = objetivo + ruido * math.sin(s / 9)
            pts.append((x0 + i, y0 + h - v * h / 250))
        d.line(pts, fill=color, width=3)
        y = y0 + h - objetivo * h / 250
        for x in range(x0, x0 + w, 12):
            d.line([(x, y), (x + 6, y)], fill=color, width=1)

    curva(210, 30, 35, 1.5, ROJO_CLARO)
    curva(60, 25, 120, 0.4, NARANJA)
    d.rectangle([x0 + 10, y0 + 10, x0 + 175, y0 + 58], fill=(26, 26, 26))
    d.line([(x0 + 18, y0 + 22), (x0 + 38, y0 + 22)], fill=ROJO_CLARO, width=3)
    d.text((x0 + 46, y0 + 22), 'Hotend 210 / 210', font=f(14), fill=BLANCO, anchor='lm')
    d.line([(x0 + 18, y0 + 45), (x0 + 38, y0 + 45)], fill=NARANJA, width=3)
    d.text((x0 + 46, y0 + 45), 'Cama 60 / 60', font=f(14), fill=BLANCO, anchor='lm')
    boton_atras(d)
    d.text((50, 290), '- - -  objetivo', font=f(13), fill=GRIS, anchor='lm')
    return sc


def mapa_nivelacion():
    sc = fondo()
    d = ImageDraw.Draw(sc)
    d.text((3, 8), 'Nivelación de la cama  (BLTouch, 5 × 5)', font=f(16), fill=BLANCO)
    valores = [[0.12, 0.08, 0.05, 0.07, 0.11],
               [0.06, 0.02, 0.00, 0.03, 0.08],
               [0.02, -0.01, -0.03, 0.00, 0.04],
               [0.00, -0.04, -0.06, -0.02, 0.03],
               [0.03, -0.02, -0.05, 0.01, 0.06]]

    def color(v):
        a = abs(v)
        if a <= 0.05:
            return (40, 140, 70)
        if a <= 0.10:
            return (190, 160, 30)
        return (190, 40, 40)

    x0, y0, c = 20, 40, 44
    for fila in range(5):
        for col in range(5):
            v = valores[fila][col]
            x, y = x0 + col * c, y0 + fila * c
            d.rectangle([x, y, x + c - 3, y + c - 3], fill=color(v))
            d.text((x + c / 2 - 1, y + c / 2 - 1), f'{v:+.2f}'.replace('.', ','), font=f(12), fill=(255, 255, 255), anchor='mm')
    d.text((x0 + 110, y0 + 5 * c + 10), 'frente', font=f(13), fill=GRIS, anchor='mm')
    d.text((x0 + 110, y0 - 4), '', font=f(13), fill=GRIS, anchor='mm')
    tx = 262
    d.text((tx, 52), 'Diferencia máxima', font=f(15), fill=GRIS)
    d.text((tx, 72), '0,18 mm', font=f(30), fill=BLANCO)
    d.text((tx, 112), 'Lo más alto: atrás a la izquierda', font=f(14), fill=BLANCO)
    d.text((tx, 132), 'Lo más bajo: centro, adelante', font=f(14), fill=BLANCO)
    for i, col in enumerate(((40, 140, 70), (190, 160, 30), (190, 40, 40))):
        y = 168 + i * 26
        d.rectangle([tx, y, tx + 18, y + 18], fill=col)
        d.text((tx + 28, y + 9), ('hasta 0,05 mm', 'hasta 0,10 mm', 'más de 0,10 mm')[i], font=f(14), fill=BLANCO, anchor='lm')
    boton_atras(d)
    return sc


PANTALLAS = [
    ('00-actual', 'Hoy: pantalla de impresión', lambda: pantalla_impresion()),
    ('01-tiempo-restante', '1. Tiempo restante y hora de fin', lambda: pantalla_impresion(linea='Faltan 2 h 15 min  ·  termina 23:40')),
    ('02-capas', '2. Capa actual / total', lambda: pantalla_impresion(linea='Capa 57 de 210')),
    ('03-barra-grande', '3. Barra de progreso más grande', lambda: pantalla_impresion(barra_grande=True)),
    ('04-vista-previa', '4. Vista previa de la pieza (miniatura de Cura)', lambda: pantalla_impresion(miniatura=miniatura_pieza())),
    ('05-resumen', '5. Resumen al terminar', resumen_terminada),
    ('06-iconos-estado', '6. Íconos de estado (WiFi, Telegram)', lambda: principal(iconos=True)),
    ('07-reloj', '7. Reloj en el inicio', lambda: principal(reloj=True)),
    ('08-grafico', '8. Gráfico de temperaturas', grafico_temperaturas),
    ('09-nivelacion', '9. Mapa de nivelación', mapa_nivelacion),
    ('10-todo-junto', 'Impresión con 1 + 2 + 3 juntos', lambda: pantalla_impresion(linea='Capa 57/210 · faltan 2:15 · fin 23:40', barra_grande=True)),
]


def hoja(items, nombre, OUT):
    cols = 2
    filas = (len(items) + cols - 1) // cols
    H = Image.new('RGB', (cols * 500 + 10, filas * 360 + 10), (45, 45, 45))
    d = ImageDraw.Draw(H)
    for i, (archivo, titulo, im) in enumerate(items):
        x, y = 10 + (i % cols) * 500, 10 + (i // cols) * 360
        d.text((x, y + 4), titulo, font=f(20), fill=(255, 255, 255))
        H.paste(im, (x, y + 32))
    H.save(os.path.join(OUT, nombre))


if __name__ == '__main__':
    iniciar(sys.argv[1])
    OUT = sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    hechas = []
    for archivo, titulo, fn in PANTALLAS:
        im = fn()
        im.save(os.path.join(OUT, archivo + '.png'))
        hechas.append((archivo, titulo, im))
    hoja([h for h in hechas if h[0][:2] in ('00', '01', '02', '03', '04', '10')], 'hoja-impresion.png', OUT)
    hoja([h for h in hechas if h[0][:2] in ('05', '06', '07', '08', '09')], 'hoja-resto.png', OUT)
    print('maquetas en', OUT)
