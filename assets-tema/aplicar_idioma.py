#!/usr/bin/env python3
"""
Etapa 39: pantalla en castellano completa, arreglo de la carpeta _assets y aviso "sin probar".

Lo llama aplicar_colores.py al final (también se puede correr solo). Trabaja sobre el árbol
completo de Marlin: python3 aplicar_idioma.py <raíz del proyecto>

1. tft_Language_sp.h: se reescribe con todos los textos de traduccion_es.py (el de Makerbase
   traía unos 210 de ~380; lo que faltaba salía en inglés aunque eligieras Español).
2. tft_multi_language.cpp: en Español se usan todos esos textos:
   - el bloque de Español de disp_language_init() pasa a ser una copia del de inglés con _SP;
   - machine_setting_disp() (Ajustes de la máquina) suma un bloque de Español;
   - las asignaciones comunes que estaban fijas en inglés (_EN) eligen según el idioma.
3. Textos fijos en inglés escritos en el código: la pantalla de "Assets Updating", la de error
   grave ("PRINTER HALTED") y los mensajes de subida por WiFi. Esas pantallas usan la letra fija
   de 16 px, que es solo ASCII: van sin tildes (y el motivo del error se escribe sin tildes).
4. Carpeta assets: al terminar de cargarla, la pantalla la renombra a _assets; si ya había una
   _assets de una instalación anterior, el renombre fallaba y la cargaba en cada arranque. Ahora
   borra la vieja antes.
5. Firmware de un modelo sin probar (MAGNA_SIN_PROBAR, lo define variantes/modelo.py): Acerca de
   muestra el modelo con "SIN PROBAR".
6. M115 por WiFi manda también "MACHINE_TYPE:Magna 2 XXX" y "MAGNA_PLACA:1.3" o "1.2" (MagnAir sabe el
   modelo y la placa).

Si un cambio no se encuentra, FALLA (no se compila algo a medias).
"""
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import traduccion_es  # noqa: E402

RAIZ = sys.argv[1] if len(sys.argv) > 1 else '.'
UI = os.path.join(RAIZ, 'Marlin/src/lcd/extui/mks_ui')
MARCA = '// Magna2 (etapa 39)'
errores = 0


def leer(nombre):
    return open(os.path.join(UI, nombre), encoding='utf-8').read()


def escribir(nombre, s):
    open(os.path.join(UI, nombre), 'w', encoding='utf-8').write(s)


def c_texto(t):
    """Texto de Python -> literal de C (UTF-8 con escapes, para no depender del editor)."""
    out = []
    for ch in t:
        if ch == '\n':
            out.append('\\n')
        elif ch == '"':
            out.append('\\"')
        elif ch == '\\':
            out.append('\\\\')
        elif ord(ch) < 128:
            out.append(ch)
        else:
            out.append(''.join(f'\\x{b:02X}' for b in ch.encode('utf-8')))
    s = ''.join(out)
    # un escape \xNN seguido de una letra hex se lee como uno solo: se corta el literal
    s = re.sub(r'(\\x[0-9A-F]{2})(?=[0-9A-Fa-f])', r'\1""', s)
    return '"' + s + '"'


def cambiar(nombre, viejo, nuevo, para):
    global errores
    s = leer(nombre)
    if nuevo in s:
        print('ya aplicado:', para)
        return
    if s.count(viejo) != 1:
        print(f'NO ENCONTRADO ({nombre}): {para}')
        errores += 1
        return
    escribir(nombre, s.replace(viejo, nuevo))
    print('ok:', para)


