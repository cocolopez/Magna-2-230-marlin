#!/usr/bin/env python3
"""Maquetas de las animaciones y de las ideas copiadas de otros sistemas (propuestas, NO están en el
firmware). Usa los mismos íconos, colores y letra que maquetas_visuales.py.

Uso: python3 assets-tema/maquetas_animadas.py <carpeta_lvgl> <carpeta_salida>
Genera GIF animados (a-*.gif) y pantallas fijas (b-*.png), más hoja-ideas.png con las fijas.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import maquetas_visuales as mv  # noqa: E402
from maquetas_visuales import BLANCO, GRIS, ROJO, cargar, f, fondo, pegar  # noqa: E402

mv.iniciar(sys.argv[1])
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def gif(nombre, cuadros, ms):
    """GIF con paleta común (los colores del tema se ven igual en todos los cuadros)."""
    cuadros = [c.convert('RGB') for c in cuadros]
    muestra = cuadros[::max(1, len(cuadros) // 6)] + [cuadros[-1]]   # paleta con colores de todo el GIF
    junta = Image.new('RGB', (480, 320 * len(muestra)))
    for k, c in enumerate(muestra):
        junta.paste(c, (0, 320 * k))
    pal = junta.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [c.quantize(palette=pal, dither=Image.Dither.NONE) for c in cuadros]
    q[0].save(os.path.join(OUT, nombre), save_all=True, append_images=q[1:], duration=ms, loop=0, optimize=False)


def color_temp(t):
    """Azul (frío) -> blanco -> rojo (caliente), para el número de temperatura."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        k = t / 0.5
        return (int(90 + 165 * k), int(150 + 105 * k), 255)
    k = (t - 0.5) / 0.5
    return (255, int(255 - 180 * k), int(255 - 180 * k))


# --- A. pantalla de impresión animada: ventilador que gira, barra con brillo, hotend calentando -----
def impresion_animada():
    ven = cargar('fan_state')
    cuadros = []
    N = 24
    for i in range(N):
        temp = 150 + int(60 * min(1, i / (N - 6)))
        caliente = temp >= 210
        sc = mv.pantalla_impresion(reloj_chico=True, pct=45, ext='', omitir=('fan_state',))
        d = ImageDraw.Draw(sc)
        # brillo que recorre la barra (solo sobre la parte llena)
        x = 210 + (i * 18) % 160
        for k in range(14):
            a = 1 - abs(k - 7) / 7
            d.line([(x + k, 41), (x + k - 6, 71)], fill=(int(205 + 50 * a), int(32 + 120 * a), int(40 + 120 * a)), width=1)
        d.text((340, 56), '45%', font=f(24), fill=(255, 255, 255), anchor='mm')
        # ventilador girando
        r = ven.rotate(-i * 40 % 360, resample=Image.BICUBIC)
        sc.paste(r, (350, 136), r)
        d.text((400, 158), '100%', font=f(16), fill=BLANCO, anchor='lm')
        # hotend: el número sube y cambia de color; titila hasta llegar
        col = color_temp((temp - 25) / 185)
        if not caliente and i % 2:
            col = tuple(int(c * 0.55) for c in col)
        d.text((256, 158), f'{temp}/210', font=f(16), fill=col, anchor='lm')
        cuadros.append(sc)
    gif('a1-impresion-animada.gif', cuadros, 110)


# --- B. arranque: el tornillo se imprime capa por capa ------------------------------------------
def arranque():
    import generar_assets as g
    cuadros = [g.logo(progreso=p) for p in [0.02 + 0.98 * k / 13 for k in range(14)]]
    cuadros += [cuadros[-1]] * 6
    gif('a2-arranque.gif', cuadros, 150)


# --- C. nivelación en vivo: la grilla se pinta mientras el BLTouch toca -------------------------
VAL = [[0.12, 0.08, 0.05, 0.07, 0.11], [0.06, 0.02, 0.00, 0.03, 0.08], [0.02, -0.01, -0.03, 0.00, 0.04],
       [0.00, -0.04, -0.06, -0.02, 0.03], [0.03, -0.02, -0.05, 0.01, 0.06]]


