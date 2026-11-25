#!/usr/bin/env python3
"""
Aplica el tema negro/rojo a la interfaz MKS (TFT_LVGL_UI) de Marlin:
  * colores fijos del código de la pantalla (azul/amarillo/marrón de Makerbase -> rojo/gris),
  * fondo con degradé (gris oscuro arriba -> rojo oscuro abajo) en todas las pantallas,
  * decoración de la pantalla principal: "MAGNA 2", raya roja y líneas de capas,
  * decoración marcada de los menús de íconos (decoracion_menus.inc).
Todo con reemplazos exactos; si alguno no se encuentra (otra versión de Marlin) avisa y lo saltea.
Es idempotente: se puede correr varias veces.
Uso: python3 aplicar_colores.py <raíz del proyecto Marlin completo>
"""
import os, sys
R = os.path.join(sys.argv[1] if len(sys.argv) > 1 else '.', 'Marlin/src/lcd/extui/mks_ui')
# Código que se agrega a la pantalla principal (draw_ready_print.cpp), detrás de los botones.
DECORACION = '''
  // Magna2-230 (tema): encabezado y líneas de capas sobre el fondo degradé
  {
    static lv_style_t st_titulo, st_dos, st_raya, st_capa[5];
    static lv_point_t pts_raya[2] = { { 0, 0 }, { 440, 0 } };
    static lv_point_t pts_capa[2] = { { 0, 0 }, { 480, 0 } };
    lv_style_copy(&st_titulo, &tft_style_label_rel);
    st_titulo.text.color = LV_COLOR_MAKE(0xEE, 0xEE, 0xEE);
    st_titulo.text.letter_space = 3;
    lv_style_copy(&st_dos, &st_titulo);
    st_dos.text.color = LV_COLOR_MAKE(0xD6, 0x20, 0x27);
    lv_obj_t *titulo = lv_label_create(scr, 24, 24, "MAGNA");
    lv_obj_set_style(titulo, &st_titulo);
    lv_obj_t *dos = lv_label_create(scr, 0, 24, "2");
    lv_obj_set_style(dos, &st_dos);
    lv_obj_align(dos, titulo, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_style_copy(&st_raya, &lv_style_plain);
    st_raya.line.color = LV_COLOR_MAKE(0xD6, 0x20, 0x27);
    st_raya.line.width = 2;
    lv_obj_t *raya = lv_line_create(scr, nullptr);
    lv_line_set_points(raya, pts_raya, 2);
    lv_line_set_style(raya, LV_LINE_STYLE_MAIN, &st_raya);
    lv_obj_set_pos(raya, 20, 72);
    for (uint8_t i = 0; i < 5; i++) {
      lv_style_copy(&st_capa[i], &lv_style_plain);
      const uint8_t r = 0x80 + i * 0x14, g = 0x12 + i * 3, b = 0x18 + i * 3;  // de rojo medio a rojo (se ven sobre el degradé)
      st_capa[i].line.color = LV_COLOR_MAKE(r, g, b);
      st_capa[i].line.width = 2;
      lv_obj_t *capa = lv_line_create(scr, nullptr);
      lv_line_set_points(capa, pts_capa, 2);
      lv_line_set_style(capa, LV_LINE_STYLE_MAIN, &st_capa[i]);
      lv_obj_set_pos(capa, 0, 236 + i * 4);
    }
  }
'''

# Decoración "marcada" de los menús de íconos (variante B): el código está en decoracion_menus.inc
# (el mismo archivo que compila la prueba de render) y se pega en draw_ui.cpp.
AQUI = os.path.dirname(os.path.abspath(__file__))
INC = open(os.path.join(AQUI, 'decoracion_menus.inc'), encoding='utf-8').read()
MENUS = """
// Magna2-230 (tema): pantallas de íconos que llevan la decoración (no listas de parámetros ni diálogos)
static bool magna_menu_de_iconos(const DISP_STATE s) {
  switch (s) {
    case TOOL_UI: case SET_UI: case PREHEAT_UI: case PRINT_FILE_UI: case FAN_UI: case ZERO_UI:
    case LANGUAGE_UI: case LEVELING_UI: case MOVE_MOTOR_UI: case EXTRUSION_UI: case OPERATE_UI:
    case BABYSTEP_UI: case MORE_UI: case FILAMENTCHANGE_UI: case CHANGE_SPEED_UI:
      return true;
    default:
      return false;
  }
}

"""
DIALOGOS = open(os.path.join(AQUI, 'estilo_dialogos.inc'), encoding='utf-8').read()
FUENTE = open(os.path.join(AQUI, 'fuente_grande.inc'), encoding='utf-8').read()
CREDITOS = open(os.path.join(AQUI, 'creditos.inc'), encoding='utf-8').read()
ACERCA_INICIO = 'void lv_draw_about() {\n'
ACERCA_FIN = '  lv_obj_align(protocol, nullptr, LV_ALIGN_CENTER, 0, 40);\n'
IDIOMA = """
// Magna2-230 (tema): la letra grande tiene ASCII + Latin-1; en chino, japonés, coreano, ruso,
// griego o turco se deja la letra original de la pantalla.
bool magna_idioma_latino() {
  switch (gCfgItems.language) {
    case LANG_ENGLISH: case LANG_GERMAN: case LANG_FRENCH: case LANG_SPANISH:
    case LANG_ITALY: case LANG_PORTUGUESE:
      return true;
    default:
      return false;
  }
}

"""
DECLARACIONES = """// Magna2-230: apagado automático de la pantalla y M256 por WiFi (tft_lvgl_configuration.cpp)
void magna_pantalla_despertar();
void magna_pantalla_apagar();
bool magna_pantalla_encendida();
// Magna2-230 (tema): letra grande y barras (estilo_dialogos.inc, fuente_grande.inc)
extern lv_font_t magna_fuente_grande;
bool magna_idioma_latino();
void magna_texto_grande(lv_obj_t *etiqueta);
void magna_estilo_barra(lv_obj_t *barra, const lv_font_t *letra);

"""
ARCHIVO_FUENTE = ('/**\n * Magna2-230 (tema): letra grande (Roboto 26 px, ASCII + Latin-1).\n'
                  ' * Archivo agregado por assets-tema/aplicar_colores.py a partir de fuente_grande.inc.\n */\n'
                  '#include "../../../inc/MarlinConfigPre.h"\n\n#if HAS_TFT_LVGL_UI\n\n#include <lvgl.h>\n\n'
                  + FUENTE + '\n#endif // HAS_TFT_LVGL_UI\n')
