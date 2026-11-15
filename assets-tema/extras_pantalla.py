"""
Cambios de la pantalla agregados desde la etapa 30 (los usa aplicar_colores.py, después del tema).

Etapa 30: hora (M258 desde MagnAir), capas (M259 desde Cura), línea "Capa · faltan · fin" debajo de
la barra de impresión, hora chica en todas las pantallas, hora grande + fecha + íconos de WiFi y
Telegram en la principal. El código de pantalla está en magna_extras.inc (lo compila también la
prueba de render); acá van los archivos nuevos y los reemplazos exactos en el código de Marlin.

Cada cambio es (archivo, original, nuevo, para qué), igual que CAMBIOS de aplicar_colores.py.
"""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
_leer = lambda n: open(os.path.join(AQUI, n), encoding='utf-8').read()

EXTRAS_INC = _leer('magna_extras.inc')
FUENTE_CHICA = _leer('fuente_chica.inc')
FUENTE_ENORME = _leer('fuente_enorme.inc')
# etapa 32: arranque animado (C++ con las constantes que genera generar_assets.py)
ANIM_GLUE = _leer('animacion_arranque.cpp.inc').replace('#include "animacion_arranque.inc"\n', _leer('animacion_arranque.inc'))
GLUE33 = r'''
// ---- etapa 33 ------------------------------------------------------------------------------------
#if ENABLED(AUTO_BED_LEVELING_BILINEAR)
  #include "../../../feature/bedlevel/bedlevel.h"
#endif
#if ENABLED(CANCEL_OBJECTS)
  #include "../../../feature/cancel_object.h"
  static void magna_cancelar_pieza(int i) { cancelable.cancel_object(i); }
  static int magna_pieza_cancelada(int i) { return cancelable.is_canceled(i); }
#endif

// M262 <nombre>: Cura (Buscar y reemplazar) lo pone en cada ";MESH:<nombre>" (docs-magna/CURA-PANTALLA.md).
// Cada nombre nuevo es una pieza nueva; "NONMESH" (movimientos sin pieza) = ninguna.
void magna_m262() {
  const int i = magna_pieza_indice(parser.string_arg);
  #if ENABLED(CANCEL_OBJECTS)
    if (i >= 0 && i + 1 > cancelable.state.object_count) cancelable.state.object_count = i + 1;
    cancelable.set_active_object(i);
  #else
    UNUSED(i);
  #endif
}

// M263 <texto>: mensaje en la pantalla desde el gcode (lo agrega el editor de MagnAir, etapa 34)
void magna_m263() {
  if (parser.string_arg && parser.string_arg[0]) { magna_pantalla_despertar(); magna_mensaje(parser.string_arg); }
}

void magna_piezas_empezar() {
  magna_piezas_reiniciar();
  TERN_(CANCEL_OBJECTS, cancelable.reset());
  magna_vista_reiniciar();
}

// Volver a dibujar la miniatura (o el tornillo) de la pantalla de impresión, como cuando se vuelve a ella
static void magna_redibujar_previa() {
  extern bool flash_preview_begin, default_preview_flg;
  if (gCfgItems.from_flash_pic) flash_preview_begin = true; else default_preview_flg = true;
}
void magna_vista_crear_impresion(lv_obj_t *scr) {
  magna_vista_cama(X_BED_SIZE, Y_BED_SIZE);
  magna_vista_crear(scr, magna_redibujar_previa);
}

// Volver a armar la pantalla de abajo después de cerrar un mensaje, el bloqueo, "siempre encendida", el gráfico, las piezas o la nivelación (ver
// mg_cerrar_pendientes): igual que cuando se vuelve a ella desde un menú.
static void magna_rehacer_pantalla() {
  lv_img_cache_invalidate_src(NULL);
  switch (disp_state) {
    case PRINT_READY_UI: lv_clear_ready_print(); lv_draw_ready_print(); break;
    case PRINTING_UI: lv_clear_printing(); magna_redibujar_previa(); lv_draw_printing(); break;
    default:
      // cualquier otra pantalla: se repite arriba en la pila y se "vuelve" a ella, como hacen los diálogos de MKS
      if (disp_state_stack._disp_state[disp_state_stack._disp_index] == disp_state && disp_state_stack._disp_index < 98) {
        disp_state_stack._disp_index++;
        disp_state_stack._disp_state[disp_state_stack._disp_index] = disp_state;
        clear_cur_ui();
        draw_return_ui();
      }
      else lv_obj_invalidate(lv_scr_act());
      break;
  }
}

static void magna_tick33(const uint32_t ahora) {
  static uint32_t muestra = 0;
  static bool listo = false;
  if (!listo) {
    TERN_(CANCEL_OBJECTS, magna_piezas_funciones(magna_cancelar_pieza, magna_pieza_cancelada));
    magna_rehacer_funcion(magna_rehacer_pantalla);
    listo = true;
  }
  if (!muestra || ahora - muestra >= 5000) {       // una muestra cada 5 s para el gráfico
    muestra = ahora | 1;
    magna_hist_agregar(thermalManager.wholeDegHotend(0), thermalManager.degTargetHotend(0),
                       TERN0(HAS_HEATED_BED, thermalManager.wholeDegBed()), TERN0(HAS_HEATED_BED, thermalManager.degTargetBed()));
  }
  #if ENABLED(AUTO_BED_LEVELING_BILINEAR)
    if (magna_nivel_abierto()) {                   // nivelación en vivo: lee la malla mientras G29 la llena
      int16_t m[GRID_MAX_POINTS_X * GRID_MAX_POINTS_Y];
      for (uint8_t x = 0; x < GRID_MAX_POINTS_X; x++)
        for (uint8_t y = 0; y < GRID_MAX_POINTS_Y; y++) {
          const float v = bedlevel.z_values[x][y];
          m[x * GRID_MAX_POINTS_Y + y] = isnan(v) ? int16_t(MAGNA_NIVEL_SIN) : int16_t(constrain(lroundf(v * 1000), -32000L, 32000L));
        }
      magna_nivel_actualizar(m);
    }
  #endif
  magna_extras33_tick();
}
'''