# ------------------------------------------------------------------ 1. tft_Language_sp.h
en = leer('tft_Language_en.h')
sp_orig = leer('tft_Language_sp.h')
multi_h = leer('tft_multi_language.h')
if MARCA not in sp_orig:
    claves_en = re.findall(r'#define\s+(\w+)_EN\s+(.+)', en + '\n' + multi_h)
    viejas = dict(re.findall(r'#define\s+(\w+)_SP\s+(.+)', sp_orig))
    lineas = ['/**', ' * ' + MARCA + ': textos en castellano de la pantalla, generado por',
              ' * assets-tema/aplicar_idioma.py desde assets-tema/traduccion_es.py. No editar a mano.',
              ' */', '#pragma once', '']
    # las que tft_multi_language.h ya define en castellano (nombres de idiomas) no se repiten
    vistos = set(re.findall(r'#define\s+(\w+)_SP\b', multi_h))
    for clave, valor in claves_en:
        if clave in vistos:
            continue
        vistos.add(clave)
        if clave in traduccion_es.TEXTOS:
            v = c_texto(traduccion_es.TEXTOS[clave])
        elif clave in viejas:
            v = viejas[clave].strip()
        else:
            v = valor.strip()  # sin traducción: igual que en inglés
        lineas.append(f'#define {clave}_SP {v}')
    # las que solo estaban en el archivo de Makerbase (por si algún archivo las usa)
    for clave, valor in viejas.items():
        if clave not in vistos:
            lineas.append(f'#define {clave}_SP {valor.strip()}')
    escribir('tft_Language_sp.h', '\n'.join(lineas) + '\n')
    print(f'ok: tft_Language_sp.h con {len(lineas) - 6} textos')
else:
    print('ya aplicado: tft_Language_sp.h')

# Los textos de subida por WiFi están en tft_multi_language.h y no tienen versión _SP
if 'DIALOG_UPLOAD_ING_SP' not in multi_h:
    extra = '\n' + MARCA + ': textos de subida por WiFi en castellano\n'
    for clave in ('DIALOG_UPLOAD_ING', 'DIALOG_UPLOAD_ERROR', 'DIALOG_UPLOAD_FINISH', 'DIALOG_UPLOAD_SIZE',
                  'DIALOG_UPLOAD_TIME', 'DIALOG_UPLOAD_SPEED', 'DIALOG_UPDATE_WIFI_FIRMWARE', 'DIALOG_UPDATE_NO_DEVICE'):
        extra += f'#define {clave}_SP {c_texto(traduccion_es.TEXTOS[clave])}\n'
    extra += ('#define MAGNA_ES(k) (gCfgItems.language == LANG_SPANISH ? k##_SP : k##_EN)  '
              '// texto según el idioma (castellano o inglés)\n')
    ancla = '#define DIALOG_UPDATE_NO_DEVICE_EN'
    i = multi_h.index(ancla)
    fin = multi_h.index('\n', i) + 1
    escribir('tft_multi_language.h', multi_h[:fin] + extra + multi_h[fin:])
    print('ok: textos de subida por WiFi y MAGNA_ES')
else:
    print('ya aplicado: textos de subida por WiFi y MAGNA_ES')

# ------------------------------------------------------------------ 2. tft_multi_language.cpp
ml = leer('tft_multi_language.cpp')
if MARCA not in ml:
    # a) disp_language_init: el bloque de Español = el de inglés con _SP
    ini_en = ml.index('          case LANG_ENGLISH:\n')
    fin_en = ml.index('            break;\n', ini_en) + len('            break;\n')
    bloque_en = ml[ini_en:fin_en]
    ini_sp = ml.index('          case LANG_SPANISH:\n')
    fin_sp = ml.index('            break;\n', ini_sp) + len('            break;\n')
    bloque_sp = re.sub(r'\b(\w+)_EN\b', r'\1_SP', bloque_en).replace('case LANG_ENGLISH:', 'case LANG_SPANISH:  ' + MARCA + ': todo en castellano')
    for viejo, nuevo in traduccion_es.TITULOS_ESPECIALES.items():
        bloque_sp = bloque_sp.replace(f'= {viejo};', f'= {c_texto(nuevo)};')
    ml = ml[:ini_sp] + bloque_sp + ml[fin_sp:]

    # b) machine_setting_disp: bloque de Español antes del "else" (inglés)
    ini_m = ml.index('void machine_setting_disp() {')
    ini_else = ml.index('  else {\n', ml.index('gCfgItems.language == LANG_COMPLEX_CHINESE', ini_m))
    fin_else = ml.index('\n  }\n', ini_else) + len('\n  }\n')
    cuerpo = ml[ini_else + len('  else {\n'):fin_else - len('  }\n')]
    nuevo_m = ('  else if (gCfgItems.language == LANG_SPANISH) {  ' + MARCA + ': Ajustes de la máquina en castellano\n'
               + re.sub(r'\b(\w+)_EN\b', r'\1_SP', cuerpo) + '  }\n')
    ml = ml[:ini_else] + nuevo_m + ml[ini_else:]

    # c) asignaciones comunes fijas en inglés (antes del switch): según el idioma
    ini_c = ml.index('  media_select_menu.title    = MEDIA_SELECT_TITLE_EN;')
    fin_c = ml.index('  switch (gCfgItems.language) {', ini_c)
    comun = re.sub(r'= (\w+)_EN;', r'= MAGNA_ES(\1);', ml[ini_c:fin_c])
    ml = ml[:ini_c] + '  ' + MARCA + ': estas eran fijas en inglés\n' + comun + ml[fin_c:]
    escribir('tft_multi_language.cpp', ml)
    print('ok: tft_multi_language.cpp usa todos los textos en castellano')
