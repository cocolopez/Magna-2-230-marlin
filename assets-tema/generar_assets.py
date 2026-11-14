#!/usr/bin/env python3
"""
Genera el tema de íconos "Magna Negro/Rojo" para la pantalla MKS TFT35 (Marlin TFT_LVGL_UI).

Formato de cada archivo (verificado contra los assets originales de Makerbase):
  * Íconos: encabezado LVGL 6 de 4 bytes (cf=4 TRUE_COLOR, ancho, alto) + píxeles RGB565
    little-endian (ancho*alto*2 bytes) + 1 byte final 0x0A.
  * bmp_logo.bin: pantalla completa 480x320 RGB565 little-endian, SIN encabezado.
Los nombres y tamaños son los mismos que los originales, así que se reemplazan sin tocar el firmware.

Uso:  python3 generar_assets.py [carpeta_salida] [--preview]
      (por defecto ./assets ; --preview además genera PNG de muestra en ./preview)
Requiere Pillow y las fuentes DejaVu Sans y Noto Sans CJK (ideogramas de chino).
"""
import math, os, random, struct, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 4  # sobremuestreo para bordes suaves
BG = (26, 26, 26)        # = LV_COLOR_BACKGROUND de la UI MKS (0x1A1A1A)
WH = (238, 238, 238)     # blanco
RD = (214, 32, 39)       # rojo
DR = (120, 18, 22)       # rojo oscuro
GR = (95, 95, 95)        # gris
SW = 3.2                 # grosor de trazo (px reales)

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_C = None
# Versión de Marlin que se muestra en el arranque (se lee de MARLIN_VERSION: 2.1.3-b3 -> 2.1.3-BETA3)
def _version():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "MARLIN_VERSION")
    v = open(p).read().strip() if os.path.exists(p) else "2.1.3-b3"
    import re
    m = re.match(r"^(\d+\.\d+\.\d+(?:\.\d+)?)-b(\d+)$", v)
    return f"{m.group(1)}-BETA{m.group(2)}" if m else v.upper()
VERSION_MARLIN = _version()
for c in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
    if os.path.exists(c): FONT_C = c; break

# ------------------------------------------------------------------ lienzo
class Lienzo:
    def __init__(self, w, h, bg=BG):
        self.w, self.h = w, h
        self.im = Image.new("RGB", (w * S, h * S), bg)
        self.d = ImageDraw.Draw(self.im)
    def P(self, x, y): return (x * S, y * S)
    def linea(self, pts, col=WH, ancho=SW):
        pts = [self.P(*p) for p in pts]
        self.d.line(pts, fill=col, width=int(ancho * S), joint="curve")
        r = ancho * S / 2
        for p in (pts[0], pts[-1]):
            self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    def circulo(self, cx, cy, r, col=WH, ancho=SW, relleno=None):
        b = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
        self.d.ellipse(b, outline=col if ancho else None, width=int(ancho * S) if ancho else 0, fill=relleno)
    def arco(self, cx, cy, r, a0, a1, col=WH, ancho=SW):
        b = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
        self.d.arc(b, a0, a1, fill=col, width=int(ancho * S))
    def rect(self, x0, y0, x1, y1, col=WH, ancho=SW, radio=3, relleno=None):
        self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=radio * S,
                                 outline=col if ancho else None, width=int(ancho * S) if ancho else 0, fill=relleno)
    def poli(self, pts, col=None, relleno=WH):
        self.d.polygon([self.P(*p) for p in pts], fill=relleno, outline=col)
    def texto(self, x, y, s, tam, col=WH, fuente=FONT_B, ancla="mm"):
        f = ImageFont.truetype(fuente, int(tam * S))
        self.d.text(self.P(x, y), s, font=f, fill=col, anchor=ancla)
    def imagen(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)

def flecha(c, x0, y0, x1, y1, col=WH, punta=7, ancho=SW):
    ang = math.atan2(y1 - y0, x1 - x0)
    c.linea([(x0, y0), (x1 - math.cos(ang) * 2, y1 - math.sin(ang) * 2)], col, ancho)
    a1, a2 = ang + math.radians(150), ang - math.radians(150)
    c.poli([(x1, y1), (x1 + punta * math.cos(a1), y1 + punta * math.sin(a1)),
            (x1 + punta * math.cos(a2), y1 + punta * math.sin(a2))], relleno=col)

# ------------------------------------------------------------------ glifos (zona útil 117x100, centro 58.5,50)
CX, CY = 58.5, 50

def g_impresora(c):
    c.rect(30, 22, 87, 80, radio=4)
    c.linea([(30, 34), (87, 34)])
    c.poli([(52, 40), (65, 40), (61, 50), (56, 50)], relleno=RD)
    c.linea([(40, 70), (77, 70)], RD, 4)

def g_engranaje(c, cx=CX, cy=CY, r=22, col=WH):
    for i in range(8):
        a = math.radians(i * 45)
        c.linea([(cx + math.cos(a) * (r - 3), cy + math.sin(a) * (r - 3)), (cx + math.cos(a) * (r + 5), cy + math.sin(a) * (r + 5))], col, 7)
    c.circulo(cx, cy, r - 2, col, SW, relleno=BG)
    c.circulo(cx, cy, 7, RD, SW)

def g_llave(c):
    """Ajustes: llave fija y destornillador cruzados."""
    # destornillador (de abajo a la derecha hacia arriba a la izquierda)
    c.linea([(80, 76), (68, 64)], RD, 10)                 # mango rojo
    c.linea([(66, 62), (42, 38)], WH, 4)                  # vástago
    c.poli([(42, 34), (38, 38), (34, 30), (38, 26)], relleno=WH)   # punta
    # llave fija (de abajo a la izquierda hacia arriba a la derecha)
    c.linea([(36, 78), (64, 50)], WH, 8)                  # mango
    c.circulo(70, 44, 13, None, 0, relleno=WH)            # cabeza
    c.poli([(70, 44), (88, 36), (78, 26)], relleno=BG)    # boca de la llave (hueco)
    c.circulo(70, 44, 4.5, None, 0, relleno=BG)
    c.circulo(36, 78, 4.2, None, 0, relleno=BG)           # agujero del mango

def g_mas_opciones(c):
    for i, x in enumerate((38, 58.5, 79)):
        c.circulo(x, CY, 5.5, None, 0, relleno=RD if i == 1 else WH)

def g_termometro(c, cx=CX, cy=CY, nivel=0.6, olas=False):
    c.rect(cx - 6, cy - 28, cx + 6, cy + 10, radio=6)
    c.circulo(cx, cy + 16, 11, WH, SW, relleno=BG)
    c.linea([(cx, cy + 14), (cx, cy + 10 - 34 * nivel)], RD, 5)
    c.circulo(cx, cy + 16, 6, None, 0, relleno=RD)
    if olas:
        for dx in (-22, 22):
            x = cx + dx
            c.linea([(x, cy - 18), (x + 4, cy - 12), (x - 4, cy - 4), (x, cy + 2)], RD if dx > 0 else WH, 2.5)