DIALOGO_FIN = """  // Magna2-230 (tema): mensajes con letra grande y barra del tema
  if (magna_idioma_latino()) {
    magna_texto_grande(labelDialog);
    if (DIALOG_IS(TYPE_FILAMENT_LOAD_HEAT, TYPE_FILAMENT_UNLOAD_HEAT)) {
      magna_texto_grande(tempText1);
      filament_sprayer_temp();
    }
    const lv_coord_t limite = BTN_OK_Y - 8;  // que el texto no pise los botones
    if (lv_obj_get_y(labelDialog) + lv_obj_get_height(labelDialog) > limite)
      lv_obj_set_y(labelDialog, LV_MATH_MAX(40, limite - lv_obj_get_height(labelDialog)));
  }
  if (DIALOG_IS(TYPE_FILAMENT_LOADING, TYPE_FILAMENT_UNLOADING)) {
    lv_obj_set_pos(filament_bar, 40, 160);
    lv_obj_set_size(filament_bar, 400, 34);
    magna_estilo_barra(filament_bar, nullptr);
  }
"""
ROTARY_DIALOGO = '  #if HAS_ROTARY_ENCODER\n    if (gCfgItems.encoder_enable) {\n      if (btnOk) lv_group_add_obj(g, btnOk);'
BARRA_IMPRESION = '  lv_label_set_text(bar1ValueText, "0%");\n  lv_obj_align(bar1ValueText, bar1, LV_ALIGN_CENTER, 0, 0);\n'
ALINEAR_PORCENTAJE = '  lv_obj_align(bar1ValueText, bar1, LV_ALIGN_CENTER, 0, 0);\n'

CREAR = 'lv_obj_t* lv_screen_create(DISP_STATE newScreenType, const char *title) {\n'
# Apagado automático de la pantalla: se apaga la luz de fondo (PD13) después de
# MAGNA_PANTALLA_APAGADO_MIN minutos sin tocarla (Configuration_adv.h; 0 = nunca). El primer toque
# solo la prende (no aprieta el botón que esté debajo). Cualquier pantalla nueva (por ejemplo un
# aviso de falta de filamento o de impresión terminada) también la prende.
TOUCH_VIEJO = """bool my_touchpad_read(lv_indev_drv_t * indev_driver, lv_indev_data_t * data) {
  static xy_int_t last { 0, 0 };
  data->state = get_point(&last.x, &last.y) ? LV_INDEV_STATE_PR : LV_INDEV_STATE_REL;"""
