#!/usr/bin/env python3
"""
Versión liviana de los extras de la pantalla, para la placa MKS Robin Nano V1.2 (mm12).

La V1.2 tiene un STM32F103 (72 MHz, 64 KB de RAM). Marlin solo, con la configuración de la Magna y la
pantalla MKS, ya usa ~62 KB: los extras completos (~11 KB de RAM) no entran. Este script deja las
funciones de magna_extras.cpp que ocupan memoria o procesador como funciones vacías, con el mismo
nombre: los cambios en los archivos de MKS siguen llamándolas igual (no hay que tocarlos) y el
enlazador descarta lo que ya nadie usa (por ejemplo los 5 KB de la vista en vivo).

Queda: tema, castellano, hora chica, línea de información al imprimir, mensajes de MagnAir, M256/M257/
M258/M262/M264, aviso de error grave, melodías, créditos.
Sale: animaciones, arranque animado, gráfico, QR de la nube de Makerbase, "siempre encendida", vista en vivo, cancelar piezas desde
la pantalla, resumen al terminar, bloqueo, nivelación en vivo, hora grande y fecha de la principal.

Solo actúa si Marlin/Configuration.h tiene "#define MAGNA_LIVIANO" (lo pone variantes/placa12.py).
Lo llama aplicar_colores.py al final. Uso: python3 liviano.py <raíz del proyecto>
"""
import os
import re
import sys

RAIZ = sys.argv[1] if len(sys.argv) > 1 else '.'
cfg = open(os.path.join(RAIZ, 'Marlin/Configuration.h'), encoding='utf-8').read()
if not re.search(r'^\s*#define MAGNA_LIVIANO\b', cfg, re.M):
    print('Liviano: no (placa V1.3)')
    sys.exit(0)

P = os.path.join(RAIZ, 'Marlin/src/lcd/extui/mks_ui/magna_extras.cpp')
s = open(P, encoding='utf-8').read()
MARCA = '/* MAGNA_LIVIANO (mm12): '

# nombre -> cuerpo nuevo
VACIAS = {
    # vista en vivo (5 kB de RAM)
    'magna_vista_linea': '', 'magna_vista_crear': '', 'magna_vista_crear_impresion': '',
    'magna_vista_reiniciar': '',
    # gráfico de temperaturas
    'magna_hist_agregar': '', 'magna_grafico_abrir': '', 'magna_boton_grafico_principal': '',
    # piezas (cancelar una desde la pantalla)
    'magna_piezas_abrir': '', 'magna_botones_impresion': '', 'magna_pieza_indice': 'return -1;',
    # "siempre encendida"
    'magna_ambiente_mostrar': '', 'magna_ambiente_actualizar': '', 'magna_ambiente_cerrar': '',
    'magna_ambiente_en_vez_de_apagar': 'return false;', 'magna_ambiente_visible': 'return 0;',
    # animaciones
    'magna_anim_iconos': '', 'magna_anim_registrar': '', 'magna_anim_datos': '', 'magna_anim_iniciar': '',
    'magna_arranque_animado': '',
    # bloqueo y resumen
    'magna_bloquear': '', 'magna_candado_crear': '', 'magna_resumen': '',
    # nivelación en vivo (BLTouch)
    'magna_nivel_abrir': '', 'magna_nivel_actualizar': '', 'magna_nivel_abierto': 'return 0;',
    # hora grande, fecha e íconos de la principal (la hora chica se muestra también ahí, ver abajo)
    'magna_principal_crear': '', 'magna_principal_actualizar': '',
    # tareas que tocan el gráfico y la vista en vivo
    'magna_extras33_tick': 'mg_cerrar_pendientes();',
}


def cuerpo(s, nombre):
    """(inicio, fin) del cuerpo { ... } de la función definida como 'tipo nombre(...) {' al principio de una línea."""
    m = re.search(r'^[\w][\w \*]*\b' + nombre + r'\s*\([^;{]*\)\s*\{', s, re.M)
    if not m:
        return None
    i = m.end() - 1
    nivel = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            nivel += 1
        elif s[j] == '}':
            nivel -= 1
            if nivel == 0:
                return i, j + 1
    return None


hechas, faltan = [], []
if MARCA in s:
    print('Liviano: ya aplicado')
    sys.exit(0)
for nombre, nuevo in VACIAS.items():
    r = cuerpo(s, nombre)
    if not r:
        faltan.append(nombre)
        continue
    a, b = r
    s = s[:a] + '{ ' + MARCA + 'no está en la placa V1.2 */ ' + nuevo + ' }' + s[b:]
    hechas.append(nombre)

# La hora chica se ve también en la principal (no está la hora grande)
viejo = '  magna_reloj_mostrar(ahora, !principal);'
if s.count(viejo) == 1:
    s = s.replace(viejo, '  magna_reloj_mostrar(ahora, 1);  ' + MARCA + 'sin hora grande, la chica va en todas */')
    hechas.append('hora chica en la principal')
else:
    faltan.append('hora chica en la principal')

open(P, 'w', encoding='utf-8').write(s)

# Código de MKS: el código QR de la "nube" de Makerbase (servicio que ya no existe; MagnAir no lo usa)
# ocupa ~2,3 KB de RAM en tablas.
Q = os.path.join(RAIZ, 'Marlin/src/lcd/extui/mks_ui/draw_cloud_bind.cpp')
q = open(Q, encoding='utf-8').read()
r = cuerpo(q, 'display_qrcode')
if r:
    q = q[:r[0]] + '{ ' + MARCA + 'sin QR de la nube de Makerbase (RAM) */ (void)qrcode_data; }' + q[r[1]:]
    open(Q, 'w', encoding='utf-8').write(q)
    hechas.append('QR de la nube')
else:
    faltan.append('display_qrcode')

print(f'Liviano (placa V1.2): {len(hechas)} cambios')
if faltan:
    # una función que falta puede ser de una variante (p. ej. la nivelación en vivo solo con BLTouch);
    # si falta otra cosa, es un error
    graves = [f for f in faltan if not f.startswith('magna_nivel')]
    print('  no encontradas:', ', '.join(faltan))
    if graves:
        sys.exit('Liviano: faltan ' + ', '.join(graves))
