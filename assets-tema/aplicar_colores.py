#!/usr/bin/env python3
"""
Aplica los colores del tema negro/rojo a la interfaz MKS (TFT_LVGL_UI) de Marlin.
Cambia SOLO colores fijos del código de la pantalla, con reemplazos exactos, y avisa si alguno no se encuentra
(por ejemplo, si otra versión de Marlin cambió esas líneas).
Uso: python3 aplicar_colores.py <raíz del proyecto Marlin completo>
"""
import os, sys
R = os.path.join(sys.argv[1] if len(sys.argv) > 1 else '.', 'Marlin/src/lcd/extui/mks_ui')
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
]
ok = falta = 0
for f, a, b, para in CAMBIOS:
    p = os.path.join(R, f); s = open(p, encoding='utf-8').read()
    if b in s: print('ya aplicado:', para); ok += 1; continue
    if s.count(a) != 1: print('NO ENCONTRADO (se deja el color original):', f, '-', para); falta += 1; continue
    open(p, 'w', encoding='utf-8').write(s.replace(a, b)); print('ok:', para); ok += 1
print(f'Colores del tema: {ok} aplicados, {falta} no encontrados')
