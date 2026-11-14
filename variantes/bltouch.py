#!/usr/bin/env python3
"""
Variante BLTouch del firmware Magna 2 230.

Convierte la configuración normal (fin de carrera de Z mecánico, nivelación manual de 5 puntos)
en la de BLTouch, con reemplazos exactos en Marlin/Configuration.h y Configuration_adv.h.
Si algún reemplazo no se encuentra, FALLA (mejor no compilar que compilar algo a medias).
Es idempotente: si ya está aplicada, no cambia nada.

Conexión en la MKS Robin Nano V1.3:
  * cable de 3 hilos del BLTouch (marrón GND, rojo 5V, naranja/amarillo señal del servo) -> conector
    "BLTouch" (PA8, SERVO0_PIN de Marlin);
  * cable de 2 hilos (negro GND, blanco señal) -> conector del fin de carrera Z- (Z_MIN), en lugar
    del fin de carrera mecánico de Z, que se desenchufa.

Qué cambia:
  * BLTOUCH, señal de Z en HIGH (el BLTouch se activa en alto);
  * nivelación automática BILINEAR de 5x5 puntos, Z_SAFE_HOMING (home de Z en el centro de la cama);
  * ENABLE_LEVELING_AFTER_G28: después de cada G28 se activa la malla guardada (no hace falta M420
    en el slicer);
  * offset de la sonda X/Y/Z = 0 y margen de 45 mm: con cualquier soporte de hasta 45 mm de
    distancia, la sonda queda dentro de la cama al medir. Z = 0 es la opción segura: si no se
    calibra, la boquilla queda en el aire y no choca. Se calibra con el asistente de offset Z
    (PROBE_OFFSET_WIZARD) y el offset X/Y en la pantalla (ver docs-magna/BLTOUCH.md);
  * BABYSTEP_ZPROBE_OFFSET: el babystep de la primera capa corrige y guarda el offset de la sonda;
  * MULTIPLE_PROBING 2 (toca dos veces cada punto, más preciso).

Uso: python3 variantes/bltouch.py [raíz del proyecto]   (por defecto, la carpeta de arriba)
"""
import os
import sys

R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MARCA = '  // Magna2-230 BLTouch'

CAMBIOS = {
    'Marlin/Configuration.h': [
        ('#define Z_MIN_ENDSTOP_HIT_STATE LOW  // Magna2-230: verificado en el bin original',
         '#define Z_MIN_ENDSTOP_HIT_STATE HIGH' + MARCA + ': la señal del BLTouch va en Z- y se activa en alto'),
        ('//#define BLTOUCH\n', '#define BLTOUCH' + MARCA + ': servo en PA8 (conector BLTouch), señal en Z-\n'),
        ('#define NOZZLE_TO_PROBE_OFFSET { 10, 10, 0 }',
         '#define NOZZLE_TO_PROBE_OFFSET { 0, 0, 0 }' + MARCA + ': medir y cargar en la pantalla o con M851 X.. Y.. Z.. + M500'),
        ('#define PROBING_MARGIN 10', '#define PROBING_MARGIN 45' + MARCA + ': seguro para soportes de hasta 45 mm'),
        ('//#define MULTIPLE_PROBING 2', '#define MULTIPLE_PROBING 2' + MARCA),
        ('//#define AUTO_BED_LEVELING_BILINEAR', '#define AUTO_BED_LEVELING_BILINEAR' + MARCA),
        ('//#define ENABLE_LEVELING_AFTER_G28', '#define ENABLE_LEVELING_AFTER_G28' + MARCA + ': activa la malla guardada después de cada G28'),
        ('#if ANY(AUTO_BED_LEVELING_LINEAR, AUTO_BED_LEVELING_BILINEAR)\n\n  // Set the number of grid points per dimension.\n  #define GRID_MAX_POINTS_X 3',
         '#if ANY(AUTO_BED_LEVELING_LINEAR, AUTO_BED_LEVELING_BILINEAR)\n\n  // Set the number of grid points per dimension.\n  #define GRID_MAX_POINTS_X 5' + MARCA),
        ('//#define Z_SAFE_HOMING\n', '#define Z_SAFE_HOMING' + MARCA + ': home de Z con la sonda en el centro de la cama\n'),
    ],
    'Marlin/Configuration_adv.h': [
        ('  //#define PROBE_OFFSET_WIZARD\n', '  #define PROBE_OFFSET_WIZARD' + MARCA + ': asistente de offset Z (Config > Nivelación)\n'),
        ('    //#define PROBE_OFFSET_WIZARD_START_Z -4.0', '    #define PROBE_OFFSET_WIZARD_START_Z -1.0' + MARCA),
        ('  //#define BABYSTEP_ZPROBE_OFFSET          // Combine M851 Z and Babystepping',
         '  #define BABYSTEP_ZPROBE_OFFSET' + MARCA + ': el babystep corrige el offset de la sonda'),
    ],
}

# Arreglo de Marlin 2.1.3-b3: menu_probe_offset.cpp (asistente de la interfaz MarlinUI) se compila
# también con la interfaz MKS y falla ("screenFunc_t does not name a type"). La pantalla MKS trae su
# propio asistente (draw_z_offset_wizard.cpp), así que ese archivo solo se compila con MarlinUI.
# Solo existe en el árbol completo de Marlin (en el zip de este repo no está).
MENU_WIZARD = 'Marlin/src/lcd/menu/menu_probe_offset.cpp'
if os.path.exists(os.path.join(R, MENU_WIZARD)):
    CAMBIOS[MENU_WIZARD] = [('#if ENABLED(PROBE_OFFSET_WIZARD)\n',
                             '#if ENABLED(PROBE_OFFSET_WIZARD) && HAS_MARLINUI_MENU  // Magna2-230 BLTouch: con la pantalla MKS se usa draw_z_offset_wizard.cpp\n')]

errores = 0
for archivo, cambios in CAMBIOS.items():
    p = os.path.join(R, archivo)
    s = open(p, encoding='utf-8').read()
    for viejo, nuevo in cambios:
        if nuevo in s:
            continue
        if s.count(viejo) != 1:
            print(f'NO ENCONTRADO en {archivo}: {viejo.splitlines()[-1][:70]}')
            errores += 1
            continue
        s = s.replace(viejo, nuevo)
    open(p, 'w', encoding='utf-8').write(s)
if errores:
    sys.exit(f'Variante BLTouch: {errores} cambios no se pudieron aplicar')
print('Variante BLTouch aplicada')