def g_cruz_flechas(c, centro=RD):
    for (dx, dy) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        flecha(c, CX + dx * 7, CY + dy * 7, CX + dx * 26, CY + dy * 26, WH, 8)
    c.circulo(CX, CY, 5, None, 0, relleno=centro)

def g_casa(c, letra=None):
    c.linea([(34, 50), (58.5, 27), (83, 50)], WH, 4)
    c.linea([(40, 46), (40, 76), (77, 76), (77, 46)])
    if letra: c.texto(58.5, 61, letra, 20, RD)
    else: c.rect(53, 60, 64, 76, RD, 0, radio=1, relleno=RD)

def g_cama(c, puntos=None, activo=None):
    # cama vista de arriba con puntos de nivelación
    c.rect(30, 26, 87, 76, radio=4)
    pos = [(39, 67), (78, 67), (78, 35), (39, 35), (58.5, 51)]
    for i, (x, y) in enumerate(pos):
        if puntos is None or i < puntos:
            sel = (activo == i)
            c.circulo(x, y, 6 if sel else 3.2, RD if sel else WH, 0 if not sel else SW, relleno=RD if sel else GR if activo is not None else WH)
    if activo is not None: c.texto(58.5, 51, str(activo + 1), 13, WH) if activo != 4 else None

def g_nivelacion(c):
    c.poli([(28, 64), (89, 64), (82, 74), (35, 74)], col=None, relleno=WH)
    c.rect(38, 36, 79, 50, radio=7)
    c.circulo(58.5, 43, 3.5, None, 0, relleno=RD)
    c.linea([(58.5, 52), (58.5, 60)], GR, 2)

def g_bobina(c):
    c.circulo(CX, CY, 24)
    c.circulo(CX, CY, 9, RD, SW)
    c.arco(CX, CY, 16, 200, 340, GR, 2)
    c.linea([(CX + 24, CY + 4), (CX + 30, CY + 26)], RD, 3)

def g_boquilla(c, cx=CX, cy=CY, gota=True, num=None):
    c.rect(cx - 16, cy - 24, cx + 16, cy - 2, radio=3)
    c.poli([(cx - 10, cy), (cx + 10, cy), (cx + 3, cy + 12), (cx - 3, cy + 12)], relleno=WH)
    if gota:
        c.poli([(cx, cy + 16), (cx - 5, cy + 25), (cx + 5, cy + 25)], relleno=RD)
        c.circulo(cx, cy + 26, 5, None, 0, relleno=RD)
    if num: c.texto(cx, cy - 13, num, 15, RD)

def g_ventilador(c, cx=CX, cy=CY, r=24, col=WH):
    c.circulo(cx, cy, r + 3, col, SW)
    for i in range(3):
        a = math.radians(i * 120 - 90)
        pts = []
        for t in range(0, 11):
            aa = a + math.radians(t * 7)
            rr = 5 + (r - 6) * math.sin(math.radians(t * 18))
            pts.append((cx + math.cos(aa) * rr, cy + math.sin(aa) * rr))
        pts.append((cx, cy))
        c.poli(pts, relleno=col)
    c.circulo(cx, cy, 5, None, 0, relleno=RD)

def g_velocimetro(c, aguja=0.5, cx=CX, cy=CY + 8, r=26):
    c.arco(cx, cy, r, 150, 390)
    c.arco(cx, cy, r, 150 + 240 * 0.75, 390, RD, SW)
    for i in range(5):
        a = math.radians(150 + i * 60)
        c.linea([(cx + math.cos(a) * (r - 8), cy + math.sin(a) * (r - 8)), (cx + math.cos(a) * (r - 4), cy + math.sin(a) * (r - 4))], GR, 2)
    a = math.radians(150 + 240 * aguja)
    c.linea([(cx, cy), (cx + math.cos(a) * (r - 6), cy + math.sin(a) * (r - 6))], RD, 3.5)
    c.circulo(cx, cy, 4, None, 0, relleno=WH)

def g_documento(c):
    c.poli([(38, 22), (68, 22), (80, 34), (80, 80), (38, 80)], col=None, relleno=WH)
    c.poli([(41, 25), (66, 25), (77, 36), (77, 77), (41, 77)], relleno=BG)
    c.linea([(66, 23), (66, 35), (78, 35)], WH, 2.5)
    for y, col in ((48, RD), (57, WH), (66, WH)):
        c.linea([(47, y), (71 if col == WH else 64, y)], col, 2.5)

def g_carpeta(c):
    c.poli([(30, 30), (50, 30), (55, 36), (87, 36), (87, 76), (30, 76)], relleno=WH)
    c.poli([(33, 41), (84, 41), (84, 73), (33, 73)], relleno=BG)
    c.linea([(33, 41), (84, 41)], RD, 3)

def g_sd(c):
    c.poli([(42, 22), (70, 22), (78, 30), (78, 80), (42, 80)], relleno=WH)
    c.poli([(45, 25), (69, 25), (75, 31), (75, 77), (45, 77)], relleno=BG)
    for x in (51, 57, 63, 69):
        c.linea([(x, 31), (x, 41)], RD if x == 51 else WH, 2.6)
    c.texto(60, 62, "SD", 12, WH)

def g_usb(c):
    c.rect(46, 22, 72, 36, radio=2)
    c.rect(52, 26, 56, 30, None, 0, radio=0, relleno=RD); c.rect(62, 26, 66, 30, None, 0, radio=0, relleno=RD)
    c.rect(41, 36, 77, 80, radio=5)
    c.linea([(52, 60), (66, 60)], GR, 2.5)

def g_wifi(c):
    for r, col in ((30, WH), (20, WH), (10, RD)):
        c.arco(CX, CY + 18, r, 220, 320, col, SW + 0.5)
    c.circulo(CX, CY + 18, 4, None, 0, relleno=RD)

def g_nube(c):
    c.d.ellipse([34 * S, 44 * S, 56 * S, 70 * S], outline=WH, width=int(SW * S))
    c.circulo(64, 46, 16)
    c.circulo(80, 58, 11)
    c.rect(40, 56, 84, 70, None, 0, radio=0, relleno=BG)
    c.linea([(44, 70), (82, 70)])
    flecha(c, 61, 66, 61, 46, RD, 7)

def g_info(c):
    c.circulo(CX, CY, 25)
    c.circulo(CX, CY - 12, 3.4, None, 0, relleno=RD)
    c.linea([(CX, CY - 3), (CX, CY + 14)], WH, 5)

def g_globo(c):
    c.circulo(CX, CY, 25)
    c.d.ellipse([(CX - 11) * S, (CY - 25) * S, (CX + 11) * S, (CY + 25) * S], outline=WH, width=int(2.5 * S))
    c.linea([(CX - 25, CY), (CX + 25, CY)], RD, 2.5)
    c.arco(CX, CY + 30, 34, 225, 315, WH, 2); c.arco(CX, CY - 30, 34, 45, 135, WH, 2)

