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
subprocess.run(['gcc', '-O1', '-w', '-DLV_CONF_INCLUDE_SIMPLE', '-I' + LV, '-I' + os.path.join(LV, 'src'),
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
for e in err: print('MAL ', e)
print('OK: los íconos se dibujan bien con la LVGL de la pantalla' if not err else f'FALLA: {len(err)} problemas'); sys.exit(1 if err else 0)
