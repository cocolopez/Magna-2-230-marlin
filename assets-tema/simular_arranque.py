#!/usr/bin/env python3
"""Simula en la compu el arranque animado del firmware (etapa 32), con el MISMO algoritmo que
magna_arranque_animado() de animacion_arranque.cpp.inc y leyendo los mismos archivos que lee la
pantalla (assets/bmp_logo.bin, assets/bmp_tornillo1..3.bin y las constantes de animacion_arranque.inc).
Sirve para ver que las tiras, las constantes y la boquilla coinciden antes de probar en la impresora.

Uso: python3 assets-tema/simular_arranque.py [salida.gif]
Sale con error si alguna fila de la última imagen no coincide con el tornillo terminado.
"""
import os
import re
import struct
import sys

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(AQUI, 'assets')
C = {m[0]: int(m[1]) for m in re.findall(r'#define MAGNA_ANIM_(\w+) (\d+)', open(os.path.join(AQUI, 'animacion_arranque.inc')).read())}
ANCHO = C['X1'] - C['X0']


def leer565(datos):
    return [(((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31) for p in struct.unpack('<%dH' % (len(datos) // 2), datos)]


logo = open(os.path.join(A, 'bmp_logo.bin'), 'rb').read()
tiras = [open(os.path.join(A, f'bmp_tornillo{i + 1}.bin'), 'rb').read() for i in range(C['TIRAS'])]
pantalla = Image.new('RGB', (480, 320))
pantalla.putdata(leer565(logo))
px = pantalla.load()


def rect(x, y, w, h, color):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px[xx, yy] = color


cuadros = [pantalla.copy()]
# las tiras van de abajo hacia arriba y se leen de corrido (como SPIFlash.readData en la pantalla)
corrido = b''.join(tiras)
leidas = 0
PASOS, corte_antes = 16, C['ABAJO']
for k in range(1, PASOS + 1):
    corte = C['ABAJO'] - (C['ABAJO'] - C['ARRIBA']) * k // PASOS
    for r in range(corte_antes - 1, corte - 1, -1):
        fila = corrido[leidas * ANCHO * 2:(leidas + 1) * ANCHO * 2]
        leidas += 1
        for i, c in enumerate(leer565(fila)):
            px[C['X0'] + i, r] = c
    for r in range(max(C['Y0'], corte - 36), corte):
        fila = logo[(r * 480 + C['X0']) * 2:(r * 480 + C['X0'] + ANCHO) * 2]
        for i, c in enumerate(leer565(fila)):
            px[C['X0'] + i, r] = c
    if k < PASOS:
        ny, nx = corte - 3, C['CENTRO']
        if ny - 32 >= 0:
            rect(nx - 17, ny - 32, 35, 3, (214, 32, 39))
            rect(nx - 17, ny - 29, 35, 17, (60, 60, 60))
            for y in range(ny - 12, ny):
                medio = 9 - (y - (ny - 12)) // 2
                rect(nx - medio, y, medio * 2 + 1, 1, (200, 200, 200))
    corte_antes = corte
    cuadros.append(pantalla.copy())

# la última imagen tiene que ser el tornillo terminado, fila por fila
errores = 0
corrido_filas = [corrido[i * ANCHO * 2:(i + 1) * ANCHO * 2] for i in range(len(corrido) // (ANCHO * 2))]
for r in range(C['ARRIBA'], C['ABAJO']):
    esperado = leer565(corrido_filas[C['ABAJO'] - 1 - r])
    if [px[C['X0'] + i, r] for i in range(ANCHO)] != esperado:
        errores += 1
salida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 'preview', 'arranque-animado.gif')
cuadros[0].save(salida, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 6, duration=90, loop=0)
print(f'{len(cuadros)} cuadros en {salida}; filas distintas al tornillo terminado: {errores}')
sys.exit(1 if errores else 0)