# --- archivos nuevos en mks_ui/ ---------------------------------------------------------------
ARCHIVO_FUENTE_CHICA = ('/**\n * Magna2-230 (etapa 30): letra chica (Roboto 14 px, ASCII + Latin-1) para la hora y la línea\n'
                        ' * de información. Archivo agregado por assets-tema/extras_pantalla.py a partir de fuente_chica.inc.\n */\n'
                        '#include "../../../inc/MarlinConfigPre.h"\n\n#if HAS_TFT_LVGL_UI\n\n#include <lvgl.h>\n\n'
                        + FUENTE_CHICA + '\n#endif // HAS_TFT_LVGL_UI\n')

ARCHIVO_EXTRAS = ('/**\n * Magna2-230 (etapa 30): hora, capas, línea de información de la impresión, hora chica en todas\n'
                  ' * las pantallas y hora grande + íconos de estado en la principal.\n'
                  ' * Archivo agregado por assets-tema/extras_pantalla.py: el código de pantalla es magna_extras.inc\n'
                  ' * (el mismo que compila la prueba de render) y abajo está lo que lo une con Marlin.\n */\n'
                  '#include "../../../inc/MarlinConfigPre.h"\n\n#if HAS_TFT_LVGL_UI\n\n'
                  '#include "draw_ui.h"\n#include <lvgl.h>\n#include <stdio.h>\n#include <string.h>\n'
                  '#include "../../../gcode/parser.h"\n#include "../../../libs/buzzer.h"\n#include "../../../module/temperature.h"\n'
                  '#include "../../../libs/W25Qxx.h"\n#include "SPI_TFT.h"\n#include "pic_manager.h"\n'
                  '#if ENABLED(PRINTCOUNTER)\n  #include "../../../module/printcounter.h"\n#endif\n'
                  '#if ENABLED(MKS_WIFI_MODULE)\n  #include "wifi_module.h"\n#endif\n\n'
                  + EXTRAS_INC + '''
// ---- unión con Marlin ----------------------------------------------------------------------

// M259 L<capa> T<total>: lo agrega Cura en cada ";LAYER:" (docs-magna/CURA-PANTALLA.md)
void magna_m259() {
  magna_capas_poner(parser.seenval('L') ? parser.value_int() : -1, parser.seenval('T') ? parser.value_int() : -1);
}

static bool magna_imprimiendo();
static void magna_tick33(const uint32_t ahora);

// Una vez por segundo, desde LV_TASK_HANDLER: hora chica (todas las pantallas menos la principal) y
// hora grande, fecha e íconos de la principal.
void magna_tick() {
  static uint32_t ultimo = 0;
  const uint32_t ahora = millis();
  if (ahora - ultimo < 1000) return;
  ultimo = ahora;
  const bool principal = disp_state == PRINT_READY_UI;
  magna_reloj_mostrar(ahora, !principal);
  magna_capa_arriba_tick(ahora, magna_imprimiendo());  // etapa 31: mensajes, bloqueo, "siempre encendida"
  magna_anim_datos(thermalManager.fanSpeedPercent(0), thermalManager.wholeDegHotend(0), thermalManager.degTargetHotend(0),  // etapa 32
                   TERN0(HAS_HEATED_BED, thermalManager.wholeDegBed()), TERN0(HAS_HEATED_BED, thermalManager.degTargetBed()),
                   !magna_ambiente_visible() && magna_pantalla_encendida());
  magna_tick33(ahora);  // etapa 33: gráfico, nivelación en vivo, piezas, vista en vivo
  if (principal) magna_principal_actualizar(ahora, TERN0(MKS_WIFI_MODULE, wifi_link_state == WIFI_CONNECTED));
}

// ---- etapa 31 ------------------------------------------------------------------------------
static bool magna_imprimiendo() {
  return uiCfg.print_state == WORKING || uiCfg.print_state == PAUSING || uiCfg.print_state == PAUSED || uiCfg.print_state == RESUMING;
}

// La pantalla se iba a apagar sola: si está imprimiendo y está activada la opción, en vez de apagarla
// se muestra la pantalla negra con el porcentaje enorme ("siempre encendida").
bool magna_ambiente_en_vez_de_apagar() {
  if (!magna_opcion(MAGNA_OP_AMBIENTE) || !magna_imprimiendo()) return false;
  magna_ambiente_mostrar(millis());
  return true;
}

// Filamento gastado: lo cuenta Marlin (PRINTCOUNTER, el temporizador arranca con el M109/M190 del gcode)
static float magna_fil_inicio = 0;
void magna_filamento_inicio() {
  #if ENABLED(PRINTCOUNTER)
    magna_fil_inicio = print_job_timer.getStats().filamentUsed;
  #endif
}

void magna_resumen_terminada(lv_obj_t *scr, lv_obj_t *titulo) {
  const uint32_t seg = print_time.hours * 3600UL + print_time.minutes * 60UL + print_time.seconds;
  float mm = 0;
  #if ENABLED(PRINTCOUNTER)
    mm = print_job_timer.getStats().filamentUsed - magna_fil_inicio;
    if (mm < 0) mm = 0;
  #endif
  magna_resumen(scr, titulo, seg, mm);
}

// Melodías con el zumbador de la placa (se pueden apagar desde MagnAir). La cola de notas es de 4:
// cada melodía tiene como mucho 4 notas para no frenar la impresora.
static void magna_melodia(const uint16_t (*notas)[2], const uint8_t n) {
  #if HAS_BEEPER
    if (!magna_opcion(MAGNA_OP_MELODIAS)) return;
    for (uint8_t i = 0; i < n; i++) BUZZ(notas[i][1], notas[i][0]);
  #else
    UNUSED(notas); UNUSED(n);
  #endif
}
void magna_melodia_fin() {        // do-mi-sol-do
  static const uint16_t notas[4][2] = { { 1047, 140 }, { 1319, 140 }, { 1568, 140 }, { 2093, 320 } };
  magna_melodia(notas, 4);
}
void magna_melodia_atencion() {   // tres pitidos
  static const uint16_t notas[4][2] = { { 1760, 120 }, { 0, 90 }, { 1760, 120 }, { 1760, 250 } };
  magna_melodia(notas, 4);
}

''' + ANIM_GLUE + GLUE33 + '''
#endif // HAS_TFT_LVGL_UI
''')