def col_nivel(v):
    a = abs(v)
    return (40, 140, 70) if a <= 0.05 else (190, 160, 30) if a <= 0.10 else (190, 40, 40)


def nivelacion_en_vivo():
    orden = []
    for fila in range(4, -1, -1):          # empieza adelante, en zigzag como el G29
        cols = range(5) if fila % 2 == 0 else range(4, -1, -1)
        orden += [(fila, c) for c in cols]
    cuadros = []
    for paso in range(len(orden) + 1):
        sc = fondo()
        d = ImageDraw.Draw(sc)
        d.text((3, 8), 'Nivelando la cama…', font=f(16), fill=BLANCO)
        mv.reloj(d)
        x0, y0, c = 20, 40, 44
        hechos = set(orden[:paso])
        for fila in range(5):
            for col in range(5):
                x, y = x0 + col * c, y0 + fila * c
                if (fila, col) in hechos:
                    v = VAL[fila][col]
                    d.rectangle([x, y, x + c - 3, y + c - 3], fill=col_nivel(v))
                    d.text((x + c / 2 - 1, y + c / 2 - 1), f'{v:+.2f}'.replace('.', ','), font=f(12), fill=(255, 255, 255), anchor='mm')
                else:
                    d.rectangle([x, y, x + c - 3, y + c - 3], outline=(80, 80, 80))
        if paso < len(orden):
            fila, col = orden[paso]
            x, y = x0 + col * c + c / 2 - 1, y0 + fila * c + c / 2 - 1
            d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=(255, 255, 255), width=3)
            d.line([(x, y - 14), (x, y - 8)], fill=(255, 255, 255), width=2)
        d.text((262, 52), f'Punto {min(paso + 1, 25)} de 25', font=f(18), fill=BLANCO)
        mv.barra(d, 262, 84, 200, 26, int(100 * paso / 25), 16)
        if paso == len(orden):
            d.text((262, 130), 'Diferencia máxima', font=f(15), fill=GRIS)
            d.text((262, 150), '0,18 mm', font=f(30), fill=BLANCO)
        cuadros.append(sc)
    cuadros += [cuadros[-1]] * 8
    gif('a3-nivelacion-en-vivo.gif', cuadros, 180)


# --- D. vista de la pieza en vivo: recorrido de la boquilla en la capa actual -------------------
def vista_en_vivo():
    # capa de ejemplo: contorno (2 vueltas) de una pieza redondeada + relleno en zigzag
    def contorno(m):
        pts = []
        for k in range(0, 361, 6):
            a = math.radians(k)
            r = 70 - m + 10 * math.cos(3 * a)
            pts.append((100 + r * math.cos(a), 100 + r * math.sin(a)))
        return pts
    tramos = [contorno(0), contorno(4)]          # cada tramo se dibuja sin unirlo al anterior (viajes)
    relleno = []
    for j, y in enumerate(range(50, 151, 7)):
        xs = [x for x in range(30, 171) if math.hypot(x - 100, y - 100) < 55]
        if xs:
            relleno += [(xs[0], y), (xs[-1], y)] if j % 2 == 0 else [(xs[-1], y), (xs[0], y)]
    tramos.append(relleno)
    camino = [(t, k) for t, tr in enumerate(tramos) for k in range(len(tr))]
    cuadros = []
    N = 22
    for i in range(N + 1):
        m = Image.new('RGB', (200, 200), (12, 12, 12))
        md = ImageDraw.Draw(m)
        md.line(contorno(0) + [contorno(0)[0]], fill=(60, 60, 60), width=1)   # capa anterior, gris
        hasta = int(len(camino) * i / N)
        if hasta > 1:
            t_fin, k_fin = camino[hasta - 1]
            for t in range(t_fin + 1):
                pts = tramos[t][:k_fin + 1] if t == t_fin else tramos[t]
                if len(pts) > 1:
                    md.line(pts, fill=(255, 255, 255), width=2)
            bx, by = tramos[t_fin][k_fin]
            md.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=ROJO)
        md.text((6, 184), 'Capa 57 · en vivo', font=f(13), fill=(170, 170, 170))
        sc = mv.pantalla_impresion(miniatura=m, reloj_chico=True)
        cuadros.append(sc)
    cuadros += [cuadros[-1]] * 4
    gif('a4-vista-en-vivo.gif', cuadros, 140)