TOUCH_NUEVO = """// Magna2-230: apagado automático de la pantalla (MAGNA_PANTALLA_APAGADO_MIN en Configuration_adv.h)
#ifndef MAGNA_PANTALLA_APAGADO_MIN
  #define MAGNA_PANTALLA_APAGADO_MIN 0
#endif
static millis_t magna_ultimo_uso = 0;
static bool magna_apagada = false;
void magna_pantalla_despertar() {
  magna_ultimo_uso = millis();
  if (magna_apagada) {
    #if PIN_EXISTS(TFT_BACKLIGHT)
      WRITE(TFT_BACKLIGHT_PIN, HIGH);
    #endif
    magna_apagada = false;
  }
}
// Magna2-230: prender/apagar la luz a pedido (M256 por WiFi, desde MagnAir). Apagada a mano, el primer
// toque la prende sin apretar nada, igual que con el apagado automático.
void magna_pantalla_apagar() {
  #if PIN_EXISTS(TFT_BACKLIGHT)
    WRITE(TFT_BACKLIGHT_PIN, LOW);
    magna_apagada = true;
  #endif
}
bool magna_pantalla_encendida() { return !magna_apagada; }
static void magna_pantalla_revisar() {
  #if PIN_EXISTS(TFT_BACKLIGHT)
    if (MAGNA_PANTALLA_APAGADO_MIN > 0 && !magna_apagada
        && ELAPSED(millis(), magna_ultimo_uso + MIN_TO_MS(MAGNA_PANTALLA_APAGADO_MIN))) {
      WRITE(TFT_BACKLIGHT_PIN, LOW);
      magna_apagada = true;
    }
  #endif
}

bool my_touchpad_read(lv_indev_drv_t * indev_driver, lv_indev_data_t * data) {
  static xy_int_t last { 0, 0 };
  static bool tragar = false;  // Magna2-230: el toque que prende la pantalla no aprieta nada
  bool tocando = get_point(&last.x, &last.y);
  if (tocando) {
    if (magna_apagada) tragar = true;
    magna_pantalla_despertar();
  }
  else
    tragar = false;
  if (tragar) tocando = false;
  magna_pantalla_revisar();
  data->state = tocando ? LV_INDEV_STATE_PR : LV_INDEV_STATE_REL;"""
# M256 por WiFi (MagnAir): "M256" responde el estado, "M256 B0" apaga la pantalla y "M256 B255" la prende.
# Lo atiende el módulo de WiFi de la UI MKS (no pasa por la cola de G-code). Marlin no tiene M256 con esta
# pantalla (HAS_LCD_BRIGHTNESS), así que el número está libre; se usa la misma letra B de brillo.
WIFI_M115 = """      case 115:
        ZERO(tempBuf);"""