else:
    print('ya aplicado: tft_multi_language.cpp')

# ------------------------------------------------------------------ 3. textos fijos en inglés
cambiar('mks_hardware.cpp', 'disp_string(100, 140, F("Assets Updating..."), 0xFFFF, 0x0000);',
        'disp_string(100, 140, F("Actualizando imagenes..."), 0xFFFF, 0x0000);  ' + MARCA + ' (letra solo ASCII)',
        'pantalla de carga de imágenes en castellano')
for viejo, nuevo in (('Erasing pics...', 'Borrando imagenes...'), ('Erasing fonts...', 'Borrando letras...'),
                     ('Reading files...', 'Leyendo archivos...')):
    cambiar('pic_manager.cpp', f'disp_assets_update_progress(F("{viejo}"));',
            f'disp_assets_update_progress(F("{nuevo}"));  ' + MARCA, f'carga de imágenes: "{nuevo}"')

ERROR_VIEJO = '''  FSTR_P const fhalted = F("PRINTER HALTED"), fplease = F("Please Reset");
  SPI_TFT.lcdClear(0x0000);
  if (fmsg) disp_string((TFT_WIDTH - strlen_P(FTOP(fmsg)) * 16) / 2, 100, fmsg, 0xFFFF, 0x0000);'''
ERROR_NUEVO = '''  ''' + MARCA + ''': en castellano. La letra de esta pantalla es solo ASCII: el motivo (que con
  // la pantalla en castellano viene con tildes) se escribe sin tildes.
  FSTR_P const fhalted = F("IMPRESORA DETENIDA"), fplease = F("Apagala y prendela");
  SPI_TFT.lcdClear(0x0000);
  if (fmsg) {
    static char motivo[30];  // 29 letras de 16 px entran en los 480 de ancho
    const char *s = FTOP(fmsg);
    uint8_t n = 0;
    while (*s && n < sizeof(motivo) - 1) {
      uint8_t c = (uint8_t)*s++;
      if (c == 0xC3 && *s) {  // á é í ó ú ñ ü (y mayúsculas) en UTF-8 -> letra sin tilde
        uint8_t d = (uint8_t)*s++ | 0x20;
        c = (d >= 0xA0 && d <= 0xA5) ? 'a' : (d >= 0xA8 && d <= 0xAB) ? 'e' : (d >= 0xAC && d <= 0xAF) ? 'i'
          : (d >= 0xB2 && d <= 0xB6) ? 'o' : (d >= 0xB9 && d <= 0xBC) ? 'u' : (d == 0xB1) ? 'n' : '?';
      }
      else if (c >= 0x80) continue;  // otros caracteres que la letra no tiene
      motivo[n++] = (c >= 'a' && c <= 'z') ? c - 32 : c;  // en mayúsculas, como el resto de la pantalla
    }
    motivo[n] = 0;
    disp_string((TFT_WIDTH - n * 16) / 2, 100, motivo, 0xFFFF, 0x0000);
  }'''
cambiar('draw_error_message.cpp', ERROR_VIEJO, ERROR_NUEVO, 'pantalla de error grave en castellano')

DIALOGO = leer('draw_dialog.cpp')
for clave in ('DIALOG_UPDATE_NO_DEVICE', 'DIALOG_UPLOAD_ING', 'DIALOG_UPLOAD_ERROR', 'DIALOG_UPDATE_WIFI_FIRMWARE'):
    cambiar('draw_dialog.cpp', f'lv_label_set_text(labelDialog, {clave}_EN);',
            f'lv_label_set_text(labelDialog, MAGNA_ES({clave}));  ' + MARCA, f'mensaje {clave} según el idioma')
