#!/usr/bin/env python3
"""Valida los perfiles de slicer: archivos bien formados, ajustes que existen en Cura,
valores dentro de los rangos de Cura y coherencia con el firmware.

Uso: python3 pruebas/verificar-perfiles.py  (desde la raíz del proyecto)

pruebas/datos/cura-5.10-ajustes.json es una foto de los ajustes de Cura 5.10
(fdmprinter + fdmextruder): nombre, tipo, opciones y mínimos/máximos. Sirve para detectar
ajustes mal escritos o valores que Cura marcaría en rojo, sin tener Cura instalado.
"""
import configparser
import glob
import json
import os
import re
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = os.path.join(R, 'perfiles-slicer')
cfg = open(os.path.join(R, 'Marlin/Configuration.h'), encoding='utf-8').read()
adv = open(os.path.join(R, 'Marlin/Configuration_adv.h'), encoding='utf-8').read()
AJ = json.load(open(os.path.join(R, 'pruebas/datos/cura-5.10-ajustes.json'), encoding='utf-8'))
sys.path.insert(0, P)
import generar_perfiles as G  # noqa: E402  (los valores de referencia)


def fw(name, txt=None):
    m = re.search(r'^\s*#define\s+' + name + r'\s+(.+?)\s*(//.*)?$', txt or cfg, re.M)
    return m.group(1)


errores = []


def ok(cond, msg):
    print(('ok   ' if cond else 'MAL  ') + msg)
    if not cond:
        errores.append(msg)


# ------------------------------------------------------------------ 1) archivos bien formados
for f in sorted(glob.glob(os.path.join(P, '**/*.json'), recursive=True)):
    try:
        json.load(open(f, encoding='utf-8'))
        ok(True, 'JSON valido ' + os.path.relpath(f, P))
    except Exception as e:
        ok(False, f'JSON invalido {f}: {e}')

ini = configparser.ConfigParser(interpolation=None, strict=False)
ini.optionxform = str
ini.read(os.path.join(P, 'prusaslicer/Magna2-230_PrusaSlicer_bundle.ini'), encoding='utf-8')
pr = ini['printer:Magna 2 230 Marlin 2.1']
ok(len([s for s in ini.sections() if s.startswith('print:')]) == len(G.PROCESOS), f'Prusa: {len(G.PROCESOS)} procesos')
ok(len([s for s in ini.sections() if s.startswith('filament:')]) == len(G.FILAMENTOS), f'Prusa: {len(G.FILAMENTOS)} filamentos')

# ------------------------------------------------------------------ 2) Cura
CID = G.CURA_ID
defi = json.load(open(os.path.join(P, f'cura/definitions/{CID}.def.json'), encoding='utf-8'))
cura = defi['overrides']
exts = [json.load(open(os.path.join(P, f'cura/extruders/{CID}_extruder_{n}.def.json'), encoding='utf-8')) for n in range(2)]
ok(defi['metadata']['machine_extruder_trains'] == {str(n): f'{CID}_extruder_{n}' for n in range(2)}, 'Cura: extrusores enlazados a la maquina')
ok(all(e['metadata']['machine'] == CID for e in exts), 'Cura: extrusores apuntan a la maquina')
ok(defi['metadata'].get('has_machine_quality') is True, 'Cura: usa calidades propias')

# valores conocidos para evaluar mínimos/máximos que son fórmulas
ns = {k: (v.get('default_value', v.get('value'))) for k, v in cura.items()}
ns.update({'machine_nozzle_size': G.MAQUINA['boquilla'], 'layer_height': 0.2, 'line_width': 0.4,
           'wall_line_width_0': 0.4, 'infill_line_width': 0.4, 'retraction_amount': 5,
           'machine_max_feedrate_e': G.MAQUINA['vmax']['e'], 'retraction_enable': True, 'skirt_brim_line_width': 0.4, 'math': __import__('math'),
           'extruderValue': lambda *a: None, 'resolveOrValue': lambda *a: None})


def literal(v):
    """Valor simple de un ajuste ('=' fórmula o expresión de Cura -> None)."""
    if isinstance(v, str):
        if v.startswith('='):
            return None
        try:
            return json.loads(v)
        except Exception:
            return v.strip("'") if v.startswith("'") else v
    return v


