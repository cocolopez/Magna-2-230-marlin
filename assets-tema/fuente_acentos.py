#!/usr/bin/env python3
"""
Agrega a la letra de la pantalla (FontUNIGBK.bin de Makerbase) las letras del castellano que le faltan.

La letra trae á é ó ñ ¿ pero NO í ú ü Á É Í Ó Ú Ñ ¡ °: con la pantalla en español, "Sí", "Menú" o
"Línea" salían con un hueco. Este script arma esas letras a partir de las que sí están (la base
sin tilde + el acento de la "é" o la tilde de la "ñ") y las agrega al final del archivo,
apuntando la tabla a ellas. Las demás letras no se tocan.

Formato del archivo (xbf de LVGL, el que lee gb2312_puhui16.cpp): encabezado {min, max (uint16),
bpp (uint8), 3 reservados}, tabla de posiciones uint32 por letra desde min (0 = no está), y en
cada posición: ancho de avance (1 byte), ancho de la caja (1 byte) y el dibujo a 1 bit por punto,
21 filas de "ancho de la caja" puntos, todo seguido (sin relleno por fila).

Uso: python3 fuente_acentos.py FontUNIGBK.bin [salida]   (sin salida, lo cambia en el lugar)
Es idempotente: si la letra ya está, no la vuelve a agregar.
"""
import struct
import sys

ALTO = 21


def leer(d, mn, c):
    p = struct.unpack_from('<I', d, 8 + (c - mn) * 4)[0]
    if not p:
        return None
    avance, ancho = d[p], d[p + 1]
    bits = ''.join(f'{b:08b}' for b in d[p + 2:p + 2 + (ancho * ALTO + 7) // 8])
    return avance, ancho, [list(bits[f * ancho:(f + 1) * ancho]) for f in range(ALTO)]


def armar(avance, ancho, filas):
    bits = ''.join(''.join(f) for f in filas)
    bits += '0' * (-len(bits) % 8)
    return bytes([avance, ancho]) + bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def poner(filas, dibujo, fila, col):
    """Dibuja [dibujo] (lista de strings con '#') desde (fila, col), sobre lo que haya."""
    for i, linea in enumerate(dibujo):
        for j, ch in enumerate(linea):
            if ch == '#' and 0 <= col + j < len(filas[0]):
                filas[fila + i][col + j] = '1'


def borrar(filas, desde, hasta):
    for f in range(desde, hasta):
        filas[f] = ['0'] * len(filas[f])


AGUDO = ['..##', '.##.', '##..']          # el acento de la "é" de la letra original
AGUDO_MAYUS = ['..##', '.##.']            # más bajo: encima de las mayúsculas queda poco lugar
DIERESIS = ['##.##']
TILDE_MAYUS = ['.###..#', '.#..###']      # la de la "ñ"


def main():
    origen = sys.argv[1]
    destino = sys.argv[2] if len(sys.argv) > 2 else origen
    d = bytearray(open(origen, 'rb').read())
    mn, mx, bpp = struct.unpack_from('<HHB', d, 0)
    if bpp != 1:
        sys.exit(f'Letra con {bpp} bits por punto: este script es para la de 1 bit de Makerbase')

    def base(ch):
        g = leer(d, mn, ord(ch))
        if not g:
            sys.exit(f'La letra no trae "{ch}" (base para las nuevas)')
        return g

    nuevas = {}
    # minúsculas: la "i" pierde el punto; el acento va donde está el de la "é" (filas 4 a 6)
    av, an, f = base('i'); borrar(f, 4, 6); poner(f, AGUDO, 4, 0); nuevas['í'] = (av, an, f)
    av, an, f = base('u'); poner(f, AGUDO, 4, 4); nuevas['ú'] = (av, an, f)
    av, an, f = base('u'); poner(f, DIERESIS, 5, 2); nuevas['ü'] = (av, an, f)
    # mayúsculas: empiezan en la fila 5, el acento va en las filas 2 y 3
    for ch, col in (('Á', 5), ('É', 4), ('Í', 1), ('Ó', 5), ('Ú', 5)):
        av, an, f = base('AEIOU'['ÁÉÍÓÚ'.index(ch)]); poner(f, AGUDO_MAYUS, 2, col); nuevas[ch] = (av, an, f)
    av, an, f = base('N'); poner(f, TILDE_MAYUS, 2, 3); nuevas['Ñ'] = (av, an, f)
    # ¡ = ! dado vuelta (el punto arriba, a la altura de las minúsculas)
    av, an, f = base('!')
    nuevas['¡'] = (av, an, [list(r) for r in f[:5]] + [list(r) for r in reversed(f[5:17])] + [list(r) for r in f[17:]])
    # ° (grados)
    f = [['0'] * 8 for _ in range(ALTO)]
    poner(f, ['.##.', '#..#', '#..#', '.##.'], 5, 1)
    nuevas['°'] = (6, 8, f)

    agregadas = []
    for ch, (av, an, f) in nuevas.items():
        c = ord(ch)
        if not (mn <= c <= mx):
            continue
        if struct.unpack_from('<I', d, 8 + (c - mn) * 4)[0]:
            continue  # ya está (original o agregada antes)
        pos = len(d)
        d += armar(av, an, f)
        struct.pack_into('<I', d, 8 + (c - mn) * 4, pos)
        agregadas.append(ch)
    open(destino, 'wb').write(d)
    print('Letra de la pantalla: ' + (f'agregadas {" ".join(agregadas)}' if agregadas else 'ya tenía todas las letras'))


if __name__ == '__main__':
    main()
