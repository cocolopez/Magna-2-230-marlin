#!/usr/bin/env python3
"""
Placa MKS Robin Nano V1.2 (STM32F103VE: 72 MHz, 64 KB de RAM) — firmware "mm12".

Se corre DESPUÉS de la variante de modelo (modelo.py) y ANTES de aplicar_colores.py. Cambia la placa y
saca lo que no entra o carga demasiado al procesador. Los extras de la pantalla los recorta
assets-tema/liviano.py (lo llama aplicar_colores.py cuando ve MAGNA_LIVIANO).

Medido (compilación local, 230 sin tema ni input shaping): ~62 KB de RAM de 64. Con todos los extras
de la pantalla eran ~76 KB: no entraba.

Qué cambia:
  * MOTHERBOARD BOARD_MKS_ROBIN_NANO (entorno mks_robin_nano_v1v2 de PlatformIO);
  * sin INPUT_SHAPING (unos 3,4 KB de RAM y mucho procesador en un F103);
  * sin ADAPTIVE_STEP_SMOOTHING (procesador);
  * BLOCK_BUFFER_SIZE 8 en vez de 16 (~1,1 KB);
  * MAGNA_LIVIANO y MAGNA_PLACA_12 (la pantalla manda "MAGNA_PLACA:1.2" por WiFi: MagnAir pregunta
    menos seguido y esconde lo que esta placa no tiene).

SIN PROBAR: el autor no tiene una placa V1.2.

Uso: python3 variantes/placa12.py [raíz del proyecto]
"""
import os
import sys

R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MARCA = '  // Magna2 placa V1.2 (mm12)'

CAMBIOS = {
    'Marlin/Configuration.h': [
        ('  #define MOTHERBOARD BOARD_MKS_ROBIN_NANO_V1_3_F4  // Magna2-230: MKS Robin Nano V1.3 (STM32F407)',
         '  #define MOTHERBOARD BOARD_MKS_ROBIN_NANO' + MARCA + ': MKS Robin Nano V1.2 (STM32F103VE)\n'
         '  #define MAGNA_LIVIANO' + MARCA + ': extras de la pantalla recortados (assets-tema/liviano.py)\n'
         '  #define MAGNA_PLACA_12' + MARCA + ': la pantalla avisa la placa por WiFi (MagnAir)'),
    ],
    'Marlin/Configuration_adv.h': [
        ('#define INPUT_SHAPING_X  // Magna2-230: calibrar con M593 X F..',
         '//#define INPUT_SHAPING_X' + MARCA + ': no entra en la RAM del F103'),
        ('#define INPUT_SHAPING_Y  // Magna2-230: calibrar con M593 Y F..',
         '//#define INPUT_SHAPING_Y' + MARCA + ': no entra en la RAM del F103'),
        ('#define ADAPTIVE_STEP_SMOOTHING  // Magna2-230',
         '//#define ADAPTIVE_STEP_SMOOTHING' + MARCA + ': procesador'),
        ('''#elif HAS_MEDIA
  #define BLOCK_BUFFER_SIZE 16''', '''#elif HAS_MEDIA
  #define BLOCK_BUFFER_SIZE  8''' + MARCA + ': RAM'),
    ],
}

errores = 0
for archivo, cambios in CAMBIOS.items():
    p = os.path.join(R, archivo)
    s = open(p, encoding='utf-8').read()
    for viejo, nuevo in cambios:
        if nuevo in s:
            continue
        if s.count(viejo) != 1:
            print(f'NO ENCONTRADO en {archivo}: {viejo.splitlines()[0][:80]}')
            errores += 1
            continue
        s = s.replace(viejo, nuevo)
    open(p, 'w', encoding='utf-8').write(s)

# PlatformIO: el entorno de la V1.2
pi = os.path.join(R, 'platformio.ini')
s = open(pi, encoding='utf-8').read()
if 'default_envs = mks_robin_nano_v1_3_f4' in s:
    s = s.replace('default_envs = mks_robin_nano_v1_3_f4', 'default_envs = mks_robin_nano_v1v2')
    open(pi, 'w', encoding='utf-8').write(s)
elif 'default_envs = mks_robin_nano_v1v2' not in s:
    print('platformio.ini: no encontré default_envs')
    errores += 1

if errores:
    sys.exit(f'Placa V1.2: {errores} cambios no se pudieron aplicar')
print('Placa V1.2 aplicada (mm12)')