def revisar(origen, clave, valor):
    if clave not in AJ:
        ok(False, f'{origen}: ajuste inexistente en Cura "{clave}"')
        return
    info = AJ[clave]
    v = literal(valor)
    if v is None or isinstance(v, str) and info.get('type') not in ('enum', 'str'):
        return
    if info.get('type') == 'enum' and isinstance(v, str):
        ok(v in info.get('options', {}), f'{origen}: {clave}={v} es una opcion valida')
        return
    for lim, cmp in (('minimum_value', lambda a, b: a >= b), ('maximum_value', lambda a, b: a <= b)):
        if lim in info and isinstance(v, (int, float)) and not isinstance(v, bool):
            try:
                tope = eval(str(info[lim]), {}, ns)
            except Exception:
                continue
            if isinstance(tope, (int, float)):
                ok(cmp(v, tope), f'{origen}: {clave}={v} respeta {lim} ({tope})')


malas = 0
for k, v in cura.items():
    revisar('Cura def', k, v.get('default_value', v.get('value')))
for n, e in enumerate(exts):
    for k, v in e['overrides'].items():
        revisar(f'Cura ext{n}', k, v.get('default_value', v.get('value')))

# calidades
qdir = os.path.join(P, f'cura/quality/{CID}')
q = {}
for f in sorted(glob.glob(os.path.join(qdir, '*.inst.cfg'))):
    c = configparser.ConfigParser(interpolation=None)
    c.optionxform = str
    c.read(f, encoding='utf-8')
    nombre = os.path.basename(f)
    ok(c['general']['definition'] == CID and c['general']['version'] == '4', f'Calidad {nombre}: cabecera correcta')
    ok(c['metadata']['type'] == 'quality' and c['metadata']['setting_version'] == str(G.CURA_SETTING_VERSION),
       f'Calidad {nombre}: tipo y setting_version {G.CURA_SETTING_VERSION}')
    clave = (c['metadata'].get('material', 'global'), c['metadata']['quality_type'])
    q[clave] = c
    for k, v in c['values'].items():
        revisar(f'Calidad {nombre}', k, v)
tipos = {p['q'] for p in G.PROCESOS}
for mat in ['global'] + [f['cura'] for f in G.FILAMENTOS]:
    ok({t for (m_, t) in q if m_ == mat} == tipos, f'Cura: {mat} tiene las {len(tipos)} calidades')
for p in G.PROCESOS:
    ok(float(q[('global', p['q'])]['values']['layer_height']) == p['capa'], f'Cura: calidad {p["q"]} = capa {p["capa"]}')

# ------------------------------------------------------------------ 3) coherencia con el firmware
X, Y, Z = int(fw('X_BED_SIZE')), int(fw('Y_BED_SIZE')), int(fw('Z_MAX_POS'))
orca = json.load(open(os.path.join(P, 'orcaslicer/machine/Magna2-230_machine.json'), encoding='utf-8'))
ok(cura['machine_width']['default_value'] == X and cura['machine_depth']['default_value'] == Y and cura['machine_height']['default_value'] == Z, 'Cura: tamano = firmware')
ok(pr['bed_shape'] == f'0x0,{X}x0,{X}x{Y},0x{Y}' and int(pr['max_print_height']) == Z, 'Prusa: tamano = firmware')
ok(orca['printable_area'][2] == f'{X}x{Y}' and int(orca['printable_height']) == Z, 'Orca: tamano = firmware')
ok(int(fw('EXTRUDERS')) == cura['machine_extruder_count']['default_value'] == len(pr['nozzle_diameter'].split(',')) == len(orca['nozzle_diameter']), 'Cantidad de extrusores = firmware')
ok('SINGLENOZZLE' in cfg and cura['machine_extruders_share_nozzle']['default_value'] and pr['single_extruder_multi_material'] == '1' and orca['single_extruder_multi_material'] == '1', 'Boquilla unica (2 en 1) en firmware y slicers')