ARCHIVO_FUENTE_ENORME = ARCHIVO_FUENTE_CHICA.replace(FUENTE_CHICA, FUENTE_ENORME).replace(
    'letra chica (Roboto 14 px, ASCII + Latin-1) para la hora y la línea\n * de información', 'números enormes (Roboto 72 px, solo "0-9 % :")\n * para la pantalla "siempre encendida" (etapa 31)').replace('fuente_chica.inc', 'fuente_enorme.inc')

ARCHIVOS = [('magna_fuente_chica.cpp', ARCHIVO_FUENTE_CHICA, 'letra chica (archivo magna_fuente_chica.cpp)'),
            ('magna_fuente_enorme.cpp', ARCHIVO_FUENTE_ENORME, 'números enormes (archivo magna_fuente_enorme.cpp)'),
            ('magna_extras.cpp', ARCHIVO_EXTRAS, 'hora, capas e información (archivo magna_extras.cpp)')]

# --- reemplazos -------------------------------------------------------------------------------
DECL_ANCLA = 'void magna_estilo_barra(lv_obj_t *barra, const lv_font_t *letra);\n'
DECL_NUEVAS = DECL_ANCLA + '''// Magna2-230 (etapa 30): hora, capas e información de la impresión (magna_extras.cpp)
void magna_hora_poner(int32_t seg, int dsem, int dia, int mes, int tg, uint32_t ahora_ms);
void magna_capas_poner(int capa, int capas);
void magna_capas_reiniciar(void);
void magna_reloj_crear(void);
void magna_principal_crear(lv_obj_t *scr);
void magna_principal_olvidar(void);
lv_obj_t *magna_info_crear(lv_obj_t *scr);
void magna_info_actualizar(lv_obj_t *l, uint32_t ahora_ms, uint32_t slicer_s, uint32_t transcurrido_s, int pct);
void magna_tick();
// Magna2-230 (etapa 31): mensajes, bloqueo, "siempre encendida", resumen y melodías (magna_extras.cpp)
void magna_opciones_poner(int op, long precio_kg, int densidad);
void magna_mensaje(const char *texto);
void magna_candado_crear(lv_obj_t *scr);
int magna_ambiente_visible(void);
void magna_ambiente_cerrar(void);
bool magna_ambiente_en_vez_de_apagar();
void magna_filamento_inicio();
void magna_resumen_terminada(lv_obj_t *scr, lv_obj_t *titulo);
void magna_melodia_fin();
void magna_melodia_atencion();
// Magna2-230 (etapa 32): animaciones (magna_extras.cpp)
void magna_anim_iniciar(void);
void magna_anim_registrar(lv_obj_t *ventilador, lv_obj_t *barra, lv_obj_t *temp_hotend, lv_obj_t *temp_cama);
void magna_anim_iconos(lv_obj_t *hotend, lv_obj_t *cama);
void magna_anim_olvidar(void);
void magna_arranque_animado();
// Magna2-230 (etapa 33): gráfico, nivelación, piezas, vista en vivo (magna_extras.cpp)
void magna_botones_impresion(lv_obj_t *scr);
void magna_boton_grafico_principal(lv_obj_t *scr);
void magna_rehacer_funcion(void (*f)(void));
void magna_nivel_abrir(int nx, int ny);
void magna_vista_crear_impresion(lv_obj_t *scr);
void magna_vista_olvidar(void);
void magna_piezas_empezar();
'''

TAREAS_VIEJO = '  GUI_RefreshPage();\n\n  TERN_(MKS_WIFI_MODULE, get_wifi_commands());\n'
TAREAS_NUEVO = '  GUI_RefreshPage();\n\n  magna_tick();  // Magna2-230 (etapa 30): hora e íconos, una vez por segundo\n\n  TERN_(MKS_WIFI_MODULE, get_wifi_commands());\n'

