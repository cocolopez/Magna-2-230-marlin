/* Magna2-230 (tema): decoración "marcada" de los menús de íconos.
 *
 * Todo se dibuja desde UN solo objeto transparente, detrás de los botones y sin capturar
 * toques, con lv_draw_rect (LVGL 6.1). Así no se crean decenas de objetos lv_line y no se
 * gasta memoria de la pantalla.
 *
 *   - franja oscura del título con acento rojo a la izquierda
 *   - línea roja de lado a lado debajo del título, con marcas tipo regla
 *     (cortas cada 20 px, largas en el borde de cada columna de íconos)
 *   - separador punteado entre las dos filas de íconos
 *   - tres "capas" rojas en el borde de abajo (de oscuro a rojo)
 *   - en la lista de archivos: línea vertical que separa la navegación
 *   - etiqueta "MAGNA 2" a la derecha del título, solo si el título deja lugar
 *
 * Este archivo lo inserta aplicar_colores.py en draw_ui.cpp y también lo compila la prueba
 * de render (pruebas/render-lvgl), así lo que se prueba es exactamente lo que se flashea.
 * Es C puro (vale como C y como C++).
 */
#define MAGNA_ANCHO        480
#define MAGNA_ALTO         320
#define MAGNA_Y_LINEA       32   /* línea roja debajo del título (2 px) */
#define MAGNA_Y_FILAS      177   /* entre la fila de íconos de arriba (y 36) y la de abajo (y 178) */
#define MAGNA_Y_CAPAS      309   /* tres líneas de 2 px: 309, 313, 317 */
#define MAGNA_X_NAV        356   /* lista de archivos: columna de navegación */
#define MAGNA_COL          119   /* ancho de columna de íconos (117 + 2) */

static lv_style_t magna_st_rect;
static uint8_t magna_con_titulo, magna_con_nav;

static void magna_rect(const lv_area_t *mask, lv_coord_t x1, lv_coord_t y1, lv_coord_t x2, lv_coord_t y2,
                       uint8_t r, uint8_t g, uint8_t b) {
  lv_area_t a;
  a.x1 = x1; a.y1 = y1; a.x2 = x2; a.y2 = y2;
  magna_st_rect.body.main_color = LV_COLOR_MAKE(r, g, b);
  magna_st_rect.body.grad_color = magna_st_rect.body.main_color;
  lv_draw_rect(&a, mask, &magna_st_rect, LV_OPA_COVER);
}

static bool magna_dibujar(lv_obj_t *obj, const lv_area_t *mask, lv_design_mode_t modo) {
  (void)obj;
  if (modo == LV_DESIGN_COVER_CHK) return false;   /* transparente: no tapa el fondo */
  if (modo != LV_DESIGN_DRAW_MAIN) return true;

  const lv_coord_t fin_filas = magna_con_nav ? MAGNA_X_NAV - 4 : MAGNA_ANCHO;
  lv_coord_t x;
  uint8_t i;

  if (magna_con_titulo) {
    magna_rect(mask, 0, 0, MAGNA_ANCHO - 1, MAGNA_Y_LINEA - 1, 0x0A, 0x0A, 0x0A);  /* franja del título */
    magna_rect(mask, 0, 6, 2, 25, 0xD6, 0x20, 0x27);                               /* acento rojo */
  }
  magna_rect(mask, 0, MAGNA_Y_LINEA, MAGNA_ANCHO - 1, MAGNA_Y_LINEA + 1, 0xD6, 0x20, 0x27);  /* línea roja */

  /* regla: marcas cortas cada 20 px y largas en el borde de cada columna de íconos */
  for (x = 20; x < MAGNA_ANCHO; x += 20)
    magna_rect(mask, x, MAGNA_Y_LINEA + 2, x, MAGNA_Y_LINEA + 3, 0x5A, 0x14, 0x18);
  for (x = MAGNA_COL; x < MAGNA_ANCHO - 10; x += MAGNA_COL)
    magna_rect(mask, x, MAGNA_Y_LINEA + 2, x, MAGNA_Y_LINEA + 6, 0x8C, 0x18, 0x1E);

  /* separador punteado entre filas: 6 px de trazo cada 12 px */
  for (x = 0; x < fin_filas; x += 12)
    magna_rect(mask, x, MAGNA_Y_FILAS, (x + 5 < fin_filas ? x + 5 : fin_filas - 1), MAGNA_Y_FILAS, 0x8C, 0x18, 0x1E);

  /* capas de abajo, de rojo oscuro a rojo */
  for (i = 0; i < 3; i++) {
    const uint8_t r = (uint8_t)(0x86 + i * 0x28), g = (uint8_t)(0x14 + i * 6), b = (uint8_t)(0x1A + i * 6);
    magna_rect(mask, 0, MAGNA_Y_CAPAS + i * 4, MAGNA_ANCHO - 1, MAGNA_Y_CAPAS + i * 4 + 1, r, g, b);
  }

  if (magna_con_nav)
    magna_rect(mask, MAGNA_X_NAV, 40, MAGNA_X_NAV, 304, 0x8C, 0x18, 0x1E);
  return true;
}

/* Crea la capa de decoración. Llamar ANTES de crear el título y los botones (queda detrás). */
static void magna_decorar_menu(lv_obj_t *scr, bool con_titulo, bool con_nav) {
  lv_obj_t *d;
  lv_style_copy(&magna_st_rect, &lv_style_plain);
  magna_st_rect.body.radius = 0;
  magna_st_rect.body.border.width = 0;
  magna_st_rect.body.shadow.width = 0;
  magna_st_rect.body.opa = LV_OPA_COVER;
  magna_con_titulo = con_titulo;
  magna_con_nav = con_nav;
  d = lv_obj_create(scr, (lv_obj_t *)NULL);
  lv_obj_set_pos(d, 0, 0);
  lv_obj_set_size(d, MAGNA_ANCHO, MAGNA_ALTO);
  lv_obj_set_click(d, false);
  lv_obj_set_design_cb(d, magna_dibujar);
}

/* "MAGNA 2" chico a la derecha del título. Si el título es largo y se pisarían, no se pone. */
static void magna_marca_titulo(lv_obj_t *scr, lv_obj_t *titulo, const lv_style_t *base) {
  static lv_style_t st_gris, st_rojo;
  lv_obj_t *dos, *magna;
  lv_style_copy(&st_gris, base);
  st_gris.text.color = LV_COLOR_MAKE(0x70, 0x70, 0x70);
  st_gris.text.letter_space = 2;
  lv_style_copy(&st_rojo, base);
  st_rojo.text.color = LV_COLOR_MAKE(0xD6, 0x20, 0x27);
  dos = lv_label_create(scr, (lv_obj_t *)NULL);
  lv_label_set_text(dos, "2");
  lv_obj_set_style(dos, &st_rojo);
  magna = lv_label_create(scr, (lv_obj_t *)NULL);
  lv_label_set_text(magna, "MAGNA");
  lv_obj_set_style(magna, &st_gris);
  lv_obj_align(dos, scr, LV_ALIGN_IN_TOP_RIGHT, -10, 5);
  lv_obj_align(magna, dos, LV_ALIGN_OUT_LEFT_MID, -6, 0);
  if (titulo && lv_obj_get_x(titulo) + lv_obj_get_width(titulo) + 12 > lv_obj_get_x(magna)) {
    lv_obj_del(magna);
    lv_obj_del(dos);
  }
}