WIFI_M256 = """      case 257: magna_m257(); send_ok_to_wifi(); break;  // Magna2-230 (MagnAir): datos de calibración

      case 256: {  // Magna2-230 (MagnAir): luz de la pantalla. "M256" = estado, "B0" apaga, "B1".."B255" prende
        const char * const bStr = strchr(mStr, 'B');
        if (bStr) {
          if (atoi(bStr + 1) > 0) magna_pantalla_despertar(); else magna_pantalla_apagar();
        }
        print_to_wifi(magna_pantalla_encendida() ? "M256 B255\\r\\n" : "M256 B0\\r\\n");
        send_ok_to_wifi();
      } break;

"""
# M257 por WiFi (MagnAir): manda los valores de calibración guardados, uno por grupo, con el formato
# "M257 <grupo> CLAVE=valor ..." y al final "M257 fin". Hace falta porque la UI MKS no reenvía al WiFi
# lo que contestan los comandos normales (M503, M306, M301...): solo sus respuestas propias.
WIFI_INCLUDES_VIEJO = '#include "../../../gcode/gcode.h"\n'
WIFI_INCLUDES_NUEVO = WIFI_INCLUDES_VIEJO + """#include "../../../module/planner.h"  // Magna2-230 (MagnAir): M257
#include "../../../module/stepper.h"
#include "../../../module/motion.h"
#if HAS_BED_PROBE
  #include "../../../module/probe.h"
#endif
#if ENABLED(PRINTCOUNTER)
  #include "../../../module/printcounter.h"  // Magna2-230 (MagnAir): estadísticas en M257
#endif
#if ENABLED(POWER_LOSS_RECOVERY)
  #include "../../../feature/powerloss.h"
#endif
#if HAS_FILAMENT_SENSOR
  #include "../../../feature/runout.h"
#endif
"""
WIFI_EXEC = 'static void wifi_gcode_exec(uint8_t * const cmd_line) {\n'
WIFI_M257_FUNC = """// Magna2-230 (MagnAir): M257 = valores de calibración guardados, por WiFi.
static void magna_m257_linea(const char *grupo, const char * const claves[], const float valores[], const uint8_t decimales[], const uint8_t n) {
  char linea[160], num[20];
  snprintf(linea, sizeof(linea), "M257 %s", grupo);
  for (uint8_t i = 0; i < n; i++) {
    dtostrf(valores[i], 1, decimales[i], num);
    const size_t l = strlen(linea);
    snprintf(linea + l, sizeof(linea) - l, " %s=%s", claves[i], num);
  }
  const size_t l = strlen(linea);
  snprintf(linea + l, sizeof(linea) - l, "\\r\\n");
  print_to_wifi(linea);
}

static void magna_m257() {
  #if ENABLED(MPCTEMP)
  {
    const MPC_t &m = thermalManager.temp_hotend[0].mpc;
    const char * const k[] = { "P", "C", "R", "A", "F", "H" };
    const float v[] = { m.heater_power, m.block_heat_capacity, m.sensor_responsiveness, m.ambient_xfer_coeff_fan0,
                        TERN0(MPC_INCLUDE_FAN, m.fan255_adjustment), m.filament_heat_capacity_permm };
    const uint8_t d[] = { 2, 4, 4, 4, 4, 5 };
    magna_m257_linea("mpc", k, v, d, 6);
  }
  #elif ENABLED(PIDTEMP)
  {
    const char * const k[] = { "P", "I", "D" };
    const float v[] = { thermalManager.temp_hotend[0].pid.p(), thermalManager.temp_hotend[0].pid.i(), thermalManager.temp_hotend[0].pid.d() };
    const uint8_t d[] = { 2, 2, 2 };
    magna_m257_linea("pidhotend", k, v, d, 3);
  }
  #endif
  #if ENABLED(PIDTEMPBED)
  {
    const char * const k[] = { "P", "I", "D" };
    const float v[] = { thermalManager.temp_bed.pid.p(), thermalManager.temp_bed.pid.i(), thermalManager.temp_bed.pid.d() };
    const uint8_t d[] = { 2, 2, 2 };
    magna_m257_linea("pidcama", k, v, d, 3);
  }
  #endif
  {
    const char * const k[] = { "X", "Y", "Z", "E0", "E1" };
    const float v[] = { planner.settings.axis_steps_per_mm[X_AXIS], planner.settings.axis_steps_per_mm[Y_AXIS],
                        planner.settings.axis_steps_per_mm[Z_AXIS], planner.settings.axis_steps_per_mm[E_AXIS_N(0)],
                        planner.settings.axis_steps_per_mm[E_AXIS_N(EXTRUDERS > 1 ? 1 : 0)] };
    const uint8_t d[] = { 2, 2, 2, 2, 2 };
    magna_m257_linea("pasos", k, v, d, 5);
  }
  #if ENABLED(LIN_ADVANCE)
  {
    const char * const k[] = { "K0", "K1" };
    const float v[] = { planner.extruder_advance_K[E_INDEX_N(0)], planner.extruder_advance_K[E_INDEX_N(EXTRUDERS > 1 ? 1 : 0)] };
    const uint8_t d[] = { 3, 3 };
    magna_m257_linea("avance", k, v, d, 2);
  }
  #endif
  #if ENABLED(INPUT_SHAPING_X) && ENABLED(INPUT_SHAPING_Y)
  {
    const char * const k[] = { "XF", "XD", "YF", "YD" };
    const float v[] = { stepper.get_shaping_frequency(X_AXIS), stepper.get_shaping_damping_ratio(X_AXIS),
                        stepper.get_shaping_frequency(Y_AXIS), stepper.get_shaping_damping_ratio(Y_AXIS) };
    const uint8_t d[] = { 2, 3, 2, 3 };
    magna_m257_linea("vibraciones", k, v, d, 4);
  }
  #endif
  {
    // ajuste fino de la altura Z: con sonda, M851 Z (S=1); sin sonda, M206 Z (S=0)
    const char * const k[] = { "S", "Z" };
    #if HAS_BED_PROBE
      const float v[] = { 1, probe.offset.z };
    #elif HAS_HOME_OFFSET
      const float v[] = { 0, home_offset.z };
    #else
      const float v[] = { 0, 0 };
    #endif
    const uint8_t d[] = { 0, 3 };
    magna_m257_linea("altura", k, v, d, 2);
  }
  {
    const char * const k[] = { "X", "Y", "Z", "E" };
    const float vel[] = { planner.settings.max_feedrate_mm_s[X_AXIS], planner.settings.max_feedrate_mm_s[Y_AXIS],
                          planner.settings.max_feedrate_mm_s[Z_AXIS], planner.settings.max_feedrate_mm_s[E_AXIS_N(0)] };
    const float ace[] = { (float)planner.settings.max_acceleration_mm_per_s2[X_AXIS], (float)planner.settings.max_acceleration_mm_per_s2[Y_AXIS],
                          (float)planner.settings.max_acceleration_mm_per_s2[Z_AXIS], (float)planner.settings.max_acceleration_mm_per_s2[E_AXIS_N(0)] };
    const uint8_t d[] = { 0, 0, 0, 0 };
    magna_m257_linea("velmax", k, vel, d, 4);
    magna_m257_linea("acelmax", k, ace, d, 4);
  }
  {
    const char * const k[] = { "P", "R", "T" };
    const float v[] = { planner.settings.acceleration, planner.settings.retract_acceleration, planner.settings.travel_acceleration };
    const uint8_t d[] = { 0, 0, 0 };
    magna_m257_linea("acel", k, v, d, 3);
  }
  {
    // recuperar tras un corte de luz (M413) y sensor de filamento (M412): 1 = activo, -1 = no está en el firmware
    const char * const k[] = { "PLR", "SF", "SFD" };
    const float v[] = { TERN(POWER_LOSS_RECOVERY, recovery.enabled ? 1.0f : 0.0f, -1.0f),
                        TERN(HAS_FILAMENT_SENSOR, runout.enabled ? 1.0f : 0.0f, -1.0f),
                        TERN(HAS_FILAMENT_RUNOUT_DISTANCE, runout.runout_distance(), 0.0f) };
    const uint8_t d[] = { 0, 0, 1 };
    magna_m257_linea("extras", k, v, d, 3);
  }
  #if ENABLED(PRINTCOUNTER)
  {
    // estadísticas de Marlin: impresiones, terminadas, tiempo total (s), la más larga (s), filamento (mm)
    const printStatistics e = print_job_timer.getStats();
    const char * const k[] = { "N", "OK", "T", "L", "F" };
    const float v[] = { (float)e.totalPrints, (float)e.finishedPrints, (float)e.printTime, (float)e.longestPrint, TERN0(HAS_EXTRUDERS, e.filamentUsed) };
    const uint8_t d[] = { 0, 0, 0, 0, 0 };
    magna_m257_linea("estadisticas", k, v, d, 5);
  }
  #endif
  print_to_wifi("M257 fin\\r\\n");
}

"""

