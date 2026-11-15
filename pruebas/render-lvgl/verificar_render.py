#!/usr/bin/env python3
"""Compila render.c contra la LVGL de MKS y verifica la imagen resultante.
Uso: python3 pruebas/render-lvgl/verificar_render.py <carpeta_lvgl> [carpeta_assets] [salida.png]
Además de la pantalla principal dibuja: un menú con la decoración, la pantalla Más con los botones
propios, un mensaje de carga de filamento, uno de calentando y la barra de impresión.
Cada una se guarda junto a salida.png (salida-menu.png, salida-mas.png, ...).
  <carpeta_lvgl>: la librería LVGL MKS (en la build de PlatformIO: .pio/libdeps/mks_robin_nano_v1_3_f4/lvgl)."""
import glob, os, struct, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); R = os.path.abspath(os.path.join(AQUI, '..', '..'))
LV = os.path.abspath(sys.argv[1]); A = sys.argv[2] if len(sys.argv) > 2 else os.path.join(R, 'assets-tema', 'assets')
PNG = sys.argv[3] if len(sys.argv) > 3 else os.path.join(R, 'render-pantalla-principal.png')
src = glob.glob(os.path.join(LV, 'src', '**', '*.c'), recursive=True)
exe = '/tmp/render_lvgl'
# letra normal de la pantalla (16 px) simulada con Roboto 16, para que las vistas previas se parezcan
woff = os.path.join(LV, 'scripts', 'built_in_font', 'Roboto-Regular.woff')
subprocess.run([sys.executable, os.path.join(R, 'assets-tema', 'generar_fuente.py'), woff if os.path.exists(woff) else '-',
                '16', '/tmp/fuente_normal.inc', 'magna_fuente_normal'], check=True)