INIT_VIEJO = '  if (ready) lv_draw_ready_print();\n'
INIT_NUEVO = '  magna_reloj_crear();  // Magna2-230 (etapa 30): hora chica arriba a la derecha (capa de arriba de LVGL)\n\n' + INIT_VIEJO

PRINCIPAL_VIEJO = '      lv_obj_set_pos(capa, 0, 236 + i * 4);\n    }\n  }\n'
PRINCIPAL_NUEVO = PRINCIPAL_VIEJO + '  magna_principal_crear(scr);  // Magna2-230 (etapa 30): hora grande, fecha e íconos de WiFi y Telegram\n'
LIMPIAR_PRINCIPAL_VIEJO = 'void lv_clear_ready_print() {\n'
LIMPIAR_PRINCIPAL_NUEVO = LIMPIAR_PRINCIPAL_VIEJO + '  magna_principal_olvidar();  // Magna2-230 (etapa 30): sus objetos se borran con la pantalla\n'

VARS_VIEJO = 'static lv_obj_t *bar1, *bar1ValueText;\n'
VARS_NUEVO = (VARS_VIEJO + 'static lv_obj_t *magna_info;  // Magna2-230 (etapa 30): "Capa 57/210 · faltan 2:15 · fin 23:40"\n'
              'static int magna_pct;         // último porcentaje, para estimar lo que falta si el slicer no lo manda\n')
BARRA_VIEJA = '  lv_obj_set_pos(bar1, 205, 36);\n'
BARRA_NUEVA = '  lv_obj_set_pos(bar1, 205, 32);  // Magna2-230 (etapa 30): 4 px más arriba, para la línea de información\n'
INFO_ANCLA = ('  magna_estilo_barra(bar1, magna_idioma_latino() ? &magna_fuente_grande : nullptr);  // Magna2-230 (tema)\n'
              '  lv_obj_align(bar1ValueText, bar1, LV_ALIGN_CENTER, 0, 0);\n')
INFO_NUEVO = INFO_ANCLA + '  magna_info = magna_info_crear(scr);  // Magna2-230 (etapa 30)\n'
TIEMPO_VIEJO = '''void disp_print_time() {
  #if ENABLED(SET_REMAINING_TIME)
    const uint32_t r = ui.get_remaining_time();
    sprintf_P(public_buf_l, PSTR("%02d:%02d R"), r / 3600, (r % 3600) / 60);
  #else
    sprintf_P(public_buf_l, PSTR("%d%d:%d%d:%d%d"), print_time.hours / 10, print_time.hours % 10, print_time.minutes / 10, print_time.minutes % 10, print_time.seconds / 10, print_time.seconds % 10);
  #endif
  lv_label_set_text(labelTime, public_buf_l);
}'''
TIEMPO_NUEVO = '''void disp_print_time() {
  // Magna2-230 (etapa 30): el reloj muestra siempre el tiempo transcurrido; lo que falta y la hora de
  // fin van en la línea de información, debajo de la barra.
  sprintf_P(public_buf_l, PSTR("%d%d:%d%d:%d%d"), print_time.hours / 10, print_time.hours % 10, print_time.minutes / 10, print_time.minutes % 10, print_time.seconds / 10, print_time.seconds % 10);
  lv_label_set_text(labelTime, public_buf_l);
  const uint32_t transcurrido = print_time.hours * 3600UL + print_time.minutes * 60UL + print_time.seconds;
  magna_info_actualizar(magna_info, millis(), TERN0(SET_REMAINING_TIME, ui.get_remaining_time()), transcurrido, magna_pct);
}'''
PCT_VIEJO = '  if (rate <= 0) return;\n'
PCT_NUEVO = PCT_VIEJO + '  magna_pct = rate;  // Magna2-230 (etapa 30)\n'
RESET_VIEJO = 'void reset_print_time() {\n'
RESET_NUEVO = RESET_VIEJO + '  magna_capas_reiniciar();  // Magna2-230 (etapa 30): impresión nueva\n  magna_pct = 0;\n'

GCODE_INC_VIEJO = '#include "gcode.h"\n'
GCODE_INC_NUEVO = GCODE_INC_VIEJO + '#if HAS_TFT_LVGL_UI\n  void magna_m259();  // Magna2-230 (etapa 30): capa actual/total desde Cura (mks_ui/magna_extras.cpp)\n#endif\n'
GCODE_CASE_VIEJO = '      case 220: M220(); break;'
GCODE_CASE_NUEVO = ('      #if HAS_TFT_LVGL_UI\n        case 259: magna_m259(); break;                          // Magna2-230: M259 L<capa> T<total> (Cura)\n      #endif\n'
                    + GCODE_CASE_VIEJO)