# Carpetas por WiFi (MagnAir): la UI MKS ignora la ruta de "M20" (exploreDisk lista siempre la carpeta
# actual, que después de montar es la raíz). Se entra a la carpeta pedida ("M20 L /CARPETA/SUB", nombres
# cortos 8.3), se lista y se vuelve a la raíz.
LISTA_VIEJA = """  exploreDisk(path, 0, with_longnames);
}"""
LISTA_NUEVA = """  #if HAS_MEDIA
    // Magna2-230 (MagnAir): entrar a la carpeta pedida ("M20 L /CARPETA/SUB")
    const char *ruta = strchr(path, '/');
    while (ruta && *ruta) {
      while (*ruta == '/') ruta++;
      char parte[FILENAME_LENGTH + 1] = { 0 };
      uint8_t n = 0;
      while (*ruta && *ruta != '/' && *ruta != ' ' && n < FILENAME_LENGTH) parte[n++] = *ruta++;
      while (*ruta && *ruta != '/') ruta++;
      if (n) card.cd(parte);
    }
  #endif
  exploreDisk(path, 0, with_longnames);
  TERN_(HAS_MEDIA, card.cdroot());  // Magna2-230: la pantalla y las subidas siguen en la raíz
}"""

# Imprimir desde una carpeta (MagnAir): M23/M24 por WiFi usaban solo lo que está después de la última "/",
# o sea siempre la raíz. Ahora se usa la ruta completa ("M23 /CARPETA/ARCHIVO.GCO"); sin carpeta es igual que antes.
M23_VIEJO = "              char *cur_name = strrchr(list_file.file_name[sel_id],'/');\n"
M23_NUEVO = ("              char *cur_name = strchr(list_file.file_name[sel_id] + 1, '/');  // Magna2-230 (MagnAir): ruta completa\n"
             "              if (!cur_name) cur_name = strrchr(list_file.file_name[sel_id], '/');\n")
M24_VIEJO = "                char *cur_name = strrchr(list_file.file_name[sel_id], '/');\n\n                MediaFile file;\n"
M24_NUEVO = ("                char *cur_name = strchr(list_file.file_name[sel_id] + 1, '/');  // Magna2-230 (MagnAir): ruta completa\n"
             "                if (!cur_name) cur_name = strrchr(list_file.file_name[sel_id], '/');\n\n                MediaFile file;\n")

LIMPIAR = '  lv_obj_clean(scr);\n\n  // breadcrumbs\n'
ESTILO_TITULO = '  if (titleLabel)\n    lv_obj_set_style(titleLabel, &tft_style_label_rel);\n'

