#!/usr/bin/env python3
"""Verifica los assets del tema (assets-tema/assets) contra el formato que espera la UI MKS (LVGL 6):
  * encabezado LVGL: cf 4 (TRUE_COLOR) o 6 (TRUE_COLOR_CHROMA_KEYED). Cualquier otro (por ejemplo 5 = con
    canal alfa, 3 bytes por píxel) se ve roto en la pantalla.
  * tamaño exacto: 4 + ancho*alto*2 + 1 bytes; logo 480x320x2 y bmp_preview 200x200x2 sin encabezado.
  * el verde de transparencia (0x07E0) solo en imágenes cf 6.
  * todos los nombres que pide el firmware (pic_manager.cpp) existen, si el código de Marlin está presente.
  * cada imagen comprimida (RLE de SPIFlashStorage) entra en su lugar de 9 KB.
Uso (desde la raíz del proyecto): python3 pruebas/verificar-assets.py"""
import os, re, struct, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
A = os.path.join(R, 'assets-tema', 'assets')
CF_OK = {4: 'TRUE_COLOR', 6: 'TRUE_COLOR_CHROMA_KEYED'}
def rle_bytes(px):
    n = len(px); count = out = 0
    while count < n:
        i = count + 1
        while i < n and i - count < 32767 and px[i] == px[count]: i += 1
        if i - count == 1:
            while i < n and i - count < 32767 and (px[i] != px[i - 1] or (i > 1 and px[i] != px[i - 2])): i += 1
            while i < n and px[i] == px[i - 1]: i -= 1
            out += 1 + (i - count)
        else: out += 2
        count = i
    return out * 2
err = []
if not os.path.isdir(A): print('No hay assets-tema/assets: nada que verificar'); sys.exit(0)
for f in sorted(os.listdir(A)):
    b = open(os.path.join(A, f), 'rb').read()
    if f == 'bmp_logo.bin':
        if len(b) != 480 * 320 * 2: err.append(f'{f}: tamaño {len(b)} (esperado 307200)')
        continue
    if f == 'bmp_preview.bin':   # vista previa por defecto: 200x200 RGB565 sin encabezado, va directo a la pantalla
        if len(b) != 200 * 200 * 2: err.append(f'{f}: tamaño {len(b)} (esperado 80000)')
        continue
    if f.startswith('bmp_tornillo'):   # etapa 32: tiras del arranque animado, RGB565 sin encabezado (ver simular_arranque.py)
        px = struct.unpack('<%dH' % (len(b) // 2), b)
        if rle_bytes(px) + 4 > 9 * 1024: err.append(f'{f}: comprimido supera 9 KB')
        continue
    hd = struct.unpack('<I', b[:4])[0]; cf, w, h = hd & 0x1f, (hd >> 10) & 0x7ff, (hd >> 21) & 0x7ff
    if cf not in CF_OK: err.append(f'{f}: cf={cf} no soportado (usar 4 o 6)')
    if len(b) != 4 + w * h * 2 + 1: err.append(f'{f}: tamaño {len(b)} != 4+{w}x{h}x2+1')
    px = struct.unpack('<%dH' % (w * h), b[4:4 + w * h * 2])
    if cf != 6 and 0x07E0 in px: err.append(f'{f}: tiene verde de transparencia pero cf={cf}')
    if rle_bytes(px) + 4 > 9 * 1024: err.append(f'{f}: comprimido supera 9 KB')
pm = os.path.join(R, 'Marlin/src/lcd/extui/mks_ui/pic_manager.cpp')
if os.path.exists(pm):
    pedidos = set(re.findall(r'F\("(bmp_[^"]+\.bin)"\)', open(pm, encoding='utf-8').read()))
    tengo = {x.lower() for x in os.listdir(A)}
    faltan = sorted(p for p in pedidos if p.lower() not in tengo and p not in ('bmp_preview.bin',))
    if faltan: print('aviso: el firmware pide y el tema no trae (se usan los de Makerbase):', faltan)
for e in err: print('MAL ', e)
print(f'OK: {len(os.listdir(A))} assets con formato válido' if not err else f'FALLA: {len(err)} errores'); sys.exit(1 if err else 0)