WIFI_M258_ANCLA = '      case 257: magna_m257(); send_ok_to_wifi(); break;  // Magna2-230 (MagnAir): datos de calibración\n'
WIFI_M258 = '''      case 258: {  // Magna2-230 (MagnAir, etapa 30): hora local para la pantalla. "M258 S<seg> D<día sem.> F<día> O<mes> T<bot>"
        const char * const s = strchr(mStr, 'S'), * const d = strchr(mStr, 'D'), * const f = strchr(mStr, 'F'),
                   * const o = strchr(mStr, 'O'), * const t = strchr(mStr, 'T');
        if (s) magna_hora_poner(atol(s + 1), d ? atoi(d + 1) : 0, f ? atoi(f + 1) : 0, o ? atoi(o + 1) : 0, t ? atoi(t + 1) : 0, millis());
        // etapa 31: opciones de la pantalla (A), precio del filamento por kilo (P) y densidad × 100 (G)
        const char * const a = strchr(mStr, 'A'), * const pr = strchr(mStr, 'P'), * const g = strchr(mStr, 'G');
        magna_opciones_poner(a ? atoi(a + 1) : -1, pr ? atol(pr + 1) : -1, g ? atoi(g + 1) : -1);
        send_ok_to_wifi();
      } break;

      case 117:  // Magna2-230 (MagnAir, etapa 31): "M117 texto" por WiFi = mensaje en la pantalla
        if (spStr && spStr[1]) { magna_pantalla_despertar(); magna_mensaje(spStr + 1); }
        send_ok_to_wifi();
        break;

''' + WIFI_M258_ANCLA

# --- etapa 31 ---
APAGAR_VIEJO = '''      WRITE(TFT_BACKLIGHT_PIN, LOW);
      magna_apagada = true;
    }'''
APAGAR_NUEVO = '''      if (magna_ambiente_en_vez_de_apagar())  // Magna2-230 (etapa 31): imprimiendo, "siempre encendida"
        magna_ultimo_uso = millis();
      else {
        WRITE(TFT_BACKLIGHT_PIN, LOW);
        magna_apagada = true;
      }
    }'''
TRAGAR_VIEJO = '    if (magna_apagada) tragar = true;\n'
TRAGAR_NUEVO = '    if (magna_apagada || magna_ambiente_visible()) tragar = true;  // etapa 31: el toque que saca "siempre encendida" tampoco aprieta nada\n'
DESPERTAR_VIEJO = 'void magna_pantalla_despertar() {\n  magna_ultimo_uso = millis();\n'
DESPERTAR_NUEVO = DESPERTAR_VIEJO + '  magna_ambiente_cerrar();  // Magna2-230 (etapa 31): un toque o una pantalla nueva sacan "siempre encendida"\n'
CANDADO_ANCLA = '  magna_info = magna_info_crear(scr);  // Magna2-230 (etapa 30)\n'
CANDADO_NUEVO = CANDADO_ANCLA + '  magna_candado_crear(scr);  // Magna2-230 (etapa 31): bloquear la pantalla mientras imprime\n'
FIN_VIEJO = '        lv_clear_printing();\n        lv_draw_dialog(DIALOG_TYPE_FINISH_PRINT);\n'
FIN_NUEVO = '        magna_melodia_fin();  // Magna2-230 (etapa 31)\n' + FIN_VIEJO
RESET_ANCLA = '  magna_capas_reiniciar();  // Magna2-230 (etapa 30): impresión nueva\n'
RESET_FIL = RESET_ANCLA + '  magna_filamento_inicio();  // etapa 31: para el resumen al terminar\n'
ROTARY_DIALOGO = '  #if HAS_ROTARY_ENCODER\n    if (gCfgItems.encoder_enable) {\n      if (btnOk) lv_group_add_obj(g, btnOk);'
RESUMEN_NUEVO = '''  // Magna2-230 (etapa 31): resumen al terminar y aviso con el zumbador cuando hay que poner filamento
  if (DIALOG_IS(TYPE_FINISH_PRINT)) magna_resumen_terminada(scr, labelDialog);
  #if ENABLED(ADVANCED_PAUSE_FEATURE)
    if (DIALOG_IS(PAUSE_MESSAGE_INSERT, PAUSE_MESSAGE_WAITING)) magna_melodia_atencion();
  #endif
''' + ROTARY_DIALOGO

# --- etapa 32 ---
INIT_ANIM_VIEJO = '  magna_reloj_crear();  // Magna2-230 (etapa 30): hora chica arriba a la derecha (capa de arriba de LVGL)\n'
INIT_ANIM_NUEVO = INIT_ANIM_VIEJO + '  magna_anim_iniciar();  // etapa 32: animaciones de la pantalla de impresión\n'
ANIM_REG_ANCLA = '  magna_candado_crear(scr);  // Magna2-230 (etapa 31): bloquear la pantalla mientras imprime\n'
ANIM_REG_NUEVO = ANIM_REG_ANCLA + '  magna_anim_registrar(buttonFanstate, bar1, labelExt1, TERN(HAS_HEATED_BED, labelBed, nullptr));  // etapa 32\n'
# etapa 37: en la pantalla de impresión también se animan los íconos de hotend y cama
ANIM_REG_NUEVO += '  magna_anim_iconos(buttonExt1, TERN(HAS_HEATED_BED, buttonBedstate, nullptr));  // etapa 37\n'
# y en la principal: íconos de abajo + color y titileo de sus temperaturas
PRINC_ANIM_VIEJO = '    TERN_(HAS_FAN, labelFan = lv_label_create_empty(scr));\n\n    lv_temp_refr();\n  }\n'
PRINC_ANIM_NUEVO = ('    TERN_(HAS_FAN, labelFan = lv_label_create_empty(scr));\n\n    lv_temp_refr();\n'
                    '    magna_anim_registrar(nullptr, nullptr, labelExt1, TERN(HAS_HEATED_BED, labelBed, nullptr));  // Magna2-230 (etapa 37)\n'
                    '    magna_anim_iconos(buttonExt1, TERN(HAS_HEATED_BED, buttonBedstate, nullptr));\n  }\n')
