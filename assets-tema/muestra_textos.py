#!/usr/bin/env python3
"""
Dibuja los textos en castellano de la pantalla con la letra REAL de la pantalla (FontUNIGBK.bin con
las letras que agrega fuente_acentos.py), para ver de un vistazo si entran: debajo de los íconos
(117 px), títulos, listas de ajustes y mensajes. Una letra que falte sale como un cuadrado rojo.

Uso: python3 muestra_textos.py FontUNIGBK.bin salida.png
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import traduccion_es as T  # noqa: E402

tmp = os.path.join(tempfile.mkdtemp(), 'f.bin')
shutil.copy(sys.argv[1], tmp)
subprocess.run([sys.executable, os.path.join(AQUI, 'fuente_acentos.py'), tmp], check=True, stdout=subprocess.DEVNULL)
d = open(tmp, 'rb').read()
mn, mx, _ = struct.unpack('<HHB', d[:5])
H = 21


def glifo(ch):
    c = ord(ch)
    if not (mn <= c <= mx):
        return None
    p = struct.unpack('<I', d[8 + (c - mn) * 4:12 + (c - mn) * 4])[0]
    if not p:
        return None
    adv, bw = d[p], d[p + 1]
    return adv, bw, ''.join(f'{b:08b}' for b in d[p + 2:p + 2 + (bw * H + 7) // 8])


def ancho(t):
    return max(sum((glifo(c) or (10,))[0] for c in linea) for linea in t.split('\n'))


def texto(img, x, y, t, col):
    px = img.load()
    x0 = x
    for ch in t:
        if ch == '\n':
            y += H
            x = x0
            continue
        g = glifo(ch)
        if not g:
            ImageDraw.Draw(img).rectangle([x, y + 4, x + 8, y + 16], outline=(255, 0, 0))
            x += 10
            continue
        adv, bw, bits = g
        for r in range(H):
            for c in range(bw):
                if bits[r * bw + c] == '1' and 0 <= x + c < img.width and 0 <= y + r < img.height:
                    px[x + c, y + r] = col
        x += adv


ICONOS = ['TOOL_TEXT', 'PREHEAT_TEXT', 'MOVE_TEXT', 'HOME_TEXT', 'LEVELING_TEXT', 'SET_TEXT', 'FILAMENT_TEXT',
          'FAN_TEXT', 'MOTOR_OFF_TEXT', 'LANGUAGE_TEXT', 'ABOUT_TEXT', 'EEPROM_SETTINGS', 'PRINTING_OPERATION',
          'PRINTING_PAUSE', 'PRINTING_STOP', 'PRINTING_RESUME', 'PRINTING_CHANGESPEED', 'MACHINE_PARA',
          'EXTRUDER_IN_TEXT', 'EXTRUDER_OUT_TEXT', 'EXTRUDE_HIGH_SPEED_TEXT', 'DEFAULT']
TITULOS = ['TITLE_READYPRINT', 'TITLE_CHOOSEFILE', 'TITLE_PRINTING', 'MACHINE_CONFIG_TITLE', 'ENDSTOP_CONF_TITLE',
           'MAXFEEDRATE_CONF_TITLE', 'HOMEFEEDRATE_CONF_TITLE', 'LEVELING_ZOFFSET_TITLE', 'EEPROM_SETTINGS_TITLE']
LISTA = ['X_MAX_LENGTH', 'HOME_DIR_X', 'MIN_ENDSTOP_Z', 'FILAMENT_TEMPERATURE', 'TRAMMING_POS', 'LEVELING_AUTO_ZOFFSET',
         'PROBE_Z_OFFSET', 'PREHEAT_TEMPER', 'NOZZLE_MAX_TEMPERATURE', 'X_MAXFEEDRATE', 'PRINT_ACCELERATION',
         'Z_HOMESPEED', 'PWROFF_AFTER_PRINT', 'PAUSE_POSITION_Z', 'WIFI_SETTINGS_PASSWORD', 'ENABLE']
DIALOGOS = ['DIALOG_PRINT_MODEL', 'DIALOG_CANCEL_PRINT', 'DIALOG_PRINT_FINISH', 'FILAMENT_DIALOG_LOAD_CONFIRM1_TIPS',
            'MESSAGE_OPTION', 'EEPROM_REVERT_TIPS', 'DIALOG_REPRINT_FROM_BREAKPOINT']

W = 980
img = Image.new('RGB', (W, 1400), (20, 20, 20))
dr = ImageDraw.Draw(img)
BLANCO, ROJO, GRIS = (238, 238, 238), (214, 32, 39), (150, 150, 150)
y = 8
dr.text((10, y), 'Textos de la pantalla en castellano, con la letra real de la pantalla', fill=GRIS)
y += 20
dr.text((10, y), 'Debajo de los iconos (caja de 117 px = ancho del boton; en rojo si no entra):', fill=ROJO)
y += 18
x = 10
for k in ICONOS:
    if x + 120 > W:
        x = 10
        y += 34
    t = T.TEXTOS[k]
    dr.rectangle([x, y, x + 117, y + 26], outline=(70, 70, 70))
    texto(img, x + max(0, (117 - ancho(t)) // 2), y + 3, t, BLANCO if ancho(t) <= 117 else (255, 80, 80))
    x += 124
y += 44
for titulo, claves, limite in (("Titulos (franja de arriba; 'MAGNA 2' ocupa la derecha desde ~330 px):", TITULOS, 330),
                               ('Listas de ajustes (el valor va a la derecha, desde ~300 px):', LISTA, 300)):
    dr.text((10, y), titulo, fill=ROJO)
    y += 18
    for k in claves:
        dr.line([(10 + limite, y), (10 + limite, y + 20)], fill=(90, 40, 40))
        texto(img, 10, y, T.TEXTOS[k], BLANCO if ancho(T.TEXTOS[k]) <= limite else (255, 80, 80))
        y += 23
    y += 10
dr.text((10, y), 'Mensajes (centrados en la pantalla de 480 px):', fill=ROJO)
y += 18
for k in DIALOGOS:
    texto(img, 10, y, T.TEXTOS[k], BLANCO)
    y += 23 * (T.TEXTOS[k].count('\n') + 1) + 6
y += 6
dr.text((10, y), 'Letras agregadas a la letra de la pantalla:', fill=ROJO)
y += 18
texto(img, 10, y, 'í ú ü Á É Í Ó Ú Ñ ¡ °     Sí, Menú, Línea, ¡Listo!, 60°', BLANCO)
y += 30
img.crop((0, 0, W, y + 6)).save(sys.argv[2])
print('Muestra:', sys.argv[2])