CAMBIOS = [
    # archivo, original, nuevo, para qué
    ('draw_ui.h', 'TFT_LV_PARA_BACK_BODY_COLOR  LV_COLOR_MAKE(0x4A, 0x52, 0xFF)', 'TFT_LV_PARA_BACK_BODY_COLOR  LV_COLOR_MAKE(0x7A, 0x12, 0x16)', 'fondo de botones de parámetros: azul -> rojo oscuro'),
    ('draw_ui.h', 'PARA_SEL_ICON_TEXT_COLOR  LV_COLOR_MAKE(0x4A, 0x52, 0xFF)', 'PARA_SEL_ICON_TEXT_COLOR  LV_COLOR_MAKE(0xE0, 0x26, 0x2C)', 'texto seleccionado: azul -> rojo'),
    ('draw_ui.cpp', 'style_line.line.color   = LV_COLOR_MAKE(0x49, 0x54, 0xFF);', 'style_line.line.color   = LV_COLOR_MAKE(0x5A, 0x5A, 0x5A);', 'líneas separadoras: azul -> gris'),
    ('draw_ui.cpp', 'style_sel_text.text.color        = LV_COLOR_YELLOW;', 'style_sel_text.text.color        = LV_COLOR_MAKE(0xFF, 0x4D, 0x4D);', 'texto elegido: amarillo -> rojo claro'),
    ('draw_ui.cpp', 'style_sel_text.text.sel_color    = LV_COLOR_YELLOW;', 'style_sel_text.text.sel_color    = LV_COLOR_MAKE(0xFF, 0x4D, 0x4D);', 'texto elegido: amarillo -> rojo claro'),
    ('draw_keyboard.cpp', 'rel_style.body.main_color   = lv_color_make(0xA9, 0x62, 0x1D);', 'rel_style.body.main_color   = lv_color_make(0x3A, 0x3A, 0x3A);', 'teclado: tecla marrón -> gris'),
    ('draw_keyboard.cpp', 'rel_style.body.grad_color   = lv_color_make(0xA7, 0x59, 0x0E);', 'rel_style.body.grad_color   = lv_color_make(0x30, 0x30, 0x30);', 'teclado: tecla marrón -> gris'),
    ('draw_keyboard.cpp', 'pr_style.body.main_color   = lv_color_make(0x72, 0x42, 0x15);', 'pr_style.body.main_color   = lv_color_make(0x8A, 0x14, 0x1A);', 'teclado: tecla apretada -> rojo'),
    ('draw_keyboard.cpp', 'pr_style.body.grad_color   = lv_color_make(0x6A, 0x3A, 0x0C);', 'pr_style.body.grad_color   = lv_color_make(0x70, 0x10, 0x14);', 'teclado: tecla apretada -> rojo'),
    ('draw_ui.cpp', 'tft_style_scr.body.main_color   = LV_COLOR_BACKGROUND;', 'tft_style_scr.body.main_color   = LV_COLOR_MAKE(0x14, 0x14, 0x14);', 'fondo: degradé, arriba gris oscuro'),
    ('draw_ui.cpp', 'tft_style_scr.body.grad_color   = LV_COLOR_BACKGROUND;', 'tft_style_scr.body.grad_color   = LV_COLOR_MAKE(0x5C, 0x0E, 0x14);', 'fondo: degradé, abajo rojo oscuro'),
    ('draw_ui.cpp', CREAR, '\n' + INC + MENUS + CREAR, 'menús: código de la decoración marcada'),
    ('draw_ui.cpp', '\n' + INC + MENUS + CREAR, '\n' + INC + MENUS + DIALOGOS + IDIOMA + CREAR, 'mensajes: letra grande y barras (código)'),
    ('draw_ui.h', 'lv_obj_t* lv_screen_create(DISP_STATE newScreenType, const char *title = nullptr);', DECLARACIONES + 'lv_obj_t* lv_screen_create(DISP_STATE newScreenType, const char *title = nullptr);', 'mensajes: declaraciones'),
    ('draw_dialog.cpp', '#define BTN_OK_Y      180\n#define BTN_CANCEL_Y  180', '#define BTN_OK_Y      250  // Magna2-230: más abajo, para que entre el texto grande\n#define BTN_CANCEL_Y  250', 'mensajes: botones más abajo'),
    ('draw_dialog.cpp', '  lv_obj_align(tempText1, nullptr, LV_ALIGN_CENTER, 0, -50);', '  lv_obj_align(tempText1, nullptr, LV_ALIGN_CENTER, 0, magna_idioma_latino() ? -95 : -50);  // Magna2-230', 'mensajes: temperatura encima del texto grande'),
    ('draw_dialog.cpp', ROTARY_DIALOGO, DIALOGO_FIN + ROTARY_DIALOGO, 'mensajes: letra grande y barra de carga/descarga'),
    ('draw_printing.cpp', BARRA_IMPRESION, BARRA_IMPRESION + '  magna_estilo_barra(bar1, magna_idioma_latino() ? &magna_fuente_grande : nullptr);  // Magna2-230 (tema)\n' + ALINEAR_PORCENTAJE, 'imprimiendo: barra del tema y porcentaje grande'),
    ('draw_ui.cpp', LIMPIAR, '  lv_obj_clean(scr);\n\n  // Magna2-230 (tema): decoración marcada, dibujada con el fondo (no agrega objetos)\n  const bool magna_menu = magna_menu_de_iconos(newScreenType);\n  if (magna_menu) magna_decorar_menu(scr, !title || title[0] != \'\\0\', newScreenType == PRINT_FILE_UI);\n\n  // breadcrumbs\n', 'menús: dibujar la decoración al crear la pantalla'),
    ('draw_ui.cpp', ESTILO_TITULO, ESTILO_TITULO + '  if (magna_menu && titleLabel && newScreenType != MOVE_MOTOR_UI && newScreenType != BABYSTEP_UI)  // Magna2-230: esas dos escriben su estado arriba a la derecha\n    magna_marca_titulo(scr, titleLabel, &tft_style_label_rel);\n', 'menús: MAGNA 2 a la derecha del título'),
    ('draw_tool.cpp', """        get_gcode_command(AUTO_LEVELING_COMMAND_ADDR, (uint8_t *)public_buf_m);
        public_buf_m[sizeof(public_buf_m) - 1] = 0;
        queue.inject(public_buf_m);""", """        queue.inject(F("G28\\nG29\\nM500"));  // Magna2-230 (BLTouch): home, malla de 5x5 y guardar (el comando guardado en la pantalla era G29 sin home)""", 'BLTouch: botón Nivelación hace G28 + G29 + M500'),
    ('tft_lvgl_configuration.cpp', TOUCH_VIEJO, TOUCH_NUEVO, 'pantalla: apagado automático y encendido con un toque'),
    ('draw_ui.cpp', CREAR + '  lv_obj_t *scr = lv_obj_create(nullptr, nullptr);\n', CREAR + '  magna_pantalla_despertar();  // Magna2-230: una pantalla nueva (aviso, fin de impresión) prende la luz\n  lv_obj_t *scr = lv_obj_create(nullptr, nullptr);\n', 'pantalla: se prende sola con cada pantalla nueva'),
    ('wifi_module.cpp', WIFI_M115, WIFI_M256 + WIFI_M115, 'WiFi: M256 prende/apaga la pantalla y M257 manda la calibración (MagnAir)'),
    ('wifi_module.cpp', WIFI_INCLUDES_VIEJO, WIFI_INCLUDES_NUEVO, 'WiFi: includes para M257'),
    ('wifi_module.cpp', WIFI_EXEC, WIFI_M257_FUNC + WIFI_EXEC, 'WiFi: función M257 (datos de calibración)'),
    ('wifi_module.cpp', LISTA_VIEJA, LISTA_NUEVA, 'WiFi: listar carpetas de la SD (M20 L /CARPETA)'),
    ('wifi_module.cpp', M23_VIEJO, M23_NUEVO, 'WiFi: M23 con ruta completa (imprimir desde carpetas)'),
    ('wifi_module.cpp', M24_VIEJO, M24_NUEVO, 'WiFi: M24 con ruta completa (imprimir desde carpetas)'),
    ('tft_lvgl_configuration.cpp', 'uint8_t bmp_public_buf[16 * 1024];\n', '__attribute__((aligned(4))) uint8_t bmp_public_buf[16 * 1024];  // Magna2-230: alineado; el DMA de la pantalla copia de a 2 bytes y con una dirección impar mostraba todos los colores corridos\n', 'pantalla: buffer de imagen alineado (colores corridos)'),
    ('draw_about.cpp', ACERCA_INICIO, CREDITOS + '\n' + ACERCA_INICIO, 'Acerca de: código de los créditos'),
    ('draw_about.cpp', ACERCA_FIN, ACERCA_FIN + '  magna_creditos(scr, &tft_style_label_rel, magna_idioma_latino());  // Magna2-230: créditos\n', 'Acerca de: créditos (Andrés Londero)'),
    ('draw_ready_print.cpp', '  scr = lv_screen_create(PRINT_READY_UI, "");\n', '  scr = lv_screen_create(PRINT_READY_UI, "");\n' + DECORACION, 'pantalla principal: MAGNA 2 + raya roja + líneas de capas'),
]
# Etapa 41: subida por WiFi con nombre largo. En Marlin, file_writer.saveFileName y el buffer de
# utf8_2_unicode tienen 30 bytes, pero el nombre que manda el módulo puede tener hasta 255: con un
# nombre largo se pisaba la memoria (y la pila) y la placa se reiniciaba al recibir el archivo.
# Se recorta a 29 bytes conservando la extensión y sin cortar una letra con tilde a la mitad.
# Marlin guarda el archivo con nombre 8.3, que sale de las primeras letras: no cambia.
SUBIDA_NOMBRE_FUNC_ANCLA = 'static void file_first_msg_handle(const uint8_t * const msg, const uint16_t msgLen) {\n'
SUBIDA_NOMBRE_FUNC = """// Magna2-230: copia el nombre del archivo recortado a 'cap' bytes (sin contar el 0 del final),
// conservando la extensión (hasta 7 bytes con el punto) y sin dejar media letra UTF-8.
static uint8_t magna_nombre_recortado(uint8_t *sal, const uint8_t cap, const uint8_t *nombre, const uint8_t largo) {
  if (largo <= cap) { memcpy(sal, nombre, largo); return largo; }
  uint8_t ext = 0;
  for (uint8_t i = largo; i > 0 && largo - i < 7; i--)
    if (nombre[i - 1] == '.') { ext = largo - (i - 1); break; }
  uint8_t base = cap - ext;
  while (base > 0 && (nombre[base] & 0xC0) == 0x80) base--;  // no cortar una letra de varios bytes
  memcpy(sal, nombre, base);
  memcpy(sal + base, nombre + largo - ext, ext);
  return base + ext;
}

"""
SUBIDA_NOMBRE_VIEJO = """  memcpy(file_writer.saveFileName, msg + 5, fileNameLen);

  utf8_2_unicode(file_writer.saveFileName, fileNameLen);
"""
SUBIDA_NOMBRE_NUEVO = """  // Magna2-230: el nombre puede traer hasta 255 bytes y acá entran 29 (ver magna_nombre_recortado)
  const uint8_t largoNombre = magna_nombre_recortado(file_writer.saveFileName, sizeof(file_writer.saveFileName) - 1, msg + 5, fileNameLen);

  utf8_2_unicode(file_writer.saveFileName, largoNombre);
"""
CAMBIOS += [
    ('wifi_module.cpp', SUBIDA_NOMBRE_FUNC_ANCLA, SUBIDA_NOMBRE_FUNC + SUBIDA_NOMBRE_FUNC_ANCLA, 'WiFi: función para recortar el nombre del archivo subido'),
    ('wifi_module.cpp', SUBIDA_NOMBRE_VIEJO, SUBIDA_NOMBRE_NUEVO, 'WiFi: nombre largo al subir ya no pisa la memoria (reinicio)'),
]
# Etapa 42: reinicio al terminar cada impresión. Al terminar, Marlin guarda las estadísticas
# (PRINTCOUNTER) en la EEPROM emulada en la flash del STM32F4: borra un sector de 128 KB con las
# interrupciones apagadas (1-2 s). Si el perro guardián (watchdog) venía de no refrescarse un rato
# (redibujar la pantalla del resumen leyendo íconos de la memoria SPI), se pasaba de los 4 s y la placa
# se reiniciaba después del pitido. Se refresca justo antes de borrar (y el watchdog pasa a 8 s en
# Configuration_adv.h, WATCHDOG_DURATION_8S).
EEPROM_FLUSH_VIEJO = """      hal.isr_off();
      eeprom_buffer_flush();
      hal.isr_on();
"""
EEPROM_FLUSH_NUEVO = """      hal.watchdog_refresh();  // Magna2-230 (etapa 42): el borrado tarda 1-2 s sin interrupciones
      hal.isr_off();
      eeprom_buffer_flush();
      hal.isr_on();
      hal.watchdog_refresh();  // Magna2-230 (etapa 42)
"""
CAMBIOS += [
    ('../../../HAL/STM32/eeprom/eeprom_flash.cpp', EEPROM_FLUSH_VIEJO, EEPROM_FLUSH_NUEVO, 'EEPROM: refrescar el watchdog antes de borrar la flash (reinicio al terminar)'),
]
ok = falta = 0
p = os.path.join(R, 'magna_fuente_grande.cpp')
if os.path.exists(p) and open(p, encoding='utf-8').read() == ARCHIVO_FUENTE: print('ya aplicado: letra grande (archivo)'); ok += 1
else: open(p, 'w', encoding='utf-8').write(ARCHIVO_FUENTE); print('ok: letra grande (archivo magna_fuente_grande.cpp)'); ok += 1
# Versión de prueba B (MAGNA_PRUEBA=B, para buscar fallas en la placa V1.2): solo el tema (colores, íconos,
# diálogos, decoración, créditos, M256/M257 de MagnAir); sin extras_pantalla.py, castellano ni liviano.py.
PRUEBA_B = os.environ.get('MAGNA_PRUEBA', '').strip().upper() == 'B'
if PRUEBA_B:
    print('*** VERSIÓN DE PRUEBA B: solo el tema, sin extras ni castellano ***')