SUBIDA_VIEJO = '''        MString<200> buf(
          F(DIALOG_UPLOAD_FINISH_EN), '\\n',
          F(DIALOG_UPLOAD_SIZE_EN), F(": "), int(upload_size / 1024), F(" KBytes\\n"),
          F(DIALOG_UPLOAD_TIME_EN), F(": "), int(upload_time_sec), F(" s\\n"),
          F(DIALOG_UPLOAD_SPEED_EN), F(": "), int(upload_size / upload_time_sec / 1024), F(" KBytes/s\\n")
        );'''
SUBIDA_NUEVO = '''        const bool es = gCfgItems.language == LANG_SPANISH;  ''' + MARCA + '''
        MString<200> buf(
          es ? F(DIALOG_UPLOAD_FINISH_SP) : F(DIALOG_UPLOAD_FINISH_EN), '\\n',
          es ? F(DIALOG_UPLOAD_SIZE_SP) : F(DIALOG_UPLOAD_SIZE_EN), F(": "), int(upload_size / 1024), F(" KBytes\\n"),
          es ? F(DIALOG_UPLOAD_TIME_SP) : F(DIALOG_UPLOAD_TIME_EN), F(": "), int(upload_time_sec), F(" s\\n"),
          es ? F(DIALOG_UPLOAD_SPEED_SP) : F(DIALOG_UPLOAD_SPEED_EN), F(": "), int(upload_size / upload_time_sec / 1024), F(" KBytes/s\\n")
        );'''
cambiar('draw_dialog.cpp', SUBIDA_VIEJO, SUBIDA_NUEVO, 'resumen de subida por WiFi según el idioma')

# ------------------------------------------------------------------ 4. carpeta _assets
cambiar('pic_manager.cpp', '      dir.rename(&root, bakPath);\n',
        '      {  ' + MARCA + ': si quedó una _assets de antes, el renombre fallaba y la carpeta\n'
        '         // assets se volvía a cargar en cada arranque. Se borra la vieja primero.\n'
        '        MediaFile vieja;\n'
        '        if (vieja.open(&root, bakPath, O_RDONLY)) { vieja.rmRfStar(); vieja.close(); }\n'
        '      }\n'
        '      dir.rename(&root, bakPath);\n',
        'carga de imágenes: borrar la _assets vieja antes de renombrar')

# ------------------------------------------------------------------ 5. modelo sin probar
cambiar('draw_about.cpp', '  website = lv_label_create(scr, WEBSITE_URL);\n',
        '  #ifdef MAGNA_SIN_PROBAR  ' + MARCA + ': firmware de un modelo que nadie probó todavía\n'
        '    website = lv_label_create(scr, CUSTOM_MACHINE_NAME " - SIN PROBAR");\n'
        '  #else\n'
        '    website = lv_label_create(scr, WEBSITE_URL);\n'
        '  #endif\n',
        'Acerca de: aviso de modelo sin probar')

# El modelo por WiFi: a la respuesta de M115 se le agrega una línea con CUSTOM_MACHINE_NAME
# ("Magna 2 400D"). MagnAir la usa para saber el tamaño de la cama (visor 3D y nivelación).
cambiar('wifi_module.cpp', '        #define SENDFW "FIRMWARE_NAME:Robin_nano\\r\\n"\n',
        '        #ifdef MAGNA_PLACA_12  ' + MARCA + ': la placa (MagnAir pregunta menos seguido y esconde lo que no hay)\n'
        '          #define MAGNA_PLACA_TXT "MAGNA_PLACA:1.2\\r\\n"\n'
        '        #else\n'
        '          #define MAGNA_PLACA_TXT "MAGNA_PLACA:1.3\\r\\n"\n'
        '        #endif\n'
        '        #define SENDFW "FIRMWARE_NAME:Robin_nano\\r\\nMACHINE_TYPE:" CUSTOM_MACHINE_NAME "\\r\\n" MAGNA_PLACA_TXT  ' + MARCA + ': el modelo para MagnAir\n',
        'M115 por WiFi: el modelo (MACHINE_TYPE)')

if errores:
    sys.exit(f'Idioma: {errores} cambios no se pudieron aplicar')
print('Idioma: listo')