LIMPIAR_PRINC_ANIM_VIEJO = '  magna_principal_olvidar();  // Magna2-230 (etapa 30): sus objetos se borran con la pantalla\n'
LIMPIAR_PRINC_ANIM_NUEVO = LIMPIAR_PRINC_ANIM_VIEJO + '  magna_anim_olvidar();  // etapa 37\n'
LIMPIAR_IMP_VIEJO = 'void lv_clear_printing() {\n'
LIMPIAR_IMP_NUEVO = LIMPIAR_IMP_VIEJO + '  magna_anim_olvidar();  // Magna2-230 (etapa 32): sus objetos se borran con la pantalla\n'
ASSETS_VIEJO = '  F("bmp_fan_state.bin"),\n'
ASSETS_NUEVO = ASSETS_VIEJO + ('  F("bmp_fan_state1.bin"),  // Magna2-230 (etapa 32): el ventilador que gira\n  F("bmp_fan_state2.bin"),\n'
                               '  F("bmp_bed_state1.bin"),  // Magna2-230 (etapa 37): calor de la cama y gota del hotend\n  F("bmp_bed_state2.bin"),\n'
                               '  F("bmp_ext1_state1.bin"),\n  F("bmp_ext1_state2.bin"),\n'
                               '  F("bmp_tornillo1.bin"),    // Magna2-230 (etapa 32): arranque animado\n  F("bmp_tornillo2.bin"),\n  F("bmp_tornillo3.bin"),\n')
LOGO_VIEJO = '  #if PIN_EXISTS(TFT_BACKLIGHT)\n    OUT_WRITE(TFT_BACKLIGHT_PIN, HIGH);\n  #endif\n  TERN_(HAS_LOGO_IN_FLASH, delay(2000));\n'
LOGO_NUEVO = ('  #if PIN_EXISTS(TFT_BACKLIGHT)\n    OUT_WRITE(TFT_BACKLIGHT_PIN, HIGH);\n  #endif\n'
              '  magna_arranque_animado();  // Magna2-230 (etapa 32): el tornillo se imprime (~1,4 s)\n'
              '  TERN_(HAS_LOGO_IN_FLASH, delay(800));\n')

# --- etapa 33 ---
BOTONES_ANCLA = '  magna_anim_registrar(buttonFanstate, bar1, labelExt1, TERN(HAS_HEATED_BED, labelBed, nullptr));  // etapa 32\n'
BOTONES_NUEVO = BOTONES_ANCLA + ('  magna_botones_impresion(scr);      // etapa 33: piezas y gráfico (arriba, junto al candado)\n'
                                 '  magna_vista_crear_impresion(scr);  // etapa 33: tocar la vista previa = vista en vivo\n')
OLVIDAR_ANCLA = '  magna_anim_olvidar();  // Magna2-230 (etapa 32): sus objetos se borran con la pantalla\n'
OLVIDAR_NUEVO = OLVIDAR_ANCLA + '  magna_vista_olvidar();  // etapa 33\n'
RESET33_ANCLA = '  magna_filamento_inicio();  // etapa 31: para el resumen al terminar\n'
RESET33_NUEVO = RESET33_ANCLA + '  magna_piezas_empezar();  // etapa 33: piezas y vista en vivo en cero\n'
GRAF_PRINC_ANCLA = '  magna_principal_crear(scr);  // Magna2-230 (etapa 30): hora grande, fecha e íconos de WiFi y Telegram\n'
GRAF_PRINC_NUEVO = GRAF_PRINC_ANCLA + '  magna_boton_grafico_principal(scr);  // etapa 33: gráfico de temperaturas\n'
NIVEL_ANCLA = 'queue.inject(F("G28\\nG29\\nM500"));'
NIVEL_NUEVO = NIVEL_ANCLA + '\n        TERN_(AUTO_BED_LEVELING_BILINEAR, magna_nivel_abrir(GRID_MAX_POINTS_X, GRID_MAX_POINTS_Y));  // etapa 33: nivelación en vivo'
G1_INC_VIEJO = '#include "../gcode.h"\n'
G1_INC_NUEVO = G1_INC_VIEJO + '#if HAS_TFT_LVGL_UI\n  void magna_vista_linea(float x0, float y0, float x1, float y1, float z);  // Magna2-230 (etapa 33): vista en vivo\n#endif\n'
G1_VIEJO = '  get_destination_from_command();                 // Get X Y [Z[I[J[K]]]] [E] F (and set cutter power)\n'
G1_NUEVO = G1_VIEJO + ('  #if HAS_TFT_LVGL_UI\n    if (destination.e > current_position.e)   // Magna2-230 (etapa 33): dibujar lo que extruye (vista en vivo)\n'
                       '      magna_vista_linea(current_position.x, current_position.y, destination.x, destination.y, destination.z);\n  #endif\n')
PARSER_VIEJO = '    TERN_(HAS_STATUS_MESSAGE, case 117:)\n'
PARSER_NUEVO = PARSER_VIEJO + '    TERN_(HAS_TFT_LVGL_UI, case 262: case 263:)   // Magna2-230 (etapas 33-34): M262 <pieza>, M263 <mensaje>\n'
M262_INC_VIEJO = '  void magna_m259();  // Magna2-230 (etapa 30): capa actual/total desde Cura (mks_ui/magna_extras.cpp)\n'
M262_INC_NUEVO = M262_INC_VIEJO + '  void magna_m262();  // Magna2-230 (etapa 33): pieza actual (Cura ;MESH:) para cancelar piezas\n  void magna_m263();  // Magna2-230 (etapa 34): mensaje en la pantalla desde el gcode\n'
M262_VIEJO = '        case 259: magna_m259(); break;                          // Magna2-230: M259 L<capa> T<total> (Cura)\n'
M262_NUEVO = M262_VIEJO + '        case 262: magna_m262(); break;                          // Magna2-230: M262 <pieza> (Cura)\n        case 263: magna_m263(); break;                          // Magna2-230: M263 <mensaje> (editor de MagnAir)\n'