else:
    # Etapa 30 en adelante: archivos y cambios nuevos (extras_pantalla.py)
    sys.path.insert(0, AQUI)
    import extras_pantalla
    for nombre, contenido, para in extras_pantalla.ARCHIVOS:
        p = os.path.join(R, nombre)
        if os.path.exists(p) and open(p, encoding='utf-8').read() == contenido: print('ya aplicado:', para); ok += 1
        else: open(p, 'w', encoding='utf-8').write(contenido); print('ok:', para); ok += 1
    CAMBIOS += extras_pantalla.CAMBIOS_EXTRA
for f, a, b, para in CAMBIOS:
    p = os.path.join(R, f); s = open(p, encoding='utf-8').read()
    if b in s: print('ya aplicado:', para); ok += 1; continue
    if s.count(a) != 1: print('NO ENCONTRADO (se deja el color original):', f, '-', para); falta += 1; continue
    open(p, 'w', encoding='utf-8').write(s.replace(a, b)); print('ok:', para); ok += 1
print(f'Colores del tema: {ok} aplicados, {falta} no encontrados')

# Etapa 39: pantalla en castellano completa, carpeta _assets y aviso de modelo sin probar
import subprocess
if PRUEBA_B:
    sys.exit(0)
_r = subprocess.run([sys.executable, os.path.join(AQUI, 'aplicar_idioma.py'), sys.argv[1] if len(sys.argv) > 1 else '.'])
if _r.returncode:
    sys.exit(_r.returncode)

# mm12 (placa V1.2): extras recortados si Configuration.h tiene MAGNA_LIVIANO
_r = subprocess.run([sys.executable, os.path.join(AQUI, 'liviano.py'), sys.argv[1] if len(sys.argv) > 1 else '.'])
if _r.returncode:
    sys.exit(_r.returncode)
