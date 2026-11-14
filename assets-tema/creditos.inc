/* Magna2-230: créditos en "Acerca de" (información del sistema), abajo a la izquierda,
 * debajo de los datos de Marlin y a la izquierda del botón Atrás (x >= 359, y >= 178).
 *
 * Lo pega aplicar_colores.py en draw_about.cpp y lo compila la prueba de render, así se prueba
 * exactamente el mismo código. Es C puro (vale como C y como C++).
 *
 * Con idioma latino el nombre va con la letra grande (tiene Latin-1, por la "é"). En los demás
 * idiomas la letra de la pantalla es otra y puede no tener acentos: va en inglés y sin tilde. */
extern lv_font_t magna_fuente_grande;

#define MAGNA_AUTOR_ES  "Creado por Andr\xC3\xA9s Londero"
#define MAGNA_AUTOR_EN  "Created by Andres Londero"
#define MAGNA_CONTACTO  "andreslondero@gmail.com"

void magna_creditos(lv_obj_t *scr, const lv_style_t *base, int latino) {
  static lv_style_t nombre, contacto;
  lv_obj_t *l;
  lv_style_copy(&nombre, base);
  lv_style_copy(&contacto, base);
  if (latino) nombre.text.font = &magna_fuente_grande;
  nombre.text.color = LV_COLOR_WHITE;
  contacto.text.color = LV_COLOR_MAKE(0xFF, 0x8A, 0x8E);   /* rojo claro del tema */

  l = lv_label_create(scr, (lv_obj_t *)NULL);  /* el cast evita la sobrecarga de MKS con texto */
  lv_obj_set_style(l, &nombre);
  lv_label_set_text(l, latino ? MAGNA_AUTOR_ES : MAGNA_AUTOR_EN);
  lv_obj_set_pos(l, 12, 236);

  l = lv_label_create(scr, (lv_obj_t *)NULL);  /* el cast evita la sobrecarga de MKS con texto */
  lv_obj_set_style(l, &contacto);
  lv_label_set_text(l, MAGNA_CONTACTO);
  lv_obj_set_pos(l, 12, 272);
}