# --- fijas ---------------------------------------------------------------------------------------
def siempre_encendida():
    sc = Image.new('RGB', (480, 320), (0, 0, 0))
    d = ImageDraw.Draw(sc)
    d.text((240, 40), '21:05', font=f(28), fill=(110, 110, 110), anchor='mm')
    d.text((240, 130), '45%', font=f(90), fill=(150, 30, 34), anchor='mm')
    d.rounded_rectangle([90, 190, 390, 202], 6, fill=(30, 30, 30))
    d.rounded_rectangle([90, 190, 90 + 135, 202], 6, fill=(110, 22, 26))
    d.text((240, 238), 'termina 23:40  ·  faltan 2 h 35 min', font=f(20), fill=(120, 120, 120), anchor='mm')
    d.text((240, 296), 'tocá la pantalla para volver', font=f(14), fill=(70, 70, 70), anchor='mm')
    return sc


def mensaje_en_pantalla():
    sc = mv.principal(reloj=True, iconos=True)
    capa = Image.new('RGBA', (480, 320), (0, 0, 0, 120))
    sc.paste(capa, (0, 0), capa)
    d = ImageDraw.Draw(sc)
    d.rounded_rectangle([50, 90, 430, 230], 10, fill=(26, 26, 26), outline=ROJO, width=2)
    mv.icono_avion(d, 82, 118, BLANCO)
    d.text((104, 118), 'Mensaje desde MagnAir', font=f(16), fill=GRIS, anchor='lm')
    d.text((240, 160), 'Cambiá el filamento a PETG negro', font=f(20), fill=BLANCO, anchor='mm')
    d.rounded_rectangle([170, 186, 310, 218], 8, fill=(26, 26, 26), outline=ROJO, width=2)
    d.text((240, 202), 'Entendido', font=f(16), fill=BLANCO, anchor='mm')
    return sc


def menu_con_reloj():
    sc = fondo()
    d = ImageDraw.Draw(sc)
    d.text((3, 5), 'Ajustes', font=f(16), fill=BLANCO)
    mv.reloj(d)
    items = [('preHeat', 'Precalentar'), ('extruct', 'Extrusor'), ('mov', 'Mover'), ('zero', 'Home'),
             ('leveling', 'Nivelar'), ('filamentchange', 'Filamento'), ('more', 'Más'), ('return', 'Atrás')]
    for i, (n, lab) in enumerate(items):
        x = 2 + (i % 4) * 119
        y = 36 + (i // 4) * 142
        pegar(sc, n, x, y)
        d.text((x + 58, y + 120), lab, font=f(16), fill=BLANCO, anchor='mm')
    return sc


def asistente_tornillos():
    sc = fondo()
    d = ImageDraw.Draw(sc)
    d.text((3, 8), 'Asistente de tornillos de la cama', font=f(16), fill=BLANCO)
    mv.reloj(d)
    d.rounded_rectangle([40, 50, 250, 260], 6, fill=(30, 30, 30), outline=(90, 90, 90), width=2)
    d.text((145, 272), 'frente', font=f(13), fill=GRIS, anchor='mm')
    datos = [((62, 72), 'OK', None), ((228, 72), '¼ vuelta', 'horario'), ((62, 238), '½ vuelta', 'antihorario'), ((228, 238), 'OK', None)]
    for (x, y), t, sentido in datos:
        ok = sentido is None
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(40, 140, 70) if ok else (190, 40, 40))
        d.text((x, y + (24 if y < 150 else -24)), t, font=f(16), fill=BLANCO, anchor='mm')
    d.text((270, 60), 'Atrás derecha', font=f(15), fill=GRIS)
    d.text((270, 80), '¼ vuelta horario', font=f(20), fill=BLANCO)
    d.text((270, 120), 'Adelante izquierda', font=f(15), fill=GRIS)
    d.text((270, 140), '½ vuelta antihorario', font=f(20), fill=BLANCO)
    d.text((270, 185), 'Las otras dos: bien', font=f(15), fill=(120, 200, 140))
    d.rounded_rectangle([270, 262, 370, 304], 8, fill=(26, 26, 26), outline=ROJO, width=2)
    d.text((320, 283), 'Medir otra vez', font=f(14), fill=BLANCO, anchor='mm')
    mv.boton_atras(d)
    return sc