subprocess.run(['gcc', '-O1', '-w', '-DLV_CONF_INCLUDE_SIMPLE', '-I' + LV, '-I' + os.path.join(LV, 'src'), '-I' + os.path.join(R, 'assets-tema'), '-I/tmp',
                os.path.join(AQUI, 'render.c')] + src + ['-o', exe, '-lm'], check=True)
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
def dibujar(modo):
    subprocess.run([exe, A, '/tmp/render_%s.raw' % modo, modo], check=True)
    pm = struct.unpack('<%dH' % (480 * 320), open('/tmp/render_%s.raw' % modo, 'rb').read())
    img = [(((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31) for p in pm]
    try:
        from PIL import Image
        im = Image.new('RGB', (480, 320)); im.putdata(img); im.save(PNG.replace('.png', '-%s.png' % modo))
    except ImportError:
        pass
    if sum(1 for r, g, b in img if g > 180 and r < 90 and b < 90): err.append(modo + ': píxeles verdes')
    return img
mg = dibujar('menu')
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
# ---- Ajustes > Más: los 6 botones propios
ms = dibujar('mas')
for i in range(8):
    x0, y0 = 2 + (i % 4) * 119 + 15, 36 + (i // 4) * 142 + 10
    if sum(1 for y in range(y0, y0 + 85) for x in range(x0, x0 + 87) if min(ms[y * 480 + x]) > 200) < 80:
        err.append(f'Más: botón {i} sin ícono')
# ---- mensaje de carga de filamento: letra grande y barra del tema al 60 %
cg = dibujar('carga')
filas = [y for y in range(36, 150) if any(min(cg[y * 480 + x]) > 200 for x in range(20, 460))]
if len(filas) < 40: err.append(f'carga: el texto no se ve grande ({len(filas)} filas con letra)')
if not es_rojo(cg[177 * 480 + 200]): err.append('carga: la barra no se pinta de rojo')
if es_rojo(cg[177 * 480 + 400]) or max(cg[177 * 480 + 400]) > 60: err.append('carga: la parte vacía de la barra no es oscura')
if min(cg[275 * 480 + 320]) > 200 or not cg[275 * 480 + 280][0] > 90: err.append('carga: falta el botón Cancelar')
# ---- calentando: temperatura arriba y texto abajo, sin encimarse
ca = dibujar('calentando')
bloques, dentro = [], False
for y in range(36, 245):
    hay = any(min(ca[y * 480 + x]) > 200 for x in range(20, 460))
    if hay and not dentro: bloques.append(y)
    dentro = hay
if len(bloques) < 3: err.append(f'calentando: temperatura y texto encimados ({len(bloques)} bloques)')
# ---- barra de impresión con el porcentaje grande
im_ = dibujar('imprimiendo')
if not es_rojo(im_[56 * 480 + 230]): err.append('imprimiendo: la barra no se pinta de rojo')
if sum(1 for y in range(40, 74) for x in range(300, 380) if min(im_[y * 480 + x]) > 200) < 60: err.append('imprimiendo: no se ve el porcentaje')
# ---- Acerca de: créditos abajo a la izquierda, sin tocar el botón Atrás ni los datos de Marlin
ac = dibujar('acerca')
claros = lambda x0, x1, y0, y1: sum(1 for y in range(y0, y1) for x in range(x0, x1) if min(ac[y * 480 + x]) > 200)
if claros(12, 340, 238, 264) < 150: err.append('acerca: no se ve "Creado por Andrés Londero"')
if sum(1 for y in range(272, 292) for x in range(12, 340) if ac[y * 480 + x][0] > 200 and ac[y * 480 + x][1] < 170) < 60: err.append('acerca: no se ve el correo')
if claros(340, 359, 230, 300) > 0: err.append('acerca: los créditos se meten en el botón Atrás')
# ---- etapa 30: textos de magna_extras.inc (capa, faltan, fin, hora, fecha)
r = subprocess.run([exe, A, '/tmp/render_textos.raw', 'textos'], capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode: err.append('textos de magna_extras.inc: ' + r.stdout.strip().splitlines()[-1])
# ---- etapa 30: pantalla de impresión con la línea de información y la hora chica
i2 = dibujar('impresion2')
if not es_rojo(i2[52 * 480 + 230]): err.append('impresion2: la barra no se pinta de rojo')
if sum(1 for y in range(73, 90) for x in range(210, 470) if i2[y * 480 + x][0] > 200 and i2[y * 480 + x][1] > 150) < 80: err.append('impresion2: no se ve la línea "Capa · faltan · fin"')
if sum(1 for y in range(8, 26) for x in range(215, 265) if min(i2[y * 480 + x]) > 160) < 20: err.append('impresion2: no se ve la hora chica arriba al medio')
if any(min(i2[y * 480 + x]) > 200 for y in range(73, 86) for x in range(205, 212)) and False: pass
# ---- etapa 30: principal con hora grande, fecha e íconos
p2 = dibujar('principal2')
if sum(1 for y in range(16, 46) for x in range(390, 460) if min(p2[y * 480 + x]) > 200) < 120: err.append('principal2: no se ve la hora grande')
if sum(1 for y in range(30, 52) for x in range(340, 380) if min(p2[y * 480 + x]) > 200) < 25: err.append('principal2: no se ve el ícono de WiFi')
if sum(1 for y in range(28, 58) for x in range(298, 330) if min(p2[y * 480 + x]) > 200) < 25: err.append('principal2: no se ve el ícono de Telegram')
if sum(1 for y in range(8, 26) for x in range(430, 478) if min(p2[y * 480 + x]) > 160 and y < 14) > 0: err.append('principal2: la hora chica no se tiene que ver en la principal')
# ---- etapa 31: resumen, mensaje, bloqueo y "siempre encendida"
rs = dibujar('resumen')
if sum(1 for y in range(96, 240) for x in range(250, 412) if min(rs[y * 480 + x]) > 200) < 300: err.append('resumen: no se ven los valores')
if any(min(rs[y * 480 + x]) > 200 for y in range(236, 248) for x in range(60, 420)): err.append('resumen: el texto pisa los botones')
mj = dibujar('mensaje')
if not es_rojo(mj[60 * 480 + 240]): err.append('mensaje: falta el borde rojo de la caja')
if sum(1 for y in range(100, 190) for x in range(60, 420) if min(mj[y * 480 + x]) > 200) < 200: err.append('mensaje: no se ve el texto')
if max(mj[20 * 480 + 20]) > 40: err.append('mensaje: el fondo no se oscurece')
bq = dibujar('bloqueo')
if sum(1 for y in range(140, 175) for x in range(100, 380) if min(bq[y * 480 + x]) > 200) < 200: err.append('bloqueo: no se ve "Pantalla bloqueada"')
if not es_rojo(bq[222 * 480 + 112]): err.append('bloqueo: falta la perilla roja del deslizador')
am = dibujar('ambiente')
if sum(1 for y in range(70, 160) for x in range(120, 360) if am[y * 480 + x][0] > 100 and am[y * 480 + x][1] < 60) < 500: err.append('ambiente: no se ve el porcentaje enorme')
if max(am[300 * 480 + 20]) > 10 or max(am[150 * 480 + 20]) > 10: err.append('ambiente: el fondo no es negro')
# ---- etapa 33: gráfico, nivelación, piezas y vista en vivo
gr = dibujar('grafico')
if sum(1 for y in range(40, 240) for x in range(50, 470) if gr[y * 480 + x][0] > 200 and gr[y * 480 + x][1] < 120) < 150: err.append('grafico: no se ve la línea del hotend')
nv = dibujar('nivel')
if sum(1 for y in range(40, 260) for x in range(20, 240) if nv[y * 480 + x][1] > 120 and nv[y * 480 + x][0] < 80) < 2000: err.append('nivel: no se ven las celdas verdes')
pz = dibujar('piezas')
if sum(1 for y in range(40, 200) for x in range(330, 460) if es_rojo(pz[y * 480 + x])) < 100: err.append('piezas: no se ven los botones Cancelar')
vv = dibujar('vivo')
if sum(1 for y in range(36, 236) for x in range(2, 202) if min(vv[y * 480 + x]) > 200) < 300: err.append('vivo: no se ve el recorrido')
for e in err: print('MAL ', e)
print('OK: los íconos se dibujan bien con la LVGL de la pantalla' if not err else f'FALLA: {len(err)} problemas'); sys.exit(1 if err else 0)