def g_deslizadores(c):
    for i, (y, k) in enumerate(((32, 70), (50, 44), (68, 60))):
        c.linea([(32, y), (85, y)], GR if i != 1 else WH, 3)
        c.circulo(k, y, 6, RD if i == 1 else WH, SW, relleno=BG)

def g_guardar(c):
    c.poli([(34, 24), (76, 24), (84, 32), (84, 78), (34, 78)], relleno=WH)
    c.poli([(37, 27), (75, 27), (81, 33), (81, 75), (37, 75)], relleno=BG)
    c.rect(44, 27, 72, 42, radio=1); c.rect(63, 30, 68, 39, None, 0, radio=0, relleno=RD)
    c.rect(44, 53, 74, 75, GR, 2.5, radio=1)

def g_rayo(c):
    c.poli([(64, 20), (40, 54), (56, 54), (50, 82), (78, 44), (61, 44), (70, 20)], relleno=RD)

def g_custom(c, n):
    c.rect(34, 26, 84, 76, radio=8)
    c.texto(52, 51, "C", 22, WH); c.texto(68, 53, str(n), 18, RD)

def g_calibrar(c, que):
    """Calibrar hotend o cama: el objeto y una curva de temperatura que sube y se estabiliza."""
    c.linea([(56, 24), (56, 78), (94, 78)], GR, 2)                       # ejes del gráfico
    pts = [(56 + t, 72 - 40 * (1 - math.exp(-t / 8.0))) for t in range(0, 37, 2)]
    c.linea(pts, RD, 3.5)
    c.linea([(56, 33), (94, 33)], WH, 1.5)                               # temperatura objetivo
    if que == 'hotend':
        g_boquilla(c, cx=34, cy=46, gota=False)
    else:
        c.poli([(14, 66), (50, 66), (46, 76), (18, 76)], relleno=WH)
        for x in (24, 32, 40):
            c.linea([(x, 58), (x + 3, 51), (x - 3, 44), (x, 37)], RD if x == 32 else WH, 2.5)

def g_dos_en_uno_flecha(c, n, sube):
    """Hotend 2 en 1 con la rama del filamento n en rojo y una flecha: sube = estacionar, baja = cargar."""
    izq = (n == 1)
    c.linea([(44, 22), (58.5, 48)], RD if izq else WH, 4 if izq else 2.5)
    c.linea([(73, 22), (58.5, 48)], WH if izq else RD, 2.5 if izq else 4)
    c.linea([(58.5, 48), (58.5, 62)], WH, 4)
    c.poli([(50, 62), (67, 62), (62, 74), (55, 74)], relleno=WH)
    x = 26 if izq else 91
    if sube: flecha(c, x, 66, x, 22, RD, 9, 4)
    else: flecha(c, x, 22, x, 66, RD, 9, 4)
    c.texto(x, 78, str(n), 14, WH)

def g_volver(c):
    """Volver: flecha en U, entera dentro del cuadro (punta grande a la izquierda)."""
    cx, cy, r = 64, 51, 19
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 91, 6)]
    c.linea([(44, cy - r)] + pts, WH, 5)                  # recta superior + curva
    c.poli([(30, cy - r), (46, cy - r - 10), (46, cy - r + 10)], relleno=WH)   # punta
    c.linea([(cx, cy + r), (52, cy + r)], RD, 5)          # cola roja

def g_masmenos(c, signo):
    c.circulo(CX, CY, 25)
    c.linea([(CX - 12, CY), (CX + 12, CY)], RD, 5)
    if signo == "+": c.linea([(CX, CY - 12), (CX, CY + 12)], RD, 5)

def g_eje(c, eje, signo):
    c.texto(48, 50, eje, 34, WH)
    col = RD
    if signo == "+":
        c.linea([(72, 50), (88, 50)], col, 5); c.linea([(80, 42), (80, 58)], col, 5)
    else:
        c.linea([(72, 50), (88, 50)], col, 5)

def g_valor(c, valor, unidad, regla=True):
    if regla:
        c.linea([(30, 70), (87, 70)], GR, 2.5)
        for i in range(8):
            x = 30 + i * 57 / 7
            c.linea([(x, 70), (x, 64 if i % 2 else 60)], GR, 2)
    if regla:
        c.texto(58.5, 42, valor, 24 if len(valor) <= 3 else 19, WH)
        c.texto(58.5, 84, unidad, 11, RD, FONT_B)
    else:
        c.texto(58.5, 46, valor, 32, WH)
        c.texto(58.5, 74, unidad, 15, RD, FONT_B)

def g_babystep(c, valor):
    c.texto(40, 40, "Z", 30, WH)
    flecha(c, 72, 50, 72, 26, RD, 8); flecha(c, 72, 50, 72, 74, RD, 8)
    c.texto(58.5, 82, valor, 12, WH, FONT_B)

def g_apagado(c, letra=None):
    c.arco(CX, CY + 3, 24, 300, 600, WH, 4)
    c.linea([(CX, CY - 26), (CX, CY + 2)], RD, 5)
    if letra: c.texto(CX, CY + 15, letra, 13, WH)

def g_idioma(c, txt):
    if len(txt) == 1 and FONT_C:
        c.texto(58.5, 50, txt, 42, WH, FONT_C)
    else:
        c.texto(58.5, 50, txt, 34, WH)
    c.linea([(44, 76), (73, 76)], RD, 4)

def g_cama_caliente(c):
    c.poli([(28, 64), (89, 64), (82, 76), (35, 76)], relleno=WH)
    for i, x in enumerate((44, 58.5, 73)):
        c.linea([(x, 56), (x + 5, 47), (x - 5, 38), (x, 29)], RD if i == 1 else WH, 3)

def g_cargar(c, entra=True):
    g_boquilla(c, cx=58.5, cy=58, gota=False)
    if entra: flecha(c, 58.5, 8, 58.5, 30, RD, 9, 4)
    else: flecha(c, 58.5, 30, 58.5, 8, RD, 9, 4)

def g_dos_en_uno(c):
    c.linea([(40, 22), (58.5, 50)], WH, 4); c.linea([(77, 22), (58.5, 50)], RD, 4)
    c.linea([(58.5, 50), (58.5, 66)], WH, 4)
    c.poli([(50, 66), (67, 66), (62, 78), (55, 78)], relleno=WH)

def g_laser(c):
    c.linea([(40, 26), (66, 66)], RD, 3)
    c.rect(32, 18, 50, 30, radio=2)
    c.linea([(36, 76), (86, 76)], WH, 3); c.circulo(66, 68, 5, None, 0, relleno=RD)

def g_lampara(c, prendida):
    c.circulo(CX, CY - 6, 18, WH, SW, relleno=RD if prendida else BG)
    c.rect(CX - 9, CY + 14, CX + 9, CY + 24, radio=2)
    if prendida:
        for a in (200, 240, 300, 340):
            r = math.radians(a)
            c.linea([(CX + math.cos(r) * 24, CY - 6 + math.sin(r) * 24), (CX + math.cos(r) * 31, CY - 6 + math.sin(r) * 31)], WH, 2.5)