def bloqueo():
    sc = mv.pantalla_impresion(reloj_chico=True)
    capa = Image.new('RGBA', (480, 320), (0, 0, 0, 200))
    sc.paste(capa, (0, 0), capa)
    d = ImageDraw.Draw(sc)
    # candado
    d.rounded_rectangle([222, 120, 258, 150], 4, fill=BLANCO)
    d.arc([226, 98, 254, 130], 180, 360, fill=BLANCO, width=4)
    d.ellipse([236, 130, 244, 138], fill=(20, 20, 20))
    d.text((240, 172), 'Pantalla bloqueada', font=f(22), fill=BLANCO, anchor='mm')
    d.rounded_rectangle([110, 200, 370, 240], 20, fill=(30, 30, 30), outline=(110, 110, 110), width=2)
    d.ellipse([114, 204, 146, 236], fill=ROJO)
    d.text((255, 220), 'deslizá para desbloquear  ›', font=f(15), fill=GRIS, anchor='mm')
    return sc


def cancelar_objetos():
    sc = fondo()
    d = ImageDraw.Draw(sc)
    d.text((3, 8), 'Cancelar una pieza (las demás siguen)', font=f(16), fill=BLANCO)
    mv.reloj(d)
    m = Image.new('RGB', (200, 200), (24, 24, 26))
    md = ImageDraw.Draw(m)
    piezas = [((25, 30, 85, 90), '1'), ((115, 30, 175, 90), '2'), ((25, 115, 85, 175), '3'), ((115, 115, 175, 175), '4')]
    for (x0, y0, x1, y1), n in piezas:
        cancelada = n == '3'
        md.rectangle([x0, y0, x1, y1], fill=(70, 30, 30) if cancelada else (200, 160, 30))
        md.text(((x0 + x1) / 2, (y0 + y1) / 2), n, font=f(20), fill=(255, 255, 255), anchor='mm')
        if cancelada:
            md.line([(x0, y0), (x1, y1)], fill=ROJO, width=3)
            md.line([(x0, y1), (x1, y0)], fill=ROJO, width=3)
    sc.paste(m, (2, 36))
    filas = [('1  soporte_A', False), ('2  soporte_B', False), ('3  tapa', True), ('4  clip', False)]
    for i, (t, canc) in enumerate(filas):
        y = 44 + i * 52
        d.text((214, y + 18), t, font=f(18), fill=(130, 130, 130) if canc else BLANCO, anchor='lm')
        d.rounded_rectangle([370, y, 470, y + 38], 8, fill=(26, 26, 26), outline=(90, 90, 90) if canc else ROJO, width=2)
        d.text((420, y + 19), 'cancelada' if canc else 'Cancelar', font=f(14), fill=(130, 130, 130) if canc else BLANCO, anchor='mm')
    mv.boton_atras(d)
    return sc


if __name__ == '__main__':
    impresion_animada()
    nivelacion_en_vivo()
    vista_en_vivo()
    arranque()
    fijas = [('b1-siempre-encendida', 'Siempre encendida mientras imprime (atenuada)', siempre_encendida()),
             ('b2-mensaje', 'Mensaje enviado desde MagnAir / Telegram', mensaje_en_pantalla()),
             ('b3-menu-con-hora', 'La hora chica en todas las pantallas', menu_con_reloj()),
             ('b4-asistente-tornillos', 'Asistente de tornillos (Marlin, con BLTouch)', asistente_tornillos()),
             ('b5-bloqueo', 'Bloqueo de pantalla mientras imprime', bloqueo()),
             ('b6-cancelar-piezas', 'Cancelar una pieza sin parar las demás', cancelar_objetos())]
    for n, _, im in fijas:
        im.save(os.path.join(OUT, n + '.png'))
    mv.hoja(fijas, 'hoja-ideas.png', OUT)
    print('animaciones y pantallas en', OUT)