# Etapa 37: los íconos de la memoria SPI están comprimidos (RLE) y el original solo sabía volver al
# principio (seek a 4). Cuando LVGL redibujaba un pedazo de un ícono (por ejemplo al juntar las zonas de
# dos textos que cambian, o al cerrar algo que lo tapaba) leía las filas equivocadas: rayas o íconos en
# blanco. Ahora se lleva la posición real: si piden más adelante se saltean bytes, si piden más atrás
# se vuelve al principio y se avanza. Así se puede animar un ícono o redibujar cualquier parte.
FLASH_LEER_VIEJO = """lv_fs_res_t spi_flash_read_cb (lv_fs_drv_t * drv, void * file_p, void * buf, uint32_t btr, uint32_t * br) {
  lv_pic_test((uint8_t *)buf, pic_read_addr_offset, btr);
  *br = btr;
  return LV_FS_RES_OK;
}

lv_fs_res_t spi_flash_seek_cb(lv_fs_drv_t * drv, void * file_p, uint32_t pos) {
  #if HAS_SPI_FLASH_COMPRESSION
    if (pos == 4) {
      uint8_t bmp_header[4];
      SPIFlash.beginRead(pic_read_base_addr);
      SPIFlash.readData(bmp_header, 4);
      currentFlashPage = 1;
    }
    pic_read_addr_offset = pic_read_base_addr;
  #else
    pic_read_addr_offset = pic_read_base_addr + pos;
  #endif
  return LV_FS_RES_OK;
}

lv_fs_res_t spi_flash_tell_cb(lv_fs_drv_t * drv, void * file_p, uint32_t * pos_p) {
  *pos_p = pic_read_addr_offset - pic_read_base_addr;
  return LV_FS_RES_OK;
}"""
FLASH_LEER_NUEVO = """// Magna2-230 (etapa 37): posición real dentro del ícono comprimido (bytes ya entregados)
static uint32_t magna_pos_flash = 0;

lv_fs_res_t spi_flash_read_cb (lv_fs_drv_t * drv, void * file_p, void * buf, uint32_t btr, uint32_t * br) {
  #if HAS_SPI_FLASH_COMPRESSION
    if (currentFlashPage == 0) magna_pos_flash = 0;   // recién abierto: lv_pic_test empieza del principio
  #endif
  lv_pic_test((uint8_t *)buf, pic_read_addr_offset, btr);
  magna_pos_flash += btr;
  *br = btr;
  return LV_FS_RES_OK;
}

lv_fs_res_t spi_flash_seek_cb(lv_fs_drv_t * drv, void * file_p, uint32_t pos) {
  #if HAS_SPI_FLASH_COMPRESSION
    // Magna2-230 (etapa 37): ir a cualquier posición (antes solo al principio)
    if (currentFlashPage == 0 || pos < magna_pos_flash || pos == 4) {
      uint8_t bmp_header[4];
      SPIFlash.beginRead(pic_read_base_addr);
      SPIFlash.readData(bmp_header, 4);
      currentFlashPage = 1;
      magna_pos_flash = 4;
    }
    uint8_t descarte[64];
    while (magna_pos_flash < pos) {                   // avanzar descomprimiendo hasta donde piden
      const uint32_t n = pos - magna_pos_flash < sizeof(descarte) ? pos - magna_pos_flash : sizeof(descarte);
      SPIFlash.readData(descarte, n);
      magna_pos_flash += n;
    }
    pic_read_addr_offset = pic_read_base_addr;
  #else
    pic_read_addr_offset = pic_read_base_addr + pos;
    magna_pos_flash = pos;
  #endif
  return LV_FS_RES_OK;
}

lv_fs_res_t spi_flash_tell_cb(lv_fs_drv_t * drv, void * file_p, uint32_t * pos_p) {
  *pos_p = magna_pos_flash;
  return LV_FS_RES_OK;
}"""
CAMBIOS_EXTRA = [
    ('draw_ready_print.cpp', PRINC_ANIM_VIEJO, PRINC_ANIM_NUEVO, 'etapa 37: principal: íconos y temperaturas animados'),
    ('tft_lvgl_configuration.cpp', FLASH_LEER_VIEJO, FLASH_LEER_NUEVO, 'etapa 37: íconos comprimidos: leer desde cualquier fila'),
    ('draw_ui.h', DECL_ANCLA, DECL_NUEVAS, 'etapa 30: declaraciones (hora, capas, información)'),
    ('draw_ui.cpp', TAREAS_VIEJO, TAREAS_NUEVO, 'etapa 30: hora e íconos una vez por segundo'),
    ('tft_lvgl_configuration.cpp', INIT_VIEJO, INIT_NUEVO, 'etapa 30: hora chica en todas las pantallas'),
    ('draw_ready_print.cpp', PRINCIPAL_VIEJO, PRINCIPAL_NUEVO, 'etapa 30: principal con hora grande e íconos'),
    ('draw_ready_print.cpp', LIMPIAR_PRINCIPAL_VIEJO, LIMPIAR_PRINCIPAL_NUEVO, 'etapa 30: principal: olvidar sus objetos al salir'),
    ('draw_ready_print.cpp', LIMPIAR_PRINC_ANIM_VIEJO, LIMPIAR_PRINC_ANIM_NUEVO, 'etapa 37: principal: olvidar los íconos animados'),
    ('draw_printing.cpp', VARS_VIEJO, VARS_NUEVO, 'etapa 30: imprimiendo: variables de la línea de información'),
    ('draw_printing.cpp', BARRA_VIEJA, BARRA_NUEVA, 'etapa 30: imprimiendo: barra 4 px más arriba'),
    ('draw_printing.cpp', INFO_ANCLA, INFO_NUEVO, 'etapa 30: imprimiendo: línea "Capa · faltan · fin"'),
    ('draw_printing.cpp', TIEMPO_VIEJO, TIEMPO_NUEVO, 'etapa 30: imprimiendo: tiempo transcurrido y actualizar la línea'),
    ('draw_printing.cpp', PCT_VIEJO, PCT_NUEVO, 'etapa 30: imprimiendo: recordar el porcentaje'),
    ('draw_printing.cpp', RESET_VIEJO, RESET_NUEVO, 'etapa 30: imprimiendo: capas en cero al empezar'),
    ('../../../gcode/gcode.cpp', GCODE_INC_VIEJO, GCODE_INC_NUEVO, 'etapa 30: M259 (declaración)'),
    ('../../../gcode/gcode.cpp', GCODE_CASE_VIEJO, GCODE_CASE_NUEVO, 'etapa 30: M259 capa actual/total (Cura)'),
    ('wifi_module.cpp', WIFI_M258_ANCLA, WIFI_M258, 'etapa 30: M258 hora desde MagnAir'),
    ('tft_lvgl_configuration.cpp', APAGAR_VIEJO, APAGAR_NUEVO, 'etapa 31: imprimiendo, "siempre encendida" en vez de apagar'),
    ('tft_lvgl_configuration.cpp', TRAGAR_VIEJO, TRAGAR_NUEVO, 'etapa 31: el toque que la saca no aprieta nada'),
    ('tft_lvgl_configuration.cpp', DESPERTAR_VIEJO, DESPERTAR_NUEVO, 'etapa 31: tocar o una pantalla nueva sacan "siempre encendida"'),
    ('draw_printing.cpp', CANDADO_ANCLA, CANDADO_NUEVO, 'etapa 31: candado para bloquear la pantalla'),
    ('draw_printing.cpp', FIN_VIEJO, FIN_NUEVO, 'etapa 31: melodía al terminar'),
    ('draw_printing.cpp', RESET_ANCLA, RESET_FIL, 'etapa 31: filamento al empezar (para el resumen)'),
    ('draw_dialog.cpp', ROTARY_DIALOGO, RESUMEN_NUEVO, 'etapa 31: resumen al terminar y aviso de filamento'),
    ('tft_lvgl_configuration.cpp', INIT_ANIM_VIEJO, INIT_ANIM_NUEVO, 'etapa 32: tarea de las animaciones'),
    ('draw_printing.cpp', ANIM_REG_ANCLA, ANIM_REG_NUEVO, 'etapa 32: animaciones de la pantalla de impresión'),
    ('draw_printing.cpp', LIMPIAR_IMP_VIEJO, LIMPIAR_IMP_NUEVO, 'etapa 32: olvidar sus objetos al salir'),
    ('pic_manager.cpp', ASSETS_VIEJO, ASSETS_NUEVO, 'etapa 32: imágenes nuevas (ventilador y arranque)'),
    ('SPI_TFT.cpp', LOGO_VIEJO, LOGO_NUEVO, 'etapa 32: arranque animado'),
    ('draw_printing.cpp', BOTONES_ANCLA, BOTONES_NUEVO, 'etapa 33: botones de piezas y gráfico, vista en vivo'),
    ('draw_printing.cpp', OLVIDAR_ANCLA, OLVIDAR_NUEVO, 'etapa 33: olvidar la vista en vivo al salir'),
    ('draw_printing.cpp', RESET33_ANCLA, RESET33_NUEVO, 'etapa 33: piezas y vista en vivo en cero al empezar'),
    ('draw_ready_print.cpp', GRAF_PRINC_ANCLA, GRAF_PRINC_NUEVO, 'etapa 33: botón del gráfico en la principal'),
    ('draw_tool.cpp', NIVEL_ANCLA, NIVEL_NUEVO, 'etapa 33: nivelación en vivo al tocar Nivelación (BLTouch)'),
    ('../../../gcode/motion/G0_G1.cpp', G1_INC_VIEJO, G1_INC_NUEVO, 'etapa 33: vista en vivo (declaración)'),
    ('../../../gcode/motion/G0_G1.cpp', G1_VIEJO, G1_NUEVO, 'etapa 33: vista en vivo (cada G1 que extruye)'),
    ('../../../gcode/parser.cpp', PARSER_VIEJO, PARSER_NUEVO, 'etapa 33: M262 con nombre'),
    ('../../../gcode/gcode.cpp', M262_INC_VIEJO, M262_INC_NUEVO, 'etapa 33: M262 (declaración)'),
    ('../../../gcode/gcode.cpp', M262_VIEJO, M262_NUEVO, 'etapa 33: M262 pieza actual (Cura)'),
]
