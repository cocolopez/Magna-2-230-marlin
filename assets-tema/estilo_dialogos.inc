/* Magna2-230 (tema): mensajes con letra grande y barras de progreso del tema.
 *
 * - magna_texto_grande(): pasa un texto a la letra grande (fuente_grande.inc, 26 px),
 *   centrado, con salto de línea automático a 460 px, sin moverlo de su altura.
 * - magna_estilo_barra(): barra roja redondeada sobre fondo oscuro con borde rojo apagado.
 *   Si se pasa una letra, el texto que va adentro de la barra (por ejemplo el "%") la usa.
 *
 * Lo pega aplicar_colores.py en draw_ui.cpp y lo compila la prueba de render, así se prueba
 * exactamente el mismo código. Es C puro (vale como C y como C++).
 */
extern lv_font_t magna_fuente_grande;

#define MAGNA_TEXTO_ANCHO 460

void magna_texto_grande(lv_obj_t *etiqueta) {
  static lv_style_t st;
  lv_coord_t centro_y, y;
  if (!etiqueta) return;
  centro_y = lv_obj_get_y(etiqueta) + lv_obj_get_height(etiqueta) / 2;
  lv_style_copy(&st, lv_obj_get_style(etiqueta));
  st.text.font = &magna_fuente_grande;
  st.text.line_space = 2;
  st.text.letter_space = 0;
  lv_obj_set_style(etiqueta, &st);
  lv_label_set_long_mode(etiqueta, LV_LABEL_LONG_BREAK);
  lv_label_set_align(etiqueta, LV_LABEL_ALIGN_CENTER);
  lv_obj_set_width(etiqueta, MAGNA_TEXTO_ANCHO);
  y = centro_y - lv_obj_get_height(etiqueta) / 2;
  if (y < 40) y = 40;                                   /* nunca encima del título */
  lv_obj_set_pos(etiqueta, (480 - MAGNA_TEXTO_ANCHO) / 2, y);
}

void magna_estilo_barra(lv_obj_t *barra, const lv_font_t *letra) {
  static lv_style_t fondo, fondo_letra, relleno;
  lv_style_copy(&fondo, &lv_style_plain);
  fondo.body.main_color = LV_COLOR_MAKE(0x22, 0x22, 0x22);
  fondo.body.grad_color = LV_COLOR_MAKE(0x16, 0x16, 0x16);
  fondo.body.radius = LV_RADIUS_CIRCLE;
  fondo.body.border.width = 2;
  fondo.body.border.color = LV_COLOR_MAKE(0x6A, 0x14, 0x18);
  fondo.body.border.opa = LV_OPA_COVER;
  fondo.body.padding.left = fondo.body.padding.right = 4;
  fondo.body.padding.top = fondo.body.padding.bottom = 4;
  fondo.text.color = LV_COLOR_WHITE;
  lv_style_copy(&relleno, &lv_style_plain);
  relleno.body.main_color = LV_COLOR_MAKE(0xE6, 0x2A, 0x30);
  relleno.body.grad_color = LV_COLOR_MAKE(0x9A, 0x16, 0x1C);
  relleno.body.radius = LV_RADIUS_CIRCLE;
  relleno.body.border.width = 0;
  if (letra) {
    lv_style_copy(&fondo_letra, &fondo);
    fondo_letra.text.font = letra;
    lv_bar_set_style(barra, LV_BAR_STYLE_BG, &fondo_letra);
  }
  else
    lv_bar_set_style(barra, LV_BAR_STYLE_BG, &fondo);
  lv_bar_set_style(barra, LV_BAR_STYLE_INDIC, &relleno);
}