vmax = [s.strip() for s in fw('DEFAULT_MAX_FEEDRATE').strip('{} ').split(',')]
ok(pr['machine_max_feedrate_x'] == vmax[0] and orca['machine_max_speed_x'] == [vmax[0]], 'Velocidad max X = firmware')
emax = float(vmax[3])
ok(float(G.MAQUINA['vmax']['e']) == emax, 'Velocidad max E del generador = firmware')
ok(all(f['vel_retr'] <= emax for f in G.FILAMENTOS) and G.CAMBIO['velocidad'] <= emax, 'Retracciones no superan la velocidad max del extrusor')

# cambio 2 en 1: lo hace el slicer, el firmware queda apagado
L = G.CAMBIO['largo']
ok(re.search(r'^\s*#define TOOLCHANGE_FS_LENGTH 0\b', adv, re.M) is not None, 'Firmware: TOOLCHANGE_FS_LENGTH 0 (cambio a cargo del slicer)')
ok(int(fw('EXTRUDE_MAXLENGTH')) >= L, f'Firmware: EXTRUDE_MAXLENGTH permite mover {L} mm')
s0 = cura['machine_start_gcode']['default_value']
ok('M217 S0' in s0 and 'M217 S0' in pr['start_gcode'] and 'M217 S0' in orca['machine_start_gcode'], 'Los tres slicers apagan el cambio del firmware (M217 S0)')


def e_total(codigo, signo):
    """Suma los movimientos de E de un gcode: signo +1 = cargas, -1 = retiros."""
    patron = r'G1 [^;\n]*E-([\d.]+)' if signo < 0 else r'G1 [^;\n]*E([\d.]+)'
    return sum(float(x) for x in re.findall(patron, codigo))


ini_ret = cura['machine_extruders_shared_nozzle_initial_retraction']['default_value']
sw = cura['switch_extruder_retraction_amount']['value']
for n, e in enumerate(exts):
    o = e['overrides']
    carga = e_total(o['machine_extruder_start_code']['default_value'], +1)
    desc = e_total(o['machine_extruder_end_code']['default_value'], -1)
    ok(carga + ini_ret == L and carga + sw == L, f'Cura T{n}: carga {carga} + {sw} des-retraccion = {L} mm')
    ok(desc + sw == L, f'Cura T{n}: estaciona {desc} + {sw} retraccion = {L} mm')
    zs = re.findall(r'G1 Z(-?[\d.]+)', o['machine_extruder_start_code']['default_value'] + o['machine_extruder_end_code']['default_value'])
    ok(sum(float(z) for z in zs) == 0, f'Cura T{n}: subida y bajada de Z se compensan')
ok(int(pr['parking_pos_retraction']) == L and orca['parking_pos_retraction'] == str(L), f'Prusa/Orca: estacionado a {L} mm')
ok(e_total(pr['start_gcode'].replace('\\n', '\n'), +1) >= L and e_total(pr['end_gcode'].replace('\\n', '\n'), -1) == L, 'Prusa: carga al inicio y estaciona al final')
ok(pr['toolchange_gcode'].startswith('T[next_extruder]'), 'Prusa: el toolchange_gcode emite el comando T')
for n in range(2):
    est = open(os.path.join(P, f'gcode-utiles/estacionar_T{n}.gcode'), encoding='utf-8').read()
    ok(f'T{n}' in est and e_total(est, -1) == L and 'M109' in est, f'gcode-utiles: estacionar_T{n} retira {L} mm en caliente')

# movimientos dentro de la cama
codigos = [('Cura inicio', s0), ('Prusa', pr['start_gcode']), ('Orca', orca['machine_start_gcode'])]
codigos += [(f'Cura ext{n}', e['overrides']['machine_extruder_start_code']['default_value'] + e['overrides']['machine_extruder_end_code']['default_value']) for n, e in enumerate(exts)]
for nombre, txt in codigos:
    ok('{TEMP0}' not in txt and '{BED0}' not in txt, f'{nombre}: sin marcadores sin reemplazar')
    for xy in re.findall(r'X([\d.]+) Y([\d.]+)', txt.replace('\\n', '\n')):
        ok(float(xy[0]) <= X and float(xy[1]) <= Y, f'{nombre}: movimiento X{xy[0]} Y{xy[1]} dentro de la cama')

print('\nRESULTADO:', 'OK' if not errores else f'{len(errores)} errores')
sys.exit(1 if errores else 0)
