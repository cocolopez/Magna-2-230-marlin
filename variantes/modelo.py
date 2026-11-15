#!/usr/bin/env python3
"""
Variantes del firmware para las otras Magna 2: 300, 400, 400D, 500 y 500D.

El código es el mismo que el de la 230; este script cambia solo los valores de la máquina en
Marlin/Configuration.h y Configuration_adv.h, con reemplazos exactos (si alguno no se encuentra,
FALLA: mejor no compilar que compilar algo a medias). Es idempotente.

De dónde salen los valores: de los firmware oficiales de Hellbot (Marlin 2.0.3 de MKS, "Placa
v1.3"). En esos paquetes el .bin es el mismo para todos los modelos y lo que cambia es
robin_nano35_cfg.txt; los valores de abajo están copiados de ahí (ver docs-magna/MODELOS.md).
Los paquetes "D" (extrusor directo) traen exactamente los mismos archivos que el modelo sin D.

Lo que NO sale del oficial (decisiones propias, explicadas en MODELOS.md):
  * Entrada Z máximo apagada (la 300 oficial la usa; acá el tope de Z lo controla el firmware).
  * Protección de temperatura de la cama más larga: las camas grandes tardan en calentar.
  * Cama sin PID (como el oficial): las de 400 y 500 parecen de 220 V con relé.
  * Extrusor: se mantienen las velocidades del extrusor de la 230 (mismo extrusor Hellbot).
  * 400/500: BLTouch como en la variante BLTouch de la 230, con el offset del oficial (-30, 0)
    y malla de 7x7 (el oficial usa 8x8: 64 toques en cada nivelación).
  * D: al cambiar filamento descarga 50 mm en vez de 100 (no hay tubo bowden).
  * Puntos de nivelación manual: la pantalla los calcula sola a 30 mm de cada borde según el
    tamaño de la cama (los del oficial de 400/500 eran los de la 230 sin cambiar).

Uso: python3 variantes/modelo.py MODELO [raíz del proyecto]
     MODELO = 300, 400, 400D, 500 o 500D. Para 400 y 500 corre también variantes/bltouch.py.
"""
import os
import subprocess
import sys

MODELOS = {
    #        cama X/Y, Z,  pasos Z, pasos E, vel máx XY, vel máx Z, acel máx XY, acel, cama máx, BLTouch, directo
    '300':  dict(xy=300, z=400, pz=400.5, pe=400, vxy=200, vz=4, axy=800, acel=800, cama=110, bltouch=False, directo=False),
    '400':  dict(xy=400, z=400, pz=400.5, pe=415, vxy=100, vz=5, axy=200, acel=500, cama=95, bltouch=True, directo=False),
    '400D': dict(xy=400, z=400, pz=400.5, pe=415, vxy=100, vz=5, axy=200, acel=500, cama=95, bltouch=True, directo=True),
    '500':  dict(xy=500, z=500, pz=400.5, pe=415, vxy=100, vz=5, axy=200, acel=500, cama=95, bltouch=True, directo=False),
    '500D': dict(xy=500, z=500, pz=400.5, pe=415, vxy=100, vz=5, axy=200, acel=500, cama=95, bltouch=True, directo=True),
}

if len(sys.argv) < 2 or sys.argv[1].upper() not in MODELOS:
    sys.exit('Uso: modelo.py 300|400|400D|500|500D [raíz]')
NOMBRE = sys.argv[1].upper()
M = MODELOS[NOMBRE]
R = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MARCA = f'  // Magna2-{NOMBRE}'

if M['bltouch']:
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bltouch.py'), R])
    if r.returncode:
        sys.exit(r.returncode)

# Cama: el oficial de 400/500 tiene máximo 95 °C; con BED_OVERSHOOT de 10 se puede pedir hasta 85.
# El ABS de fábrica (110) queda en lo máximo que deja cada cama.
abs_cama = min(110, M['cama'] - 10)
# Cuánto tarda en calentar: más grande, más tiempo antes de dar "Heating failed"
watch_cama = {300: 120, 400: 240, 500: 300}[M['xy']]
prot_cama = {300: 60, 400: 90, 500: 90}[M['xy']]

