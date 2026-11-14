#!/usr/bin/env python3
"""Compila render.c contra la LVGL de MKS y verifica la imagen resultante.
Uso: python3 pruebas/render-lvgl/verificar_render.py <carpeta_lvgl> [carpeta_assets] [salida.png]
  <carpeta_lvgl>: la librería LVGL MKS (en la build de PlatformIO: .pio/libdeps/mks_robin_nano_v1_3_f4/lvgl)."""
import glob, os, struct, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); R = os.path.abspath(os.path.join(AQUI, '..', '..'))
LV = os.path.abspath(sys.argv[1]); A = sys.argv[2] if len(sys.argv) > 2 else os.path.join(R, 'assets-tema', 'assets')
PNG = sys.argv[3] if len(sys.argv) > 3 else os.path.join(R, 'render-pantalla-principal.png')
src = glob.glob(os.path.join(LV, 'src', '**', '*.c'), recursive=True)
exe = '/tmp/render_lvgl'
subprocess.run(['gcc', '-O1', '-w', '-DLV_CONF_INCLUDE_SIMPLE', '-I' + LV, '-I' + os.path.join(LV, 'src'), '-I' + os.path.join(R, 'assets-tema'),
                os.path.join(AQUI, 'render.c')] + src + ['-o', exe], check=True)
subprocess.run([exe, A, '/tmp/render.raw'], check=True)
px = struct.unpack('<%dH' % (480 * 320), open('/tmp/render.raw', 'rb').read())
rgb = [(((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31) for p in px]
verde = sum(1 for r, g, b in rgb if g > 180 and r < 90 and b < 90)
# en cada ícono grande tiene que haber trazo blanco y sobre todo fondo oscuro (no un bloque lleno)
def zona(x0, y0, w, h):
    z = [rgb[y * 480 + x] for y in range(y0, y0 + h) for x in range(x0, x0 + w)]
    blancos = sum(1 for r, g, b in z if r > 200 and g > 200 and b > 200); oscuros = sum(1 for r, g, b in z if max(r, g, b) < 70)
    return blancos, oscuros, len(z)
err = []
if verde: err.append(f'{verde} píxeles verdes (transparencia rota)')
for x in (20, 180, 340):
    bl, os_, n = zona(x, 90, 117, 100)
    if bl < 150: err.append(f'ícono en x={x}: casi sin trazo blanco ({bl})')
    if os_ < n * 0.6: err.append(f'ícono en x={x}: fondo no transparente/oscuro ({os_}/{n})')
try:
    from PIL import Image
    im = Image.new('RGB', (480, 320)); im.putdata(rgb); im.save(PNG); print('render guardado en', PNG)
except ImportError:
    pass
# ---- pantalla de menú con la decoración marcada (decoracion_menus.inc)
subprocess.run([exe, A, '/tmp/render_menu.raw', 'menu'], check=True)
pm = struct.unpack('<%dH' % (480 * 320), open('/tmp/render_menu.raw', 'rb').read())
mg = [(((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31) for p in pm]
def px(x, y): return mg[y * 480 + x]
es_rojo = lambda c: c[0] > 170 and c[1] < 70 and c[2] < 80
if sum(1 for r, g, b in mg if g > 180 and r < 90 and b < 90): err.append('menú: píxeles verdes')
if not all(es_rojo(px(x, 32)) for x in (5, 240, 470)): err.append('menú: falta la línea roja debajo del título')
if max(px(300, 15)) > 20: err.append('menú: falta la franja oscura del título')
if not es_rojo(px(1, 15)): err.append('menú: falta el acento rojo del título')
if not all(px(x, 177)[0] > 110 for x in (1, 13, 25)) or px(9, 177)[0] > 110: err.append('menú: falta el separador punteado')
if not (px(240, 317)[0] > px(240, 309)[0] > px(240, 307)[0]): err.append('menú: las capas de abajo no se distinguen del fondo')
if px(240, 300)[0] - px(240, 40)[0] < 40: err.append('menú: el degradé rojo es demasiado débil')
for i in range(8):
    x0, y0 = 2 + (i % 4) * 119 + 20, 36 + (i // 4) * 142 + 15
    if sum(1 for y in range(y0, y0 + 80) for x in range(x0, x0 + 77) if min(px(x, y)) > 200) < 100: err.append(f'menú: ícono {i} sin trazo blanco')
try:
    from PIL import Image
    im = Image.new('RGB', (480, 320)); im.putdata(mg); m2 = PNG.replace('.png', '-menu.png'); im.save(m2); print('render del menú guardado en', m2)
except ImportError:
    pass
for e in err: print('MAL ', e)
print('OK: los íconos se dibujan bien con la LVGL de la pantalla' if not err else f'FALLA: {len(err)} problemas'); sys.exit(1 if err else 0)
