#!/usr/bin/env python3
"""Valida los perfiles de slicer: JSON/INI bien formados y coherentes con el firmware.
Uso: python3 pruebas/verificar-perfiles.py  (desde la raíz del proyecto)"""
import json, os, re, sys, configparser, glob
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = os.path.join(R, 'perfiles-slicer')
cfg = open(os.path.join(R, 'Marlin/Configuration.h'), encoding='utf-8').read()
def fw(name):
    m = re.search(r'^\s*#define\s+' + name + r'\s+(.+?)\s*(//.*)?$', cfg, re.M); return m.group(1)
errores = []
def ok(cond, msg):
    print(('ok   ' if cond else 'MAL  ') + msg)
    if not cond: errores.append(msg)

# 1) JSON válidos
for f in glob.glob(os.path.join(P, '**/*.json'), recursive=True):
    try: json.load(open(f, encoding='utf-8')); ok(True, 'JSON valido ' + os.path.relpath(f, P))
    except Exception as e: ok(False, f'JSON invalido {f}: {e}')

# 2) INI de PrusaSlicer parseable
ini = configparser.ConfigParser(interpolation=None, strict=False)
ini.optionxform = str
ini.read(os.path.join(P, 'prusaslicer/Magna2-230_PrusaSlicer_bundle.ini'), encoding='utf-8')
pr = ini['printer:Magna 2 230 Marlin 2.1']
ok(len([s for s in ini.sections() if s.startswith('print:')]) == 3, 'Prusa: 3 procesos')
ok(len([s for s in ini.sections() if s.startswith('filament:')]) == 3, 'Prusa: 3 filamentos')

# 3) coherencia con el firmware
X, Y, Z = int(fw('X_BED_SIZE')), int(fw('Y_BED_SIZE')), int(fw('Z_MAX_POS'))
cura = json.load(open(os.path.join(P, 'cura/definitions/hellbot_magna2_230_marlin.def.json'), encoding='utf-8'))['overrides']
orca = json.load(open(os.path.join(P, 'orcaslicer/machine/Magna2-230_machine.json'), encoding='utf-8'))
ok(cura['machine_width']['default_value'] == X and cura['machine_depth']['default_value'] == Y and cura['machine_height']['default_value'] == Z, 'Cura: tamano = firmware')
ok(pr['bed_shape'] == f'0x0,{X}x0,{X}x{Y},0x{Y}' and int(pr['max_print_height']) == Z, 'Prusa: tamano = firmware')
ok(orca['printable_area'][2] == f'{X}x{Y}' and int(orca['printable_height']) == Z, 'Orca: tamano = firmware')
ok(int(fw('EXTRUDERS')) == cura['machine_extruder_count']['default_value'] == len(pr['nozzle_diameter'].split(',')) == len(orca['nozzle_diameter']), 'Cantidad de extrusores = firmware')
ok('SINGLENOZZLE' in cfg and cura['machine_extruders_share_nozzle']['default_value'] and pr['single_extruder_multi_material'] == '1' and orca['single_extruder_multi_material'] == '1', 'Boquilla unica (2 en 1) en firmware y slicers')
ok(re.search(r'^\s*#define TOOLCHANGE_FILAMENT_SWAP', open(os.path.join(R, 'Marlin/Configuration_adv.h'), encoding='utf-8').read(), re.M) is not None
   and cura['switch_extruder_retraction_amount']['value'] == 0 and pr['retract_length_toolchange'] == '0,0' and orca['retract_length_toolchange'] == ['0', '0'],
   'Cambio de filamento: lo hace el firmware y los slicers no retraen de mas')
ok(pr['toolchange_gcode'].startswith('T[next_extruder]'), 'Prusa: el toolchange_gcode emite el comando T')
vmax = [s.strip() for s in fw('DEFAULT_MAX_FEEDRATE').strip('{} ').split(',')]
ok(pr['machine_max_feedrate_x'] == vmax[0] and orca['machine_max_speed_x'] == [vmax[0]], 'Velocidad max X = firmware')
for txt, nombre in ((cura['machine_start_gcode']['default_value'], 'Cura'), (pr['start_gcode'], 'Prusa'), (orca['machine_start_gcode'], 'Orca')):
    ok('{TEMP0}' not in txt and '{BED0}' not in txt and 'G28' in txt, f'{nombre}: gcode de inicio completo')
    for xy in re.findall(r'X([\d.]+) Y([\d.]+)', txt.replace('\\n', '\n')):
        ok(float(xy[0]) <= X and float(xy[1]) <= Y, f'{nombre}: movimiento X{xy[0]} Y{xy[1]} dentro de la cama')
print('\nRESULTADO:', 'OK' if not errores else f'{len(errores)} errores'); sys.exit(1 if errores else 0)
