#!/usr/bin/env python3
"""
Aplica el tema negro/rojo a la interfaz MKS (TFT_LVGL_UI) de Marlin:
  * colores fijos del código de la pantalla (azul/amarillo/marrón de Makerbase -> rojo/gris),
  * fondo con degradé (gris oscuro arriba -> rojo oscuro abajo) en todas las pantallas,
  * decoración de la pantalla principal: "MAGNA 2", raya roja y líneas de capas.
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
      st_capa[i].line.color = LV_COLOR_MAKE(0x50 + i * 0x18, 0x0C + i * 3, 0x10 + i * 3);
      st_capa[i].line.width = 2;
      lv_obj_t *capa = lv_line_create(scr, nullptr);
      lv_line_set_points(capa, pts_capa, 2);
      lv_line_set_style(capa, LV_LINE_STYLE_MAIN, &st_capa[i]);
      lv_obj_set_pos(capa, 0, 236 + i * 4);
    }
  }
'''

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
    ('draw_ui.cpp', 'tft_style_scr.body.grad_color   = LV_COLOR_BACKGROUND;', 'tft_style_scr.body.grad_color   = LV_COLOR_MAKE(0x2E, 0x0A, 0x0D);', 'fondo: degradé, abajo rojo oscuro'),
    ('draw_ready_print.cpp', '  scr = lv_screen_create(PRINT_READY_UI, "");\n', '  scr = lv_screen_create(PRINT_READY_UI, "");\n' + DECORACION, 'pantalla principal: MAGNA 2 + raya roja + líneas de capas'),
]
ok = falta = 0
for f, a, b, para in CAMBIOS:
    p = os.path.join(R, f); s = open(p, encoding='utf-8').read()
    if b in s: print('ya aplicado:', para); ok += 1; continue
    if s.count(a) != 1: print('NO ENCONTRADO (se deja el color original):', f, '-', para); falta += 1; continue
    open(p, 'w', encoding='utf-8').write(s.replace(a, b)); print('ok:', para); ok += 1
print(f'Colores del tema: {ok} aplicados, {falta} no encontrados')