def g_pin(c):
    c.circulo(CX, CY - 8, 16, WH, SW)
    c.poli([(CX - 12, CY + 2), (CX + 12, CY + 2), (CX, CY + 28)], relleno=WH)
    c.circulo(CX, CY - 8, 6, None, 0, relleno=RD)

def g_x_mode(c):
    c.texto(58.5, 50, "X", 40, WH); c.linea([(40, 76), (77, 76)], RD, 4)

def g_tijera(c):
    c.linea([(40, 28), (76, 72)], WH, 4); c.linea([(76, 28), (40, 72)], RD, 4)
    c.circulo(40, 72, 7); c.circulo(76, 72, 7, RD)

# ------------------------------------------------------------------ catálogo 117x140
def con_valor(v, u): return lambda c: g_valor(c, v, u)
ICONOS = {
    "printing": g_impresora, "Print_ui": g_impresora,
    "set": g_engranaje, "tool": g_llave, "more": g_mas_opciones,
    "preHeat": lambda c: g_termometro(c, olas=True), "temp": g_termometro,
    "mov": g_cruz_flechas, "mov_sel": g_cruz_flechas, "move_opr": g_cruz_flechas,
    "mov_changeSpeed": lambda c: (g_cruz_flechas(c), g_velocimetro(c, 0.8, 84, 80, 11)),
    "zero": g_casa, "zeroAll": g_casa,
    "zeroX": lambda c: g_casa(c, "X"), "zeroY": lambda c: g_casa(c, "Y"), "zeroZ": lambda c: g_casa(c, "Z"),
    "leveling": g_nivelacion,
    **{f"leveling{i}": (lambda i: lambda c: g_cama(c, activo=i - 1))(i) for i in range(1, 6)},
    "filamentchange": g_bobina,
    "extruct": g_boquilla, "extruct_sel": g_boquilla, "extrude_opr": g_boquilla,
    "extru1": lambda c: g_boquilla(c, num="1"), "extru2": lambda c: g_boquilla(c, num="2"),
    "in": lambda c: g_cargar(c, True), "out": lambda c: g_cargar(c, False),
    "fan": g_ventilador,
    "speed0": lambda c: (g_ventilador(c, cx=58.5, cy=40, r=16), c.texto(58.5, 80, "0%", 13, RD)),
    "speed127": lambda c: (g_ventilador(c, cx=58.5, cy=40, r=16), c.texto(58.5, 80, "50%", 13, RD)),
    "speed255": lambda c: (g_ventilador(c, cx=58.5, cy=40, r=16), c.texto(58.5, 80, "100%", 13, RD)),
    "speed": lambda c: g_velocimetro(c, 0.55),
    "speed_slow": lambda c: g_velocimetro(c, 0.15), "speed_normal": lambda c: g_velocimetro(c, 0.5),
    "speed_high": lambda c: g_velocimetro(c, 0.9),
    "speed_extruct": lambda c: (g_velocimetro(c, 0.6), c.texto(58.5, 84, "E", 12, RD)),
    "file": g_documento, "dir": g_carpeta,
    "sd": g_sd, "sd_sel": g_sd, "lcd_sd": g_sd, "lcd_sd_sel": g_sd,
    "usb_disk": g_usb, "usb_disk_sel": g_usb,
    "wifi": g_wifi, "cloud": g_nube, "about": g_info, "language": g_globo,
    "machine_para": g_deslizadores, "eeprom_settings": g_guardar, "function1": g_rayo,
    # botones de Ajustes > Más (CUSTOM_MENU_MAIN en Configuration_adv.h)
    "custom1": lambda c: g_calibrar(c, 'hotend'),
    "custom2": lambda c: g_calibrar(c, 'cama'),
    "custom3": lambda c: g_dos_en_uno_flecha(c, 1, True),
    "custom4": lambda c: g_dos_en_uno_flecha(c, 2, True),
    "custom5": lambda c: g_dos_en_uno_flecha(c, 1, False),
    "custom6": lambda c: g_dos_en_uno_flecha(c, 2, False),
    "custom7": lambda c: g_custom(c, 7),
    "return": g_volver,
    "Add": lambda c: g_masmenos(c, "+"), "Dec": lambda c: g_masmenos(c, "-"),
    "xAdd": lambda c: g_eje(c, "X", "+"), "xDec": lambda c: g_eje(c, "X", "-"),
    "yAdd": lambda c: g_eje(c, "Y", "+"), "yDec": lambda c: g_eje(c, "Y", "-"),
    "zAdd": lambda c: g_eje(c, "Z", "+"), "zDec": lambda c: g_eje(c, "Z", "-"),
    "step_move0_1": con_valor("0.1", "mm"), "step_move1": con_valor("1", "mm"), "step_move10": con_valor("10", "mm"),
    "step_move0_01": con_valor("0.01", "mm"), "step_move0_05": con_valor("0.05", "mm"),
    "step1_mm": con_valor("1", "mm"), "step5_mm": con_valor("5", "mm"), "step10_mm": con_valor("10", "mm"),
    "step1_degree": lambda c: g_valor(c, "1", "°C", False), "step5_degree": lambda c: g_valor(c, "5", "°C", False),
    "step10_degree": lambda c: g_valor(c, "10", "°C", False),
    "step1_percent": lambda c: g_valor(c, "1", "%", False), "step5_percent": lambda c: g_valor(c, "5", "%", False),
    "step10_percent": lambda c: g_valor(c, "10", "%", False),
    "baby_move0_01": lambda c: g_babystep(c, "0.01"), "baby_move0_05": lambda c: g_babystep(c, "0.05"),
    "baby_move0_1": lambda c: g_babystep(c, "0.1"),
    "auto_off": lambda c: g_apagado(c, "A"), "manual_off": lambda c: g_apagado(c, "M"), "Power": g_apagado,
    "english": lambda c: g_idioma(c, "EN"), "english_sel": lambda c: g_idioma(c, "EN"),
    "spanish": lambda c: g_idioma(c, "ES"), "spanish_sel": lambda c: g_idioma(c, "ES"),
    "french": lambda c: g_idioma(c, "FR"), "french_sel": lambda c: g_idioma(c, "FR"),
    "italy": lambda c: g_idioma(c, "IT"), "italy_sel": lambda c: g_idioma(c, "IT"),
    "russian": lambda c: g_idioma(c, "RU"), "russian_sel": lambda c: g_idioma(c, "RU"),
    "simplified_cn": lambda c: g_idioma(c, "简"), "simplified_cn_sel": lambda c: g_idioma(c, "简"),
    "traditional_cn": lambda c: g_idioma(c, "繁"), "traditional_cn_sel": lambda c: g_idioma(c, "繁"),
    "bed": g_cama_caliente, "twoInOneSet": g_dos_en_uno,
    "Laser_ui": g_laser, "engraving": g_laser, "Cut_times": g_tijera,
    "Light_open": lambda c: g_lampara(c, True), "Light_close": lambda c: g_lampara(c, False),
    "Mamual": lambda c: g_apagado(c, "M"), "Position": g_pin, "X_mode": g_x_mode,
}