CAMBIOS = {
    'Marlin/Configuration.h': [
        ('#define STRING_CONFIG_H_AUTHOR "(Magna 2 230 - Robin Nano 1.3 - TFT35)"  // Magna2-230',
         f'#define STRING_CONFIG_H_AUTHOR "(Magna 2 {NOMBRE} - Robin Nano 1.3 - TFT35)"' + MARCA),
        ('#define CUSTOM_MACHINE_NAME "Magna 2 230"  // Magna2-230',
         f'#define CUSTOM_MACHINE_NAME "Magna 2 {NOMBRE}"' + MARCA + ': MagnAir reconoce el modelo por este nombre\n'
         '#define MAGNA_SIN_PROBAR' + MARCA + ': nadie lo probó en una máquina real todavía (Acerca de lo muestra)'),
        ('#define X_BED_SIZE 230  // Magna2-230', f'#define X_BED_SIZE {M["xy"]}' + MARCA),
        ('#define Y_BED_SIZE 230  // Magna2-230', f'#define Y_BED_SIZE {M["xy"]}' + MARCA),
        ('#define Z_MAX_POS 250  // Magna2-230', f'#define Z_MAX_POS {M["z"]}' + MARCA),
        ('#define INVERT_Z_DIR true  // Magna2-230: verificado en el bin original',
         '#define INVERT_Z_DIR false' + MARCA + ': así está en el oficial (en la 230 es al revés)'),
        ('#define DEFAULT_AXIS_STEPS_PER_UNIT { 80, 80, 400, 425, 423 }  // Magna2-230: X Y Z E0 E1 (del bin original)',
         f'#define DEFAULT_AXIS_STEPS_PER_UNIT {{ 80, 80, {M["pz"]}, {M["pe"]}, {M["pe"]} }}' + MARCA + ': X Y Z E0 E1 (del oficial)'),
        ('#define DEFAULT_MAX_FEEDRATE { 300, 300, 5, 25, 25 }  // Magna2-230',
         f'#define DEFAULT_MAX_FEEDRATE {{ {M["vxy"]}, {M["vxy"]}, {M["vz"]}, 25, 25 }}' + MARCA),
        ('#define DEFAULT_MAX_ACCELERATION { 2000, 2000, 100, 8000, 8000 }  // Magna2-230',
         f'#define DEFAULT_MAX_ACCELERATION {{ {M["axy"]}, {M["axy"]}, 100, 8000, 8000 }}' + MARCA),
        ('#define DEFAULT_ACCELERATION 2000  // Magna2-230', f'#define DEFAULT_ACCELERATION {M["acel"]}' + MARCA),
        ('#define DEFAULT_RETRACT_ACCELERATION 2000  // Magna2-230', f'#define DEFAULT_RETRACT_ACCELERATION {M["acel"]}' + MARCA),
        ('#define DEFAULT_TRAVEL_ACCELERATION 2000  // Magna2-230', f'#define DEFAULT_TRAVEL_ACCELERATION {M["acel"]}' + MARCA),
        ('#define HOMING_FEEDRATE_MM_M { (50*60), (50*60), (5*60) }  // Magna2-230',
         f'#define HOMING_FEEDRATE_MM_M {{ (40*60), (40*60), ({M["vz"]}*60) }}' + MARCA + ': 2400 mm/min como el oficial'),
        ('#define BED_MAXTEMP 120  // Magna2-230', f'#define BED_MAXTEMP {M["cama"]}' + MARCA + ': del oficial'),
        ('#define PIDTEMPBED  // Magna2-230', '//#define PIDTEMPBED' + MARCA + ': cama sin PID, como el oficial'),
        ('#define PREHEAT_2_TEMP_BED    110', f'#define PREHEAT_2_TEMP_BED    {abs_cama}' + MARCA + ': lo máximo que deja la cama'),
    ],
    'Marlin/Configuration_adv.h': [
        ('  #define THERMAL_PROTECTION_BED_PERIOD        20 // (seconds)',
         f'  #define THERMAL_PROTECTION_BED_PERIOD        {prot_cama}' + MARCA + ': cama grande'),
        ('  #define WATCH_BED_TEMP_PERIOD                60 // (seconds)',
         f'  #define WATCH_BED_TEMP_PERIOD                {watch_cama}' + MARCA + ': cama grande, tarda en calentar'),
    ],
}

if M['bltouch']:
    CAMBIOS['Marlin/Configuration.h'] += [
        ('#define NOZZLE_TO_PROBE_OFFSET { 0, 0, 0 }  // Magna2-230 BLTouch: medir y cargar en la pantalla o con M851 X.. Y.. Z.. + M500',
         '#define NOZZLE_TO_PROBE_OFFSET { -30, 0, 0 }' + MARCA + ': X/Y del oficial; Z se calibra con el asistente'),
        ('#define PROBING_MARGIN 45  // Magna2-230 BLTouch: seguro para soportes de hasta 45 mm',
         '#define PROBING_MARGIN 20' + MARCA),
        ('  #define GRID_MAX_POINTS_X 5  // Magna2-230 BLTouch',
         '  #define GRID_MAX_POINTS_X 7' + MARCA + ': el oficial usa 8x8'),
    ]

if M['directo']:
    CAMBIOS['Marlin/Configuration_adv.h'].append(
        ('  #define FILAMENT_CHANGE_UNLOAD_LENGTH      100  // (mm) The length of filament for a complete unload.',
         '  #define FILAMENT_CHANGE_UNLOAD_LENGTH       50' + MARCA + ': extrusor directo, sin tubo'))

errores = 0
for archivo, cambios in CAMBIOS.items():
    p = os.path.join(R, archivo)
    s = open(p, encoding='utf-8').read()
    for viejo, nuevo in cambios:
        if nuevo in s:
            continue
        if s.count(viejo) != 1:
            print(f'NO ENCONTRADO en {archivo}: {viejo[:90]}')
            errores += 1
            continue
        s = s.replace(viejo, nuevo)
    open(p, 'w', encoding='utf-8').write(s)

# Entrada Z máximo: en la 230 no se usa; se verifica que siga así.
cfg = open(os.path.join(R, 'Marlin/Configuration.h'), encoding='utf-8').read()
if '\n#define USE_ZMAX_PLUG' in cfg:
    print('La entrada Z máximo está activada: debería estar apagada')
    errores += 1

if errores:
    sys.exit(f'Variante {NOMBRE}: {errores} cambios no se pudieron aplicar')
print(f'Variante Magna 2 {NOMBRE} aplicada')