def icono_117(nombre):
    c = Lienzo(117, 140)
    if nombre.endswith("_sel"):          # franja de seleccionado: filas 100-139, igual que el original
        c.rect(0, 100, 117, 140, None, 0, radio=0, relleno=DR)
        c.linea([(0, 101), (117, 101)], RD, 2)
    ICONOS[nombre](c)
    return c.imagen()

# ------------------------------------------------------------------ otros tamaños
def estado_45(nombre):
    c = Lienzo(45, 45)
    k = 0.5
    def esc(f):  # dibuja un glifo de 117x100 achicado
        big = Lienzo(117, 100); f(big); im = big.im.resize((117 * S // 2, 100 * S // 2), Image.LANCZOS)
        c.im.paste(im, (int((45 - 58.5) / 2 * S), int((45 - 50) / 2 * S)))
    m = {"bed_state": g_cama_caliente, "ext1_state": lambda b: g_boquilla(b, num="1"), "ext2_state": lambda b: g_boquilla(b, num="2"),
         "fan_state": g_ventilador, "time_state": None, "zpos_state": None, "speed_state": lambda b: g_velocimetro(b, 0.6),
         "power_state": g_apagado, "init_state": g_impresora, "times_state": None}
    f = m[nombre]
    if f: esc(f)
    elif nombre == "time_state":
        c.circulo(22.5, 22.5, 15, WH, 2.4); c.linea([(22.5, 22.5), (22.5, 13)], WH, 2.4); c.linea([(22.5, 22.5), (29, 26)], RD, 2.4)
    elif nombre == "times_state":
        c.circulo(22.5, 22.5, 15, WH, 2.4); flecha(c, 22.5, 22.5, 22.5, 11, RD, 5, 2.4); c.linea([(22.5, 22.5), (30, 22.5)], WH, 2.4)
    elif nombre == "zpos_state":
        c.circulo(22.5, 22.5, 15, WH, 2.4); c.texto(22.5, 23, "Z", 15, RD)
    return c.imagen()

def boton_150(nombre):
    c = Lienzo(150, 80)
    c.rect(15, 14, 134, 65, RD if nombre == "stop" else GR, 1.6, radio=6)
    x, y = 42, 39.5
    if nombre == "pause":
        c.rect(x - 7, y - 9, x - 2, y + 9, None, 0, radio=1, relleno=WH); c.rect(x + 3, y - 9, x + 8, y + 9, None, 0, radio=1, relleno=WH)
    elif nombre == "resume":
        c.poli([(x - 6, y - 10), (x - 6, y + 10), (x + 10, y)], relleno=RD)
    elif nombre == "stop":
        c.rect(x - 8, y - 8, x + 8, y + 8, None, 0, radio=2, relleno=RD)
    elif nombre == "operate":
        g = Lienzo(117, 100); g_deslizadores(g)
        im = g.im.resize((117 * S * 2 // 5, 100 * S * 2 // 5), Image.LANCZOS)
        c.im.paste(im, (int((x - 23.4) * S), int((y - 20) * S)))
    return c.imagen()

def flecha_92(nombre):
    c = Lienzo(117, 92)
    if nombre == "back":
        g_volver_c = Lienzo(117, 100); g_volver(g_volver_c)
        c.im.paste(g_volver_c.im.crop((0, 4 * S, 117 * S, 96 * S)), (0, 0))
    elif nombre == "pageUp":
        c.poli([(58.5, 26), (84, 62), (33, 62)], relleno=WH); c.linea([(40, 70), (77, 70)], RD, 4)
    elif nombre == "pageDown":
        c.poli([(33, 30), (84, 30), (58.5, 66)], relleno=WH); c.linea([(40, 22), (77, 22)], RD, 4)
    return c.imagen()

def chico(nombre):
    if nombre == "back70x40":
        c = Lienzo(70, 40, DR); c.linea([(0, 39), (70, 39)], RD, 2); return c.imagen()
    if nombre == "value_blank":
        c = Lienzo(70, 28, DR); return c.imagen()
    if nombre == "blank_sel":
        c = Lienzo(70, 28); c.rect(1, 1, 69, 27, WH, 1.5, radio=2); return c.imagen()
    if nombre in ("enable", "disable"):
        c = Lienzo(90, 30); on = nombre == "enable"
        c.rect(4, 4, 86, 26, WH if on else GR, 1.8, radio=11, relleno=DR if on else BG)
        c.circulo(74 if on else 16, 15, 8, None, 0, relleno=WH if on else GR); return c.imagen()
    if nombre == "arrow":
        c = Lienzo(10, 17); c.linea([(2.5, 2.5), (7.5, 8.5), (2.5, 14.5)], RD, 2); return c.imagen()
    raise KeyError(nombre)

# ------------------------------------------------------------------ logo de arranque 480x320
def pez_espada_mask(w, h):
    """Silueta propia de un pez espada saltando (cuerpo arqueado), con la nariz arriba.
    Se define recto en unidades propias y se curva por código. Solo el pez, sin base."""
    cuerpo = [(0, 40), (52, 37.5), (58, 34), (72, 26), (95, 20), (130, 22), (155, 30), (171, 37),
              (171, 42), (150, 48), (120, 55), (90, 57), (68, 53), (58, 46), (52, 42.5)]
    dorsal = [(84, 22), (90, 2), (97, 1), (99, 6), (108, 21)]
    cola = [(168, 37), (190, 9), (197, 11), (183, 39.5), (197, 68), (190, 70), (168, 42)]
    pectoral = [(74, 51), (100, 67), (93, 55), (86, 50)]
    anal = [(128, 54), (138, 62), (142, 51)]
    def densificar(pol, paso=2.0):
        out = []
        for (x0, y0), (x1, y1) in zip(pol, pol[1:] + pol[:1]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / paso))
            out += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
        return out
    R, y0, giro = 135.0, 40.0, math.radians(58)        # radio de la curva y giro (nariz hacia arriba)
    def curvar(x, y):
        t = (x - 100) / R; r = R - (y - y0)              # arco convexo hacia arriba (salto)
        px, py = math.sin(t) * r, R - math.cos(t) * r
        return (px * math.cos(giro) - py * math.sin(giro), px * math.sin(giro) + py * math.cos(giro))
    partes = [[curvar(*p) for p in densificar(pol)] for pol in (cuerpo, dorsal, cola, pectoral, anal)]
    ojo = curvar(63, 36)
    todos = [p for pa in partes for p in pa]
    minx, maxx = min(p[0] for p in todos), max(p[0] for p in todos)
    miny, maxy = min(p[1] for p in todos), max(p[1] for p in todos)
    # encajar en la columna derecha (x 285-472, y 12-272): ocupa todo el lado derecho, solo el pez
    esc = min(187 / (maxx - minx), 260 / (maxy - miny))
    ox = 472 - maxx * esc; oy = 272 - maxy * esc
    T = lambda pts: [((ox + x * esc) * S, (oy + y * esc) * S) for x, y in pts]
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    for pa in partes: md.polygon(T(pa), fill=255)
    ex, ey = ox + ojo[0] * esc, oy + ojo[1] * esc
    md.ellipse([(ex - 2.3) * S, (ey - 2.3) * S, (ex + 2.3) * S, (ey + 2.3) * S], fill=0)
    return m

def _perfil_simetrico(w, h, perfil, cx=385, y_base=274, alto=250):
    """Silueta simétrica de revolución vista de frente: perfil = [(t 0..1 desde la base, radio px)]."""
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    der = [((cx + r) * S, (y_base - t * alto) * S) for t, r in perfil]
    izq = [((cx - r) * S, (y_base - t * alto) * S) for t, r in reversed(perfil)]
    md.polygon(der + izq, fill=255)
    return m, md

def torre_mask(w, h):
    perfil = [(0, 62), (0.05, 62), (0.07, 52), (0.10, 52), (0.13, 44), (0.70, 34), (0.73, 46), (0.80, 46), (0.80, 50), (0.95, 50), (0.95, 0)]
    m, md = _perfil_simetrico(w, h, perfil)
    for i in range(4):                                  # almenas
        x = 385 - 50 + i * 30
        md.rectangle([x * S, (274 - 250) * S, (x + 18) * S, (274 - 0.95 * 250) * S], fill=255)
    md.rectangle([377 * S, 120 * S, 393 * S, 150 * S], fill=0)   # ventana
    return m

def cohete_mask(w, h):
    perfil = [(0, 26), (0.08, 30), (0.55, 34), (0.70, 31), (0.82, 22), (0.92, 11), (1.0, 0)]
    m, md = _perfil_simetrico(w, h, perfil, alto=240)
    T = lambda pts: [(x * S, y * S) for x, y in pts]
    md.polygon(T([(351, 274), (330, 274), (330, 250), (352, 200)]), fill=255)      # aletas
    md.polygon(T([(419, 274), (440, 274), (440, 250), (418, 200)]), fill=255)
    md.ellipse([371 * S, 120 * S, 399 * S, 148 * S], fill=0)                          # ventanilla
    md.ellipse([377 * S, 126 * S, 393 * S, 142 * S], fill=255)
    return m

def faro_mask(w, h):
    perfil = [(0, 50), (0.04, 50), (0.04, 40), (0.62, 25), (0.62, 38), (0.65, 38), (0.65, 22), (0.80, 22), (0.80, 30), (0.84, 24), (0.94, 6), (1.0, 3)]
    m, md = _perfil_simetrico(w, h, perfil, alto=255)
    for y in (150, 200):                                # ventanas
        md.rectangle([380 * S, y * S, 390 * S, (y + 14) * S], fill=0)
    md.rectangle([372 * S, 64 * S, 398 * S, 90 * S], fill=0)   # linterna (vidrio)
    md.rectangle([383 * S, 64 * S, 387 * S, 90 * S], fill=255)
    return m

def jarron_mask(w, h):
    perfil = [(t / 40, 30 + 32 * math.sin(t / 40 * math.pi * 1.15 + 0.35) + 5 * math.sin(t / 40 * 14)) for t in range(41)]
    perfil = [(0, 0)] + perfil + [(1.0, 0)]
    m, _ = _perfil_simetrico(w, h, perfil, alto=245)
    return m

def engranaje_mask(w, h):
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    cx, cy, r = 376, 160, 94
    pts = []
    for i in range(16 * 4):
        a = 2 * math.pi * i / 64
        rr = r if (i % 4) in (0, 1) else r - 16
        pts.append(((cx + math.cos(a) * rr) * S, (cy + math.sin(a) * rr) * S))
    md.polygon(pts, fill=255)
    md.ellipse([(cx - 30) * S, (cy - 30) * S, (cx + 30) * S, (cy + 30) * S], fill=0)
    for k in range(6):                                  # alivianados
        a = 2 * math.pi * k / 6 + 0.3
        x, y = cx + math.cos(a) * 52, cy + math.sin(a) * 52
        md.ellipse([(x - 9) * S, (y - 9) * S, (x + 9) * S, (y + 9) * S], fill=0)
    return m

def diamante_mask(w, h):
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    T = lambda pts: [(x * S, y * S) for x, y in pts]
    md.polygon(T([(385, 274), (300, 110), (330, 40), (440, 40), (470, 110)]), fill=255)
    for a, b in (((300, 110), (470, 110)), ((330, 40), (355, 110)), ((440, 40), (415, 110)), ((385, 40), (355, 110)), ((385, 40), (415, 110)),
                 ((355, 110), (385, 274)), ((415, 110), (385, 274))):
        md.line(T([a, b]), fill=0, width=int(2.2 * S))   # facetas
    return m

def pino_mask(w, h):
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    T = lambda pts: [(x * S, y * S) for x, y in pts]
    for (y0, y1, ancho) in ((14, 110, 52), (60, 170, 72), (115, 236, 92)):
        md.polygon(T([(385, y0), (385 - ancho, y1), (385 + ancho, y1)]), fill=255)
    md.rectangle([372 * S, 236 * S, 398 * S, 262 * S], fill=255)
    md.rectangle([350 * S, 262 * S, 420 * S, 274 * S], fill=255)
    return m

def montana_mask(w, h):
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    T = lambda pts: [(x * S, y * S) for x, y in pts]
    md.polygon(T([(290, 274), (348, 120), (372, 150), (410, 30), (476, 274)]), fill=255)
    md.polygon(T([(392, 86), (410, 30), (428, 86), (418, 78), (410, 92), (400, 78)]), fill=0)   # nieve (hueco)
    md.polygon(T([(396, 82), (410, 40), (424, 82), (418, 76), (410, 88), (402, 76)]), fill=255)
    return m

def tornillo_mask(w, h):
    """Tornillo de cabeza hexagonal apoyado sobre la cabeza, con la rosca hacia arriba."""
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    T = lambda pts: [(x * S, y * S) for x, y in pts]
    cx = 385
    md.polygon(T([(cx - 66, 274), (cx + 66, 274), (cx + 66, 238), (cx + 58, 228), (cx - 58, 228), (cx - 66, 238)]), fill=255)   # cabeza
    md.rectangle([(cx - 34) * S, 222 * S, (cx + 34) * S, 230 * S], fill=255)                                                      # arandela
    y = 222; paso = 13
    pts_d, pts_i = [], []
    while y > 40:                                    # rosca en diente de sierra
        pts_d += [(cx + 30, y), (cx + 38, y - paso * 0.45)]; pts_i += [(cx - 38, y - paso * 0.45 - paso / 2), (cx - 30, y - paso / 2)]
        y -= paso
    md.polygon(T([(cx - 30, 222)] + [(cx + 30, 222)] + pts_d + [(cx + 22, 26), (cx - 22, 26)] + list(reversed(pts_i))), fill=255)
    md.line(T([(cx - 66, 238), (cx + 66, 238)]), fill=0, width=int(2 * S))
    md.line(T([(cx - 22, 274), (cx - 22, 240)]), fill=0, width=int(2 * S)); md.line(T([(cx + 22, 274), (cx + 22, 240)]), fill=0, width=int(2 * S))
    return m

def tuerca_mask(w, h):
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    cx, cy, r = 378, 160, 100
    hexa = [((cx + math.cos(math.radians(30 + 60 * k)) * r) * S, (cy + math.sin(math.radians(30 + 60 * k)) * r) * S) for k in range(6)]
    md.polygon(hexa, fill=255)
    md.ellipse([(cx - 46) * S, (cy - 46) * S, (cx + 46) * S, (cy + 46) * S], fill=0)
    for k in range(8):                                # filetes de rosca interna
        a = math.radians(k * 45 + 10)
        md.arc([(cx - 46) * S, (cy - 46) * S, (cx + 46) * S, (cy + 46) * S], k * 45 + 10, k * 45 + 30, fill=255, width=int(5 * S))
    md.ellipse([(cx - 70) * S, (cy - 70) * S, (cx + 70) * S, (cy + 70) * S], outline=0, width=int(2 * S))   # chaflán
    return m

def rodamiento_mask(w, h):
    m = Image.new("L", (w * S, h * S), 0); md = ImageDraw.Draw(m)
    cx, cy = 376, 160
    E = lambda r, v: md.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=v)
    E(96, 255); E(79, 0); E(50, 255); E(33, 0)
    for k in range(10):                               # bolillas
        a = 2 * math.pi * k / 10
        x, y = cx + math.cos(a) * 64.5, cy + math.sin(a) * 64.5
        md.ellipse([(x - 12) * S, (y - 12) * S, (x + 12) * S, (y + 12) * S], fill=255)
    return m

FORMAS = {"pez": pez_espada_mask, "tornillo": tornillo_mask, "tuerca": tuerca_mask, "rodamiento": rodamiento_mask, "engranaje": engranaje_mask, "diamante": diamante_mask, "pino": pino_mask, "montana": montana_mask, "torre": torre_mask, "cohete": cohete_mask, "faro": faro_mask, "jarron": jarron_mask}
FORMA = os.environ.get("FORMA_ARRANQUE", "tornillo")   # forma que imprime la boquilla en la pantalla de arranque

def fondo_capas(w, h, sem=7):
    """Fondo abstracto propio: líneas de capas de impresión 3D en perspectiva y una pieza en capas."""
    rnd = random.Random(sem)
    im = Image.new("RGB", (w * S, h * S), (10, 10, 10)); d = ImageDraw.Draw(im)
    # degradé radial rojo oscuro desde abajo a la derecha
    glow = Image.new("L", (w * S, h * S), 0); gd = ImageDraw.Draw(glow)
    for i in range(60, 0, -1):
        r = i * 9 * S
        gd.ellipse([(w * 0.78) * S - r, (h * 1.05) * S - r, (w * 0.78) * S + r, (h * 1.05) * S + r], fill=int(110 * (1 - i / 60) ** 1.6))
    glow = glow.filter(ImageFilter.GaussianBlur(30 * S))
    im = Image.composite(Image.new("RGB", im.size, (95, 8, 12)), im, glow); d = ImageDraw.Draw(im)
    # pieza impresa: un pez espada (diseño propio) sobre una base tipo trofeo, armado con capas
    mask = FORMAS[FORMA](w, h)
    bb = mask.getbbox(); top, bot = bb[1], bb[3]
    progreso = 0.55                                   # porcentaje ya impreso
    corte = bot - (bot - top) * progreso
    paso = int(3.2 * S)
    capas = Image.new("RGB", im.size, (0, 0, 0)); cd = ImageDraw.Draw(capas)
    for i, y in enumerate(range(bot, top - paso, -paso)):
        t = (bot - y) / (bot - top)
        if y >= corte:
            col = (int(95 + 130 * t), int(12 + 18 * t), int(16 + 18 * t))
            if abs(y - corte) < paso: col = (255, 70, 70)       # capa que se está imprimiendo
            cd.rectangle([0, y - paso + int(0.9 * S), w * S, y], fill=col)
        else:
            if i % 2 == 0: cd.rectangle([0, y - int(0.6 * S), w * S, y], fill=(78, 78, 78))   # lo que falta imprimir
    im.paste(capas, (0, 0), mask)
    # contorno fino de la parte que falta, para que se lea la forma completa de la M
    falta = mask.crop((0, 0, w * S, int(corte))).filter(ImageFilter.FIND_EDGES)
    falta = falta.point(lambda v: 255 if v > 40 else 0)
    im.paste(Image.new("RGB", falta.size, (110, 110, 110)), (0, 0), falta)
    # boquilla sobre la capa actual
    yfila = min(int(corte) + 2 * S, h * S - 1)
    fila = mask.crop((0, yfila, w * S, yfila + 1)).tobytes()
    tramos, ini = [], None
    for x, v in enumerate(fila + b"\x00"):
        if v > 127 and ini is None: ini = x
        elif v <= 127 and ini is not None: tramos.append((ini, x)); ini = None
    centro = (bb[0] + bb[2]) / 2
    if tramos:
        a, b = min(tramos, key=lambda t: abs((t[0] + t[1]) / 2 - centro) - (t[1] - t[0]) * 0.25)
        nx = (a + b) / 2 / S
    else:
        nx = centro / S
    ny = corte / S - 3
    d.polygon([((nx - 9) * S, (ny - 12) * S), ((nx + 9) * S, (ny - 12) * S), ((nx + 3) * S, ny * S), ((nx - 3) * S, ny * S)], fill=(200, 200, 200))
    d.rectangle([(nx - 17) * S, (ny - 32) * S, (nx + 17) * S, (ny - 12) * S], fill=(60, 60, 60))
    d.rectangle([(nx - 17) * S, (ny - 32) * S, (nx + 17) * S, (ny - 29) * S], fill=RD)
    # líneas de cama en perspectiva
    hy = h * 0.88
    for i in range(-12, 13):
        x0 = w * 0.78 + i * 70; d.line([(w * 0.78 + i * 6) * S, hy * S, x0 * S, (h + 40) * S], fill=(40, 40, 40), width=S)
    for j in range(6):
        y = hy + (j ** 1.7) * 3.2; d.line([0, y * S, w * S, y * S], fill=(42, 42, 42), width=S)
    # puntos sutiles
    for _ in range(140):
        x, y = rnd.uniform(0, w * 0.6), rnd.uniform(0, h * 0.8)
        v = rnd.randint(24, 46); d.point((x * S, y * S), fill=(v, v, v))
    return im

def logo():
    w, h = 480, 320
    im = fondo_capas(w, h)
    d = ImageDraw.Draw(im)
    fB = lambda t: ImageFont.truetype(FONT_B, int(t * S)); fR = lambda t: ImageFont.truetype(FONT_R, int(t * S))
    x0 = 30
    d.rectangle([x0 * S, 92 * S, (x0 + 5) * S, 228 * S], fill=RD)
    # "MAGNA" con un "2" grande por detrás de la A y la N
    fM = fB(54); tx, ty = x0 + 16, 150
    ancho_MAG = d.textlength("MAG", font=fM); ancho_NA = d.textlength("MAGNA", font=fM)
    cx2 = (tx * S + ancho_MAG + tx * S + d.textlength("MAGN", font=fM)) / 2   # entre la A y la N
    d.text((cx2 + 14 * S, (ty + 34) * S), "2", font=fB(150), fill=(150, 18, 24), anchor="ms")
    # contorno oscuro para que las letras se separen del "2"
    d.text((tx * S, ty * S), "MAGNA", font=fM, fill=WH, anchor="ls", stroke_width=int(3 * S), stroke_fill=(14, 14, 14))
    d.text((tx * S, ty * S), "MAGNA", font=fM, fill=WH, anchor="ls")
    d.text(((x0 + 18) * S, 196 * S), "MARLIN " + VERSION_MARLIN, font=fB(13), fill=RD)
    d.text(((x0 + 18) * S, 216 * S), "DUAL EXTRUSION", font=fR(10), fill=(140, 140, 140))
    d.line([(x0 * S, 282 * S), (300 * S, 282 * S)], fill=(60, 60, 60), width=S)
    return im.resize((w, h), Image.LANCZOS)

def vista_previa():
    """bmp_preview.bin: lo que muestra la pantalla de impresión cuando el gcode no trae miniatura
    (antes era la "G" azul de Makerbase). Es el recorte de la pieza del arranque (el tornillo a medio
    imprimir) en un cuadro de 200x200. Va directo a la pantalla, sin transparencia."""
    w, h = 480, 320
    fondo = fondo_capas(w, h).resize((w, h), Image.LANCZOS)
    # centrado en la pieza (x=385): a la derecha falta pantalla, así que se completa con el borde espejado
    base = fondo.crop((385 - 135, 8, w, 278))
    falta = 270 - base.width
    cuadro = Image.new("RGB", (270, 270))
    cuadro.paste(base, (0, 0))
    cuadro.paste(base.crop((base.width - falta, 0, base.width, 270)).transpose(Image.FLIP_LEFT_RIGHT), (base.width, 0))
    im = cuadro.resize((200, 200), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 199, 199], outline=(58, 58, 58))
    d.rectangle([0, 0, 3, 199], fill=RD)
    f = ImageFont.truetype(FONT_R, 11)
    d.text((193, 190), "SIN VISTA PREVIA", font=f, fill=(150, 150, 150), anchor="rs")
    return im

# ------------------------------------------------------------------ codificación
def rgb565(im):
    px = list(im.convert("RGB").getdata()) if not hasattr(im, "get_flattened_data") else list(im.convert("RGB").get_flattened_data())
    return struct.pack("<%dH" % len(px), *[((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3) for r, g, b in px])

BG565 = ((BG[0] >> 3) << 11) | ((BG[1] >> 2) << 5) | (BG[2] >> 3)
TRANSP565 = 0x07E0                    # LV_COLOR_TRANSP = LV_COLOR_LIME (verde puro) en lv_conf.h de LVGL MKS

def lvgl_bin(im, transparente=False):
    """transparente=True: cf=6 (LV_IMG_CF_TRUE_COLOR_CHROMA_KEYED en LVGL 6: 4=TRUE_COLOR, 5=TRUE_COLOR_ALPHA
    (¡3 bytes por píxel, NO usar!), 6=TRUE_COLOR_CHROMA_KEYED). El fondo exacto del ícono pasa a verde puro y
    LVGL no lo dibuja, así se ve el fondo de la pantalla. Los bordes suavizados quedan mezclados con
    gris oscuro, que no se nota sobre el fondo oscuro de la pantalla."""
    w, h = im.size
    datos = rgb565(im)
    cf = 4
    if transparente:
        px = struct.unpack("<%dH" % (w * h), datos)
        datos = struct.pack("<%dH" % (w * h), *[TRANSP565 if p == BG565 else (0x07E1 if p == TRANSP565 else p) for p in px])
        cf = 6
    hdr = cf | (w << 10) | (h << 21)
    return struct.pack("<I", hdr) + datos + b"\x0a"

TAM_150 = ["operate", "pause", "resume", "stop"]
TAM_45 = ["bed_state", "ext1_state", "ext2_state", "fan_state", "init_state", "power_state", "speed_state", "time_state", "times_state", "zpos_state"]
TAM_92 = ["back", "pageUp", "pageDown"]
CHICOS = ["back70x40", "value_blank", "blank_sel", "enable", "disable", "arrow"]

def todos():
    out = {}
    for n in ICONOS: out[n] = icono_117(n)
    for n in TAM_45: out[n] = estado_45(n)
    for n in TAM_150: out[n] = boton_150(n)
    for n in TAM_92: out[n] = flecha_92(n)
    for n in CHICOS: out[n] = chico(n)
    return out

def main():
    dest = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    os.makedirs(dest, exist_ok=True)
    ims = todos()
    opacos = set(CHICOS) - {"arrow"}     # campos, interruptores y botón chico: con fondo propio
    for n, im in ims.items():
        open(os.path.join(dest, f"bmp_{n}.bin"), "wb").write(lvgl_bin(im, transparente=n not in opacos))
    lg = logo()
    open(os.path.join(dest, "bmp_logo.bin"), "wb").write(rgb565(lg))
    vp = vista_previa()
    open(os.path.join(dest, "bmp_preview.bin"), "wb").write(rgb565(vp))   # 200x200 RGB565 sin encabezado
    print(f"{len(ims) + 2} archivos en {dest}")
    if "--preview" in sys.argv:
        pv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview"); os.makedirs(pv, exist_ok=True)
        lg.save(os.path.join(pv, "logo.png"))
        vp.save(os.path.join(pv, "vista_previa.png"))
        orden = [n for n in ICONOS]
        cols = 10; rows = (len(orden) + cols - 1) // cols
        sh = Image.new("RGB", (cols * 119, rows * 142), (60, 60, 60))
        for i, n in enumerate(orden): sh.paste(ims[n], ((i % cols) * 119, (i // cols) * 142))
        sh.save(os.path.join(pv, "iconos.png"))
        otros = TAM_150 + TAM_92 + TAM_45 + CHICOS
        sh2 = Image.new("RGB", (900, 260), (60, 60, 60)); x = y = 4
        for n in otros:
            im = ims[n]
            if x + im.width > 896: x = 4; y += 96
            sh2.paste(im, (x, y)); x += im.width + 6
        sh2.save(os.path.join(pv, "otros.png"))
        print("preview en", pv)

if __name__ == "__main__":
    main()
