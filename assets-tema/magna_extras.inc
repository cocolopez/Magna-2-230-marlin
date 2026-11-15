/**
 * Magna2-230 (etapa 30): hora, capas y línea de información de la impresión.
 *
 *  - Hora: la manda MagnAir (el módulo WiFi la saca de internet) con "M258 S<segundos desde la
 *    medianoche> D<día de la semana> F<día> O<mes> T<1 = hay bot de Telegram>" cada 10 minutos.
 *    Marlin no tiene reloj: entre una y otra se cuenta con millis(). Sin módulo no se muestra hora.
 *  - Capas: "M259 L<capa> T<total>" dentro del gcode (lo agrega Cura con "Buscar y reemplazar":
 *    ver docs-magna/CURA-PANTALLA.md). L es la ";LAYER:" de Cura, que empieza en 0.
 *  - Línea debajo de la barra de impresión: "Capa 57/210 · faltan 2:15 · fin 23:40" (cada parte
 *    solo si se sabe; lo que falta sale de M73 R del slicer o se estima con el tiempo y el %).
 *  - Hora chica arriba a la derecha en todas las pantallas (en la capa de arriba de LVGL, un solo
 *    objeto) y hora grande + fecha + íconos de WiFi y Telegram en la pantalla principal.
 *
 * Lo pega aplicar_colores.py (extras_pantalla.py) en mks_ui/magna_extras.cpp y lo compila la prueba
 * de render. Es C puro (vale como C y como C++). Lo que depende de Marlin (millis, estado del WiFi,
 * qué pantalla se ve) se lo pasa el que llama.
 */
extern lv_font_t magna_fuente_grande;
extern lv_font_t magna_fuente_chica;

/* ---------------------------------------------------------------- hora */
static int32_t mg_seg = -1;  /* segundos desde la medianoche local cuando llegó el M258 (-1 = nunca) */
static uint32_t mg_ms;       /* millis() en ese momento */
static uint8_t mg_dsem, mg_dia, mg_mes, mg_tg;

void magna_hora_poner(int32_t seg, int dsem, int dia, int mes, int tg, uint32_t ahora_ms) {
  if (seg < 0 || seg >= 86400L) return;
  mg_seg = seg;
  mg_ms = ahora_ms;
  mg_dsem = (uint8_t)(((dsem % 7) + 7) % 7);
  mg_dia = (uint8_t)dia;
  mg_mes = (uint8_t)mes;
  mg_tg = tg ? 1 : 0;
}

/* Hora local de ahora. Devuelve 0 si todavía no llegó ninguna. */
int magna_hora(uint32_t ahora_ms, int *h, int *m, int *dsem) {
  uint32_t s, dias;
  if (mg_seg < 0) return 0;
  s = (uint32_t)mg_seg + (ahora_ms - mg_ms) / 1000U;
  dias = s / 86400U;
  s %= 86400U;
  if (h) *h = (int)(s / 3600U);
  if (m) *m = (int)((s % 3600U) / 60U);
  if (dsem) *dsem = (int)((mg_dsem + dias) % 7U);
  return 1;
}

int magna_hay_telegram(void) { return mg_tg; }

/* ---------------------------------------------------------------- capas */
static int16_t mg_capa = -1, mg_capas = -1;

/* capa: la ";LAYER:" de Cura (desde 0); capas: el total. -1 = no cambiar */
void magna_capas_poner(int capa, int capas) {
  if (capa >= 0) mg_capa = (int16_t)capa;
  if (capas > 0) mg_capas = (int16_t)capas;
}

void magna_capas_reiniciar(void) { mg_capa = mg_capas = -1; }

/* ---------------------------------------------------------------- textos (sin LVGL: se prueban en la compu) */

/* Segundos que faltan: los del slicer (M73 R) si los mandó; si no, una estimación con lo que tardó
   hasta ahora y el porcentaje. -1 = todavía no se puede saber. */
int32_t magna_faltan(uint32_t slicer_s, uint32_t transcurrido_s, int pct) {
  if (slicer_s > 0) return (int32_t)slicer_s;
  if (pct >= 3 && pct < 100 && transcurrido_s >= 60)
    return (int32_t)((uint64_t)transcurrido_s * (uint32_t)(100 - pct) / (uint32_t)pct);
  return -1;
}

#define MG_AGREGAR(...) do { if (k < n - 1) { int r_ = snprintf(s + k, (size_t)(n - k), __VA_ARGS__); k = (r_ < 0) ? k : (k + r_ >= n ? n - 1 : k + r_); } } while (0)
#define MG_PUNTO "\xC2\xB7"  /* "·" en UTF-8 */

/* "Capa 57/210 · faltan 2:15 · fin 23:40". capa: 1 en adelante (-1 = no se sabe). */
void magna_texto_info(char *s, int n, int capa, int capas, int32_t faltan, int hora_ok, int h, int m) {
  int k = 0;
  if (n <= 0) return;
  s[0] = 0;
  if (capa > 0) {
    if (capas > 0) MG_AGREGAR("Capa %d/%d", capa, capas);
    else MG_AGREGAR("Capa %d", capa);
  }
  if (faltan >= 0) {
    if (k) MG_AGREGAR(" " MG_PUNTO " ");
    MG_AGREGAR("faltan %ld:%02ld", (long)(faltan / 3600), (long)((faltan % 3600) / 60));
    if (hora_ok) {
      const long fin = ((long)h * 3600L + (long)m * 60L + (long)faltan) % 86400L;
      MG_AGREGAR(" " MG_PUNTO " fin %02ld:%02ld", fin / 3600L, (fin % 3600L) / 60L);
    }
  }
}

static const char *const MG_DIAS[7] = { "dom", "lun", "mar", "mi\xC3\xA9", "jue", "vie", "s\xC3\xA1" "b" };

/* "sáb 14/11" (o vacío si el módulo no mandó la fecha) */
void magna_texto_fecha(char *s, int n, int dsem) {
  int k = 0;
  if (n <= 0) return;
  s[0] = 0;
  if (!mg_dia || !mg_mes) return;
  MG_AGREGAR("%s %d/%d", MG_DIAS[((dsem % 7) + 7) % 7], mg_dia, mg_mes);
}

/* ---------------------------------------------------------------- LVGL */

static void mg_poner_texto(lv_obj_t *l, const char *t) {
  if (l && strcmp(lv_label_get_text(l), t) != 0) lv_label_set_text(l, t);  /* solo redibuja si cambió */
}

static void mg_ocultar(lv_obj_t *o, int ocultar) {
  if (o && lv_obj_get_hidden(o) != (ocultar ? true : false)) lv_obj_set_hidden(o, ocultar ? true : false);
}

/* --- hora chica, arriba a la derecha de todas las pantallas (menos la principal) --- */
static lv_obj_t *mg_reloj;

void magna_reloj_crear(void) {
  static lv_style_t st;
  if (mg_reloj) return;
  lv_style_copy(&st, &lv_style_plain);
  st.text.color = LV_COLOR_MAKE(0xC8, 0xC8, 0xC8);
  st.text.font = &magna_fuente_chica;
  mg_reloj = lv_label_create(lv_layer_top(), (lv_obj_t *)NULL);
  lv_obj_set_style(mg_reloj, &st);
  lv_obj_set_click(mg_reloj, false);
  lv_label_set_text(mg_reloj, "");
  lv_obj_set_hidden(mg_reloj, true);
}

void magna_reloj_mostrar(uint32_t ahora_ms, int visible) {
  char t[8];
  int h, m;
  if (!mg_reloj) return;
  if (!visible || !magna_hora(ahora_ms, &h, &m, NULL)) { mg_ocultar(mg_reloj, 1); return; }
  snprintf(t, sizeof t, "%02d:%02d", h, m);
  mg_poner_texto(mg_reloj, t);
  lv_obj_set_pos(mg_reloj, 476 - lv_obj_get_width(mg_reloj), 10);
  mg_ocultar(mg_reloj, 0);
}

/* --- pantalla principal: hora grande, fecha e íconos de WiFi y Telegram --- */
static lv_obj_t *mg_p_hora, *mg_p_fecha, *mg_p_wifi[4], *mg_p_avion[2];
static lv_style_t mg_st_icono, mg_st_icono_apagado;

/* arcos del WiFi, calculados una vez (radios 6, 12, 18; de 225° a 315°, abiertos hacia arriba) */
static lv_point_t mg_pts_wifi[3][7];
static const lv_point_t mg_pts_avion[5] = { { 0, 14 }, { 28, 2 }, { 20, 27 }, { 12, 18 }, { 0, 14 } };
static const lv_point_t mg_pts_pliegue[2] = { { 28, 2 }, { 12, 18 } };

static void mg_calcular_wifi(void) {
  static const int8_t cosenos[7] = { -71, -50, -26, 0, 26, 50, 71 };   /* cos y sen de 225°..315° × 100 */
  static const int8_t senos[7] = { -71, -87, -97, -100, -97, -87, -71 };
  int r, i;
  for (r = 0; r < 3; r++)
    for (i = 0; i < 7; i++) {
      const int radio = 6 + r * 6;
      mg_pts_wifi[r][i].x = (lv_coord_t)(18 + cosenos[i] * radio / 100);
      mg_pts_wifi[r][i].y = (lv_coord_t)(22 + senos[i] * radio / 100);
    }
}

void magna_principal_crear(lv_obj_t *scr) {
  static lv_style_t st_hora, st_fecha;
  static int listo = 0;
  int i;
  if (!listo) {
    mg_calcular_wifi();
    lv_style_copy(&st_hora, &lv_style_plain);
    st_hora.text.color = LV_COLOR_MAKE(0xEE, 0xEE, 0xEE);
    st_hora.text.font = &magna_fuente_grande;
    lv_style_copy(&st_fecha, &lv_style_plain);
    st_fecha.text.color = LV_COLOR_MAKE(0x96, 0x96, 0x96);
    st_fecha.text.font = &magna_fuente_chica;
    lv_style_copy(&mg_st_icono, &lv_style_plain);
    mg_st_icono.line.color = LV_COLOR_MAKE(0xEE, 0xEE, 0xEE);
    mg_st_icono.line.width = 3;
    mg_st_icono.line.rounded = 1;
    lv_style_copy(&mg_st_icono_apagado, &mg_st_icono);
    mg_st_icono_apagado.line.color = LV_COLOR_MAKE(0x55, 0x55, 0x55);
    listo = 1;
  }
  mg_p_hora = lv_label_create(scr, (lv_obj_t *)NULL);
  lv_obj_set_style(mg_p_hora, &st_hora);
  lv_label_set_text(mg_p_hora, "");
  mg_p_fecha = lv_label_create(scr, (lv_obj_t *)NULL);
  lv_obj_set_style(mg_p_fecha, &st_fecha);
  lv_label_set_text(mg_p_fecha, "");
  for (i = 0; i < 3; i++) {
    mg_p_wifi[i] = lv_line_create(scr, (lv_obj_t *)NULL);
    lv_line_set_points(mg_p_wifi[i], mg_pts_wifi[i], 7);
    lv_line_set_style(mg_p_wifi[i], LV_LINE_STYLE_MAIN, &mg_st_icono);
    lv_obj_set_pos(mg_p_wifi[i], 340, 26);
  }
  mg_p_wifi[3] = lv_line_create(scr, (lv_obj_t *)NULL);              /* el punto de abajo */
  {
    static const lv_point_t punto[2] = { { 17, 22 }, { 19, 22 } };
    lv_line_set_points(mg_p_wifi[3], punto, 2);
  }
  lv_line_set_style(mg_p_wifi[3], LV_LINE_STYLE_MAIN, &mg_st_icono);
  lv_obj_set_pos(mg_p_wifi[3], 340, 26);
  mg_p_avion[0] = lv_line_create(scr, (lv_obj_t *)NULL);
  lv_line_set_points(mg_p_avion[0], mg_pts_avion, 5);
  mg_p_avion[1] = lv_line_create(scr, (lv_obj_t *)NULL);
  lv_line_set_points(mg_p_avion[1], mg_pts_pliegue, 2);
  for (i = 0; i < 2; i++) {
    lv_line_set_style(mg_p_avion[i], LV_LINE_STYLE_MAIN, &mg_st_icono);
    lv_obj_set_pos(mg_p_avion[i], 298, 28);
    lv_obj_set_hidden(mg_p_avion[i], true);
  }
}

void magna_principal_actualizar(uint32_t ahora_ms, int wifi_ok) {
  char t[24];
  int h, m, dsem, i;
  if (!mg_p_hora) return;
  if (magna_hora(ahora_ms, &h, &m, &dsem)) {
    snprintf(t, sizeof t, "%02d:%02d", h, m);
    mg_poner_texto(mg_p_hora, t);
    magna_texto_fecha(t, sizeof t, dsem);
    mg_poner_texto(mg_p_fecha, t);
  }
  else {
    mg_poner_texto(mg_p_hora, "");
    mg_poner_texto(mg_p_fecha, "");
  }
  lv_obj_set_pos(mg_p_hora, 458 - lv_obj_get_width(mg_p_hora), 16);
  lv_obj_set_pos(mg_p_fecha, 458 - lv_obj_get_width(mg_p_fecha), 49);
  for (i = 0; i < 4; i++) {
    lv_style_t *st = wifi_ok ? &mg_st_icono : &mg_st_icono_apagado;
    if (lv_line_get_style(mg_p_wifi[i], LV_LINE_STYLE_MAIN) != st) lv_line_set_style(mg_p_wifi[i], LV_LINE_STYLE_MAIN, st);
  }
  for (i = 0; i < 2; i++) mg_ocultar(mg_p_avion[i], !mg_tg);
}

/* El objeto se borra con la pantalla: hay que olvidarlo al salir de la principal. */
void magna_principal_olvidar(void) { mg_p_hora = NULL; }

/* --- pantalla de impresión: línea debajo de la barra --- */
static int mg_ult_pct_info = -1;          /* para la pantalla "siempre encendida" (etapa 31) */
static int32_t mg_ult_faltan_info = -1;
lv_obj_t *magna_info_crear(lv_obj_t *scr) {
  static lv_style_t st;
  lv_obj_t *l;
  lv_style_copy(&st, &lv_style_plain);
  st.text.color = LV_COLOR_MAKE(0xFF, 0xCD, 0xCD);
  st.text.font = &magna_fuente_chica;
  l = lv_label_create(scr, (lv_obj_t *)NULL);
  lv_obj_set_style(l, &st);
  lv_label_set_long_mode(l, LV_LABEL_LONG_CROP);
  lv_label_set_align(l, LV_LABEL_ALIGN_CENTER);
  lv_obj_set_width(l, 274);
  lv_obj_set_pos(l, 203, 73);
  lv_label_set_text(l, "");
  return l;
}

void magna_info_actualizar(lv_obj_t *l, uint32_t ahora_ms, uint32_t slicer_s, uint32_t transcurrido_s, int pct) {
  char t[72];
  int h = 0, m = 0;
  const int ok = magna_hora(ahora_ms, &h, &m, NULL);
  if (!l) return;
  magna_texto_info(t, sizeof t, mg_capa >= 0 ? mg_capa + 1 : -1, mg_capas,
                   magna_faltan(slicer_s, transcurrido_s, pct), ok, h, m);
  mg_poner_texto(l, t);
  mg_ult_pct_info = pct;
  mg_ult_faltan_info = magna_faltan(slicer_s, transcurrido_s, pct);
}

/* =================================================================================================
 * Etapa 31: opciones, resumen al terminar, mensajes desde MagnAir, bloqueo y "siempre encendida".
 * ================================================================================================= */
extern lv_font_t magna_fuente_enorme;   /* Roboto 72: solo "0-9 % :" (fuente_enorme.inc) */

/* --- opciones que manda MagnAir en el M258 (A<bits> P<precio por kilo> G<densidad × 100>) --- */
#define MAGNA_OP_ANIMACIONES 1
#define MAGNA_OP_MELODIAS    2
#define MAGNA_OP_AMBIENTE    4
static uint8_t mg_op = 0xFF;          /* sin MagnAir: todo prendido */
static uint32_t mg_precio_kg;         /* 0 = no mostrar el costo */
static uint16_t mg_densidad = 124;    /* PLA */

void magna_opciones_poner(int op, long precio_kg, int densidad) {
  if (op >= 0) mg_op = (uint8_t)op;
  if (precio_kg >= 0) mg_precio_kg = (uint32_t)precio_kg;
  if (densidad >= 50 && densidad <= 300) mg_densidad = (uint16_t)densidad;
}

int magna_opcion(int bit) { return (mg_op & bit) != 0; }

/* --- textos del resumen (sin LVGL: se prueban en la compu) --- */

/* "3 h 42 min", "42 min", "menos de 1 min" */
void magna_texto_duracion(char *s, int n, uint32_t seg) {
  int k = 0;
  const uint32_t h = seg / 3600U, m = (seg % 3600U) / 60U;
  if (n <= 0) return;
  s[0] = 0;
  if (h) MG_AGREGAR("%lu h %lu min", (unsigned long)h, (unsigned long)m);
  else if (m) MG_AGREGAR("%lu min", (unsigned long)m);
  else MG_AGREGAR("menos de 1 min");
}

/* gramos de filamento de 1,75 mm: largo (mm) × área (cm²) × densidad */
static float mg_gramos(float mm, int densidad) { return mm / 10.0f * 3.14159265f * 0.0875f * 0.0875f * (float)densidad / 100.0f; }

/* "48 g · 16,1 m" */
void magna_texto_filamento(char *s, int n, float mm, int densidad) {
  int k = 0;
  const long dm = (long)(mm / 100.0f + 0.5f);   /* decímetros, para un decimal en metros */
  if (n <= 0) return;
  s[0] = 0;
  MG_AGREGAR("%ld g " MG_PUNTO " %ld,%ld m", (long)(mg_gramos(mm, densidad) + 0.5f), dm / 10, dm % 10);
}

/* "$ 1.250" (con punto de miles); vacío si no hay precio */
void magna_texto_costo(char *s, int n, float mm, int densidad, uint32_t precio_kg) {
  int k = 0;
  long pesos;
  if (n <= 0) return;
  s[0] = 0;
  if (!precio_kg) return;
  pesos = (long)(mg_gramos(mm, densidad) * (float)precio_kg / 1000.0f + 0.5f);
  if (pesos >= 1000000L) MG_AGREGAR("$ %ld.%03ld.%03ld", pesos / 1000000L, (pesos / 1000L) % 1000L, pesos % 1000L);
  else if (pesos >= 1000L) MG_AGREGAR("$ %ld.%03ld", pesos / 1000L, pesos % 1000L);
  else MG_AGREGAR("$ %ld", pesos);
}

/* --- capa de arriba: un contenedor que ocupa toda la pantalla (tapa y recibe los toques) --- */
static lv_obj_t *mg_tapa(lv_style_t *st) {
  lv_obj_t *c = lv_cont_create(lv_layer_top(), (lv_obj_t *)NULL);
  lv_obj_set_style(c, st);
  lv_obj_set_pos(c, 0, 0);
  lv_obj_set_size(c, 480, 320);
  lv_cont_set_layout(c, LV_LAYOUT_OFF);
  lv_obj_set_click(c, true);
  return c;
}

static lv_obj_t *mg_etiqueta(lv_obj_t *padre, const lv_font_t *letra, lv_color_t color, const char *texto, lv_style_t *st) {
  lv_obj_t *l = lv_label_create(padre, (lv_obj_t *)NULL);
  lv_style_copy(st, &lv_style_plain);
  st->text.color = color;
  st->text.font = letra;
  lv_obj_set_style(l, st);
  lv_label_set_text(l, texto);
  return l;
}

/* Botón del tema: fondo oscuro, borde rojo, texto blanco */
static lv_obj_t *mg_boton(lv_obj_t *padre, lv_coord_t x, lv_coord_t y, lv_coord_t w, lv_coord_t h, const char *texto, lv_event_cb_t cb) {
  static lv_style_t rel, pr;
  static int listo = 0;
  lv_obj_t *b, *l;
  if (!listo) {
    lv_style_copy(&rel, &lv_style_plain);
    rel.body.main_color = rel.body.grad_color = LV_COLOR_MAKE(0x1A, 0x1A, 0x1A);
    rel.body.radius = 8;
    rel.body.border.width = 2;
    rel.body.border.color = LV_COLOR_MAKE(0xD6, 0x20, 0x27);
    rel.body.border.opa = LV_OPA_COVER;
    rel.text.color = LV_COLOR_MAKE(0xEE, 0xEE, 0xEE);
    rel.text.font = &magna_fuente_chica;
    lv_style_copy(&pr, &rel);
    pr.body.main_color = pr.body.grad_color = LV_COLOR_MAKE(0x7A, 0x12, 0x16);
    listo = 1;
  }
  b = lv_btn_create(padre, (lv_obj_t *)NULL);
  lv_obj_set_pos(b, x, y);
  lv_obj_set_size(b, w, h);
  lv_btn_set_style(b, LV_BTN_STYLE_REL, &rel);
  lv_btn_set_style(b, LV_BTN_STYLE_PR, &pr);
  lv_obj_set_event_cb(b, cb);
  l = lv_label_create(b, (lv_obj_t *)NULL);
  lv_label_set_text(l, texto);
  return b;
}

/* --- resumen al terminar: se agrega al mensaje "Impresión terminada" --- */
void magna_resumen(lv_obj_t *scr, lv_obj_t *titulo, uint32_t seg, float mm) {
  static lv_style_t st_clave, st_valor, st_signo;
  char t[40];
  const char *iconos[2] = { "F:/bmp_time_state.bin", "F:/bmp_ext1_state.bin" };
  const char *claves[3] = { "Tiempo", "Filamento", "Costo" };
  int filas = mg_precio_kg ? 3 : 2, i;
  if (titulo) lv_obj_set_y(titulo, 34);
  for (i = 0; i < filas; i++) {
    const lv_coord_t y = (lv_coord_t)(96 + i * 48);
    lv_obj_t *l;
    if (i < 2) {
      lv_obj_t *img = lv_img_create(scr, (lv_obj_t *)NULL);
      lv_img_set_src(img, iconos[i]);
      lv_obj_set_pos(img, 70, y);
    }
    else {
      l = mg_etiqueta(scr, &magna_fuente_grande, LV_COLOR_MAKE(0xD6, 0x20, 0x27), "$", &st_signo);
      lv_obj_set_pos(l, 84, y + 6);
    }
    l = mg_etiqueta(scr, &magna_fuente_chica, LV_COLOR_MAKE(0x96, 0x96, 0x96), claves[i], &st_clave);
    lv_obj_set_pos(l, 128, y + 14);
    if (i == 0) magna_texto_duracion(t, sizeof t, seg);
    else if (i == 1) magna_texto_filamento(t, sizeof t, mm, mg_densidad);
    else magna_texto_costo(t, sizeof t, mm, mg_densidad, mg_precio_kg);
    l = mg_etiqueta(scr, &magna_fuente_grande, LV_COLOR_MAKE(0xEE, 0xEE, 0xEE), t, &st_valor);
    lv_obj_set_pos(l, 410 - lv_obj_get_width(l), y + 6);
  }
}

/* --- mensaje desde MagnAir o Telegram ("M117 texto" por WiFi) --- */
static lv_obj_t *mg_msg;
static int mg_msg_borrar;

static void mg_msg_cb(lv_obj_t *o, lv_event_t e) {
  (void)o;
  if (e == LV_EVENT_RELEASED && mg_msg) { lv_obj_set_hidden(mg_msg, true); mg_msg_borrar = 1; }
}

void magna_mensaje(const char *texto) {
  static lv_style_t st_tapa, st_caja, st_cab, st_txt;
  lv_obj_t *caja, *l;
  if (mg_msg) { lv_obj_del(mg_msg); mg_msg = NULL; }
  mg_msg_borrar = 0;
  lv_style_copy(&st_tapa, &lv_style_plain);
  st_tapa.body.main_color = st_tapa.body.grad_color = LV_COLOR_BLACK;
  st_tapa.body.opa = LV_OPA_50;
  mg_msg = mg_tapa(&st_tapa);
  lv_style_copy(&st_caja, &lv_style_plain);
  st_caja.body.main_color = st_caja.body.grad_color = LV_COLOR_MAKE(0x1A, 0x1A, 0x1A);
  st_caja.body.radius = 10;
  st_caja.body.border.width = 2;
  st_caja.body.border.color = LV_COLOR_MAKE(0xD6, 0x20, 0x27);
  st_caja.body.border.opa = LV_OPA_COVER;
  caja = lv_cont_create(mg_msg, (lv_obj_t *)NULL);
  lv_obj_set_style(caja, &st_caja);
  lv_cont_set_layout(caja, LV_LAYOUT_OFF);
  lv_obj_set_pos(caja, 40, 60);
  lv_obj_set_size(caja, 400, 200);
  l = mg_etiqueta(caja, &magna_fuente_chica, LV_COLOR_MAKE(0x96, 0x96, 0x96), "Mensaje desde MagnAir", &st_cab);
  lv_obj_set_pos(l, 20, 14);
  l = mg_etiqueta(caja, &magna_fuente_grande, LV_COLOR_MAKE(0xEE, 0xEE, 0xEE), texto, &st_txt);
  lv_label_set_long_mode(l, LV_LABEL_LONG_BREAK);
  lv_label_set_align(l, LV_LABEL_ALIGN_CENTER);
  lv_obj_set_width(l, 360);
  lv_obj_set_pos(l, 20, 40);
  mg_boton(caja, 130, 140, 140, 44, "Entendido", mg_msg_cb);
}

/* --- bloqueo de la pantalla mientras imprime --- */
static lv_obj_t *mg_bloq, *mg_bloq_desliz;
static int mg_bloq_borrar;

static void mg_desliz_cb(lv_obj_t *o, lv_event_t e) {
  if (e == LV_EVENT_RELEASED || e == LV_EVENT_PRESS_LOST) {
    if (lv_slider_get_value(o) >= 90) { lv_obj_set_hidden(mg_bloq, true); mg_bloq_borrar = 1; }
    else lv_slider_set_value(o, 0, LV_ANIM_OFF);
  }
}

/* Candado de líneas (cuerpo y arco), en x, y (esquina de arriba a la izquierda), de 20 × 26 */
static void mg_candado(lv_obj_t *padre, lv_coord_t x, lv_coord_t y, lv_style_t *st) {
  static const lv_point_t cuerpo[5] = { { 0, 12 }, { 20, 12 }, { 20, 26 }, { 0, 26 }, { 0, 12 } };
  static const lv_point_t arco[6] = { { 4, 12 }, { 4, 6 }, { 7, 2 }, { 13, 2 }, { 16, 6 }, { 16, 12 } };
  lv_obj_t *l = lv_line_create(padre, (lv_obj_t *)NULL);
  lv_line_set_points(l, cuerpo, 5);
  lv_line_set_style(l, LV_LINE_STYLE_MAIN, st);
  lv_obj_set_pos(l, x, y);
  l = lv_line_create(padre, (lv_obj_t *)NULL);
  lv_line_set_points(l, arco, 6);
  lv_line_set_style(l, LV_LINE_STYLE_MAIN, st);
  lv_obj_set_pos(l, x, y);
}

void magna_bloquear(void) {
  static lv_style_t st_tapa, st_linea, st_txt, st_aviso, st_fondo, st_ind, st_perilla;
  lv_obj_t *l;
  if (mg_bloq) return;
  mg_bloq_borrar = 0;
  lv_style_copy(&st_tapa, &lv_style_plain);
  st_tapa.body.main_color = st_tapa.body.grad_color = LV_COLOR_BLACK;
  st_tapa.body.opa = LV_OPA_80;
  mg_bloq = mg_tapa(&st_tapa);
  lv_style_copy(&st_linea, &lv_style_plain);
  st_linea.line.color = LV_COLOR_MAKE(0xEE, 0xEE, 0xEE);
  st_linea.line.width = 4;
  st_linea.line.rounded = 1;
  mg_candado(mg_bloq, 228, 92, &st_linea);
  l = mg_etiqueta(mg_bloq, &magna_fuente_grande, LV_COLOR_MAKE(0xEE, 0xEE, 0xEE), "Pantalla bloqueada", &st_txt);
  lv_obj_set_pos(l, 240 - lv_obj_get_width(l) / 2, 140);
  lv_style_copy(&st_fondo, &lv_style_plain);
  st_fondo.body.main_color = st_fondo.body.grad_color = LV_COLOR_MAKE(0x22, 0x22, 0x22);
  st_fondo.body.radius = LV_RADIUS_CIRCLE;
  st_fondo.body.border.width = 2;
  st_fondo.body.border.color = LV_COLOR_MAKE(0x6E, 0x6E, 0x6E);
  st_fondo.body.border.opa = LV_OPA_COVER;
  st_fondo.body.padding.left = st_fondo.body.padding.right = st_fondo.body.padding.top = st_fondo.body.padding.bottom = 4;
  lv_style_copy(&st_ind, &st_fondo);
  st_ind.body.main_color = st_ind.body.grad_color = LV_COLOR_MAKE(0x5C, 0x0E, 0x14);
  st_ind.body.border.width = 0;
  lv_style_copy(&st_perilla, &st_ind);
  st_perilla.body.main_color = st_perilla.body.grad_color = LV_COLOR_MAKE(0xD6, 0x20, 0x27);
  mg_bloq_desliz = lv_slider_create(mg_bloq, (lv_obj_t *)NULL);
  lv_obj_set_pos(mg_bloq_desliz, 100, 200);
  lv_obj_set_size(mg_bloq_desliz, 280, 44);
  lv_slider_set_range(mg_bloq_desliz, 0, 100);
  lv_slider_set_value(mg_bloq_desliz, 0, LV_ANIM_OFF);
  lv_slider_set_style(mg_bloq_desliz, LV_SLIDER_STYLE_BG, &st_fondo);
  lv_slider_set_style(mg_bloq_desliz, LV_SLIDER_STYLE_INDIC, &st_ind);
  lv_slider_set_style(mg_bloq_desliz, LV_SLIDER_STYLE_KNOB, &st_perilla);
  lv_obj_set_event_cb(mg_bloq_desliz, mg_desliz_cb);
  l = mg_etiqueta(mg_bloq, &magna_fuente_chica, LV_COLOR_MAKE(0x96, 0x96, 0x96), "desliz\xC3\xA1 para desbloquear  >", &st_aviso);
  lv_obj_set_pos(l, 240 - lv_obj_get_width(l) / 2, 256);
}

int magna_bloqueada(void) { return mg_bloq != NULL; }
void magna_desbloquear(void) { if (mg_bloq) { lv_obj_set_hidden(mg_bloq, true); mg_bloq_borrar = 1; } }

/* Botón con candado en la pantalla de impresión (arriba, a la izquierda de la hora) */
static void mg_candado_cb(lv_obj_t *o, lv_event_t e) { (void)o; if (e == LV_EVENT_RELEASED) magna_bloquear(); }

void magna_candado_crear(lv_obj_t *scr) {
  static lv_style_t st_btn, st_linea;
  lv_obj_t *b;
  lv_style_copy(&st_btn, &lv_style_transp);
  lv_style_copy(&st_linea, &lv_style_plain);
  st_linea.line.color = LV_COLOR_MAKE(0xC8, 0xC8, 0xC8);
  st_linea.line.width = 2;
  b = lv_btn_create(scr, (lv_obj_t *)NULL);
  lv_btn_set_style(b, LV_BTN_STYLE_REL, &st_btn);
  lv_btn_set_style(b, LV_BTN_STYLE_PR, &st_btn);
  lv_btn_set_layout(b, LV_LAYOUT_OFF);
  lv_obj_set_pos(b, 380, 0);
  lv_obj_set_size(b, 50, 32);
  lv_obj_set_event_cb(b, mg_candado_cb);
  mg_candado(b, 15, 3, &st_linea);
}

/* --- "siempre encendida" mientras imprime: pantalla negra con el porcentaje enorme --- */
static lv_obj_t *mg_amb, *mg_amb_pct, *mg_amb_barra, *mg_amb_fin, *mg_amb_hora;
static int mg_ult_pct = -1;
static int32_t mg_ult_faltan = -1;

void magna_progreso_poner(int pct, int32_t faltan) { mg_ult_pct = pct; mg_ult_faltan = faltan; }

int magna_ambiente_visible(void) { return mg_amb != NULL; }

void magna_ambiente_cerrar(void) {
  if (!mg_amb) return;
  lv_obj_del(mg_amb);
  mg_amb = mg_amb_pct = mg_amb_barra = mg_amb_fin = mg_amb_hora = NULL;
}

void magna_ambiente_actualizar(uint32_t ahora_ms) {
  char t[64];
  int h, m, k = 0, n = (int)sizeof t;
  char *s = t;
  if (!mg_amb) return;
  mg_ult_pct = mg_ult_pct_info;
  mg_ult_faltan = mg_ult_faltan_info;
  if (magna_hora(ahora_ms, &h, &m, NULL)) snprintf(t, sizeof t, "%02d:%02d", h, m); else t[0] = 0;
  mg_poner_texto(mg_amb_hora, t);
  lv_obj_set_pos(mg_amb_hora, 240 - lv_obj_get_width(mg_amb_hora) / 2, 22);
  if (mg_ult_pct >= 0) snprintf(t, sizeof t, "%d%%", mg_ult_pct); else snprintf(t, sizeof t, "%s", "");
  mg_poner_texto(mg_amb_pct, t);
  lv_obj_set_pos(mg_amb_pct, 240 - lv_obj_get_width(mg_amb_pct) / 2, 70);
  lv_bar_set_value(mg_amb_barra, mg_ult_pct > 0 ? mg_ult_pct : 0, LV_ANIM_OFF);
  t[0] = 0;
  if (mg_ult_faltan >= 0) {
    if (magna_hora(ahora_ms, &h, &m, NULL)) {
      const long fin = ((long)h * 3600L + (long)m * 60L + (long)mg_ult_faltan) % 86400L;
      MG_AGREGAR("termina %02ld:%02ld " MG_PUNTO " ", fin / 3600L, (fin % 3600L) / 60L);
    }
    MG_AGREGAR("faltan %ld:%02ld", (long)(mg_ult_faltan / 3600), (long)((mg_ult_faltan % 3600) / 60));
  }
  mg_poner_texto(mg_amb_fin, t);
  lv_obj_set_pos(mg_amb_fin, 240 - lv_obj_get_width(mg_amb_fin) / 2, 216);
}

void magna_ambiente_mostrar(uint32_t ahora_ms) {
  static lv_style_t st_negro, st_hora, st_pct, st_fin, st_aviso, st_fondo, st_ind;
  lv_obj_t *l;
  if (mg_amb) return;
  lv_style_copy(&st_negro, &lv_style_plain);
  st_negro.body.main_color = st_negro.body.grad_color = LV_COLOR_BLACK;
  st_negro.body.opa = LV_OPA_COVER;
  mg_amb = mg_tapa(&st_negro);
  mg_amb_hora = mg_etiqueta(mg_amb, &magna_fuente_grande, LV_COLOR_MAKE(0x6E, 0x6E, 0x6E), "", &st_hora);
  mg_amb_pct = mg_etiqueta(mg_amb, &magna_fuente_enorme, LV_COLOR_MAKE(0x96, 0x1E, 0x22), "", &st_pct);
  lv_style_copy(&st_fondo, &lv_style_plain);
  st_fondo.body.main_color = st_fondo.body.grad_color = LV_COLOR_MAKE(0x1E, 0x1E, 0x1E);
  st_fondo.body.radius = LV_RADIUS_CIRCLE;
  st_fondo.body.padding.left = st_fondo.body.padding.right = st_fondo.body.padding.top = st_fondo.body.padding.bottom = 0;
  lv_style_copy(&st_ind, &st_fondo);
  st_ind.body.main_color = st_ind.body.grad_color = LV_COLOR_MAKE(0x6E, 0x16, 0x1A);
  mg_amb_barra = lv_bar_create(mg_amb, (lv_obj_t *)NULL);
  lv_bar_set_style(mg_amb_barra, LV_BAR_STYLE_BG, &st_fondo);
  lv_bar_set_style(mg_amb_barra, LV_BAR_STYLE_INDIC, &st_ind);
  lv_obj_set_pos(mg_amb_barra, 90, 184);
  lv_obj_set_size(mg_amb_barra, 300, 12);
  mg_amb_fin = mg_etiqueta(mg_amb, &magna_fuente_chica, LV_COLOR_MAKE(0x78, 0x78, 0x78), "", &st_fin);
  l = mg_etiqueta(mg_amb, &magna_fuente_chica, LV_COLOR_MAKE(0x46, 0x46, 0x46), "toc\xC3\xA1 la pantalla para volver", &st_aviso);
  lv_obj_set_pos(l, 240 - lv_obj_get_width(l) / 2, 288);
  magna_ambiente_actualizar(ahora_ms);
}

/* Borra (fuera de los eventos de LVGL) lo que se cerró con un toque. Una vez por segundo. */
void magna_capa_arriba_tick(uint32_t ahora_ms, int imprimiendo) {
  if (mg_msg_borrar && mg_msg) { lv_obj_del(mg_msg); mg_msg = NULL; mg_msg_borrar = 0; }
  if (mg_bloq_borrar && mg_bloq) { lv_obj_del(mg_bloq); mg_bloq = mg_bloq_desliz = NULL; mg_bloq_borrar = 0; }
  if (!imprimiendo) { magna_ambiente_cerrar(); magna_desbloquear(); }
  if (mg_amb) magna_ambiente_actualizar(ahora_ms);
}

/* =================================================================================================
 * Etapa 32: animaciones livianas de la pantalla de impresión (se pueden apagar desde MagnAir).
 *  - el ventilador gira (3 imágenes, cada 120 ms a 100 %, más lento si el ventilador va más lento),
 *  - un brillo recorre la parte llena de la barra,
 *  - la temperatura del hotend y de la cama cambia de color (azul frío -> rojo) y titila hasta llegar.
 * Una sola tarea de LVGL cada 120 ms; solo toca objetos chicos (redibuja unas decenas de píxeles).
 * ================================================================================================= */
static lv_obj_t *mg_an_vent, *mg_an_barra, *mg_an_brillo, *mg_an_ext, *mg_an_cama;
static uint8_t mg_an_vel;              /* velocidad del ventilador, 0..100 */
static int16_t mg_an_temp[2][2];       /* [hotend/cama][actual/objetivo] */
static uint8_t mg_an_activa = 1;       /* opción prendida, pantalla prendida y sin "siempre encendida" */
static lv_style_t mg_an_st_temp[2];
static const lv_style_t *mg_an_st_orig[2];
static const char *const MG_VENT[3] = { "F:/bmp_fan_state.bin", "F:/bmp_fan_state1.bin", "F:/bmp_fan_state2.bin" };

void magna_anim_registrar(lv_obj_t *ventilador, lv_obj_t *barra, lv_obj_t *temp_hotend, lv_obj_t *temp_cama) {
  static lv_style_t st_brillo;
  mg_an_vent = ventilador;
  mg_an_barra = barra;
  mg_an_ext = temp_hotend;
  mg_an_cama = temp_cama;
  mg_an_st_orig[0] = temp_hotend ? lv_obj_get_style(temp_hotend) : NULL;
  mg_an_st_orig[1] = temp_cama ? lv_obj_get_style(temp_cama) : NULL;
  mg_an_brillo = NULL;
  if (barra) {
    lv_style_copy(&st_brillo, &lv_style_plain);
    st_brillo.body.main_color = st_brillo.body.grad_color = LV_COLOR_MAKE(0xFF, 0xB0, 0xB0);
    st_brillo.body.opa = LV_OPA_40;
    st_brillo.body.radius = 4;
    mg_an_brillo = lv_obj_create(barra, (lv_obj_t *)NULL);
    lv_obj_set_style(mg_an_brillo, &st_brillo);
    lv_obj_set_click(mg_an_brillo, false);
    lv_obj_set_size(mg_an_brillo, 10, lv_obj_get_height(barra) - 12);
    lv_obj_set_pos(mg_an_brillo, 6, 6);
    lv_obj_set_hidden(mg_an_brillo, true);
  }
}

/* La pantalla de impresión se borra: olvidar sus objetos. */
void magna_anim_olvidar(void) { mg_an_vent = mg_an_barra = mg_an_brillo = mg_an_ext = mg_an_cama = NULL; }

/* Datos de Marlin, una vez por segundo */
void magna_anim_datos(int vel, int t_ext, int obj_ext, int t_cama, int obj_cama, int activa) {
  mg_an_vel = (uint8_t)(vel < 0 ? 0 : vel > 100 ? 100 : vel);
  mg_an_temp[0][0] = (int16_t)t_ext;  mg_an_temp[0][1] = (int16_t)obj_ext;
  mg_an_temp[1][0] = (int16_t)t_cama; mg_an_temp[1][1] = (int16_t)obj_cama;
  mg_an_activa = (uint8_t)(activa && magna_opcion(MAGNA_OP_ANIMACIONES));
}

/* Color del número de temperatura: azul (frío) -> blanco -> rojo (caliente), según cuánto falta. */
lv_color_t magna_color_temp(int actual, int objetivo) {
  int t;   /* 0..100 */
  if (objetivo <= 0) return LV_COLOR_MAKE(0xEE, 0xEE, 0xEE);
  t = (actual - 25) * 100 / (objetivo - 25 > 10 ? objetivo - 25 : 10);
  if (t < 0) t = 0;
  if (t > 100) t = 100;
  if (t < 50) return LV_COLOR_MAKE((uint8_t)(90 + 165 * t / 50), (uint8_t)(150 + 105 * t / 50), 255);
  return LV_COLOR_MAKE(255, (uint8_t)(255 - 180 * (t - 50) / 50), (uint8_t)(255 - 180 * (t - 50) / 50));
}

static void mg_an_tarea(lv_task_t *tarea) {
  static uint8_t cuadro, cuenta, brillo_x, parpadeo;
  int i;
  (void)tarea;
  if (!mg_an_activa) {
    /* apagadas: todo quieto como antes */
    if (mg_an_vent && cuadro) { lv_imgbtn_set_src(mg_an_vent, LV_BTN_STATE_REL, MG_VENT[0]); lv_imgbtn_set_src(mg_an_vent, LV_BTN_STATE_PR, MG_VENT[0]); cuadro = 0; }
    if (mg_an_brillo) mg_ocultar(mg_an_brillo, 1);
    for (i = 0; i < 2; i++) {
      lv_obj_t *l = i ? mg_an_cama : mg_an_ext;
      if (l && mg_an_st_orig[i] && lv_obj_get_style(l) != mg_an_st_orig[i]) lv_obj_set_style(l, mg_an_st_orig[i]);
    }
    return;
  }
  /* ventilador: a 100 % avanza un cuadro cada 120 ms; a 25 %, cada 4 */
  if (mg_an_vent && mg_an_vel > 0) {
    const uint8_t cada = (uint8_t)(mg_an_vel >= 90 ? 1 : mg_an_vel >= 60 ? 2 : mg_an_vel >= 30 ? 3 : 4);
    if (++cuenta >= cada) {
      cuenta = 0;
      cuadro = (uint8_t)((cuadro + 1) % 3);
      lv_imgbtn_set_src(mg_an_vent, LV_BTN_STATE_REL, MG_VENT[cuadro]);
      lv_imgbtn_set_src(mg_an_vent, LV_BTN_STATE_PR, MG_VENT[cuadro]);
    }
  }
  /* brillo: recorre la parte llena de la barra */
  if (mg_an_brillo && mg_an_barra) {
    const int lleno = (lv_obj_get_width(mg_an_barra) - 8) * (mg_ult_pct_info > 0 ? mg_ult_pct_info : 0) / 100;
    if (lleno < 30) mg_ocultar(mg_an_brillo, 1);
    else {
      brillo_x = (uint8_t)(brillo_x + 12);
      if (brillo_x + 16 > lleno) brillo_x = 0;
      lv_obj_set_x(mg_an_brillo, 6 + brillo_x);
      mg_ocultar(mg_an_brillo, 0);
    }
  }
  /* temperaturas: color según cuánto falta y titila (cada 480 ms) mientras calienta */
  parpadeo = (uint8_t)((parpadeo + 1) % 8);
  for (i = 0; i < 2; i++) {
    lv_obj_t *l = i ? mg_an_cama : mg_an_ext;
    const int actual = mg_an_temp[i][0], objetivo = mg_an_temp[i][1];
    const int calentando = objetivo > 0 && actual < objetivo - 3;
    lv_color_t color;
    lv_opa_t opa;
    if (!l || !mg_an_st_orig[i]) continue;
    color = magna_color_temp(actual, objetivo);
    opa = (lv_opa_t)((calentando && parpadeo >= 4) ? LV_OPA_50 : LV_OPA_COVER);
    if (lv_obj_get_style(l) != &mg_an_st_temp[i]) lv_style_copy(&mg_an_st_temp[i], mg_an_st_orig[i]);
    else if (mg_an_st_temp[i].text.color.full == color.full && mg_an_st_temp[i].text.opa == opa) continue;   /* sin cambios: no redibujar */
    mg_an_st_temp[i].text.color = color;
    mg_an_st_temp[i].text.opa = opa;
    lv_obj_set_style(l, &mg_an_st_temp[i]);
  }
}

void magna_anim_iniciar(void) {
  static lv_task_t *t;
  if (!t) t = lv_task_create(mg_an_tarea, 120, LV_TASK_PRIO_LOW, NULL);
}

/* =================================================================================================
 * Etapa 33: gráfico de temperaturas, nivelación en vivo con mapa, cancelar piezas y vista en vivo.
 * Las tres primeras son tapas (lv_layer_top) que se abren con botones chicos y se cierran con "Atrás";
 * se borran en el próximo magna_tick (nunca dentro de su propio evento).
 * ================================================================================================= */
static lv_obj_t **mg_cerrar[4];
static void mg_cerrar_luego(lv_obj_t **o) {
  int i;
  if (!o || !*o) return;
  lv_obj_set_hidden(*o, true);
  for (i = 0; i < 4; i++) if (!mg_cerrar[i] || mg_cerrar[i] == o) { mg_cerrar[i] = o; return; }
}
static void mg_cerrar_pendientes(void) {
  int i;
  for (i = 0; i < 4; i++) if (mg_cerrar[i]) { if (*mg_cerrar[i]) { lv_obj_del(*mg_cerrar[i]); *mg_cerrar[i] = NULL; } mg_cerrar[i] = NULL; }
}

/* Botón chico de íconos de líneas (sin fondo), para las pantallas de MKS */
static lv_obj_t *mg_boton_icono(lv_obj_t *padre, lv_coord_t x, lv_coord_t y, lv_coord_t w, lv_coord_t h, lv_event_cb_t cb) {
  static lv_style_t st;
  static int listo = 0;
  lv_obj_t *b;
  if (!listo) { lv_style_copy(&st, &lv_style_transp); listo = 1; }
  b = lv_btn_create(padre, (lv_obj_t *)NULL);
  lv_btn_set_style(b, LV_BTN_STYLE_REL, &st);
  lv_btn_set_style(b, LV_BTN_STYLE_PR, &st);
  lv_btn_set_layout(b, LV_LAYOUT_OFF);
  lv_obj_set_pos(b, x, y);
  lv_obj_set_size(b, w, h);
  lv_obj_set_event_cb(b, cb);
  return b;
}

static lv_style_t mg_st_trazo;
static void mg_trazo(lv_obj_t *padre, const lv_point_t *pts, uint16_t n, lv_coord_t x, lv_coord_t y) {
  lv_obj_t *l;
  if (!mg_st_trazo.line.width) {
    lv_style_copy(&mg_st_trazo, &lv_style_plain);
    mg_st_trazo.line.color = LV_COLOR_MAKE(0xC8, 0xC8, 0xC8);
    mg_st_trazo.line.width = 2;
    mg_st_trazo.line.rounded = 1;
  }
  l = lv_line_create(padre, (lv_obj_t *)NULL);
  lv_line_set_points(l, pts, n);
  lv_line_set_style(l, LV_LINE_STYLE_MAIN, &mg_st_trazo);
  lv_obj_set_pos(l, x, y);
  lv_obj_set_click(l, false);
}

/* Pantalla con título y "Atrás" (tapa negra con el degradé de la pantalla) */
static lv_obj_t *mg_pantalla_tapa(const char *titulo, lv_event_cb_t atras) {
  static lv_style_t st, st_tit;
  lv_obj_t *t, *l;
  lv_style_copy(&st, &lv_style_plain);
  st.body.main_color = LV_COLOR_MAKE(0x14, 0x14, 0x14);
  st.body.grad_color = LV_COLOR_MAKE(0x5C, 0x0E, 0x14);
  t = mg_tapa(&st);
  l = mg_etiqueta(t, &magna_fuente_chica, LV_COLOR_MAKE(0xEE, 0xEE, 0xEE), titulo, &st_tit);
  lv_obj_set_pos(l, 6, 10);
  mg_boton(t, 380, 272, 90, 40, "Atr\xC3\xA1s", atras);
  return t;
}

/* --- historial de temperaturas: una muestra cada 5 s, los últimos 10 minutos --- */
#define MG_MUESTRAS 120
static int16_t mg_hist[4][MG_MUESTRAS];   /* hotend, objetivo, cama, objetivo */
static uint8_t mg_hist_n, mg_hist_i;
static lv_obj_t *mg_graf, *mg_graf_chart, *mg_graf_leyenda[2];
static lv_chart_series_t *mg_graf_ser[4];

void magna_hist_agregar(int ext, int obj_ext, int cama, int obj_cama) {
  mg_hist[0][mg_hist_i] = (int16_t)ext; mg_hist[1][mg_hist_i] = (int16_t)obj_ext;
  mg_hist[2][mg_hist_i] = (int16_t)cama; mg_hist[3][mg_hist_i] = (int16_t)obj_cama;
  mg_hist_i = (uint8_t)((mg_hist_i + 1) % MG_MUESTRAS);
  if (mg_hist_n < MG_MUESTRAS) mg_hist_n++;
}

static void mg_graf_llenar(void) {
  int s, k;
  char t[40];
  if (!mg_graf) return;
  for (s = 0; s < 4; s++)
    for (k = 0; k < MG_MUESTRAS; k++) {
      /* de la más vieja a la más nueva; las que todavía no hay quedan sin dibujar */
      mg_graf_ser[s]->points[k] = (k < MG_MUESTRAS - mg_hist_n) ? LV_CHART_POINT_DEF : mg_hist[s][(mg_hist_i + k) % MG_MUESTRAS];
    }
  lv_chart_refresh(mg_graf_chart);
  if (mg_hist_n) {
    const int u = (mg_hist_i + MG_MUESTRAS - 1) % MG_MUESTRAS;
    snprintf(t, sizeof t, "Hotend %d / %d", mg_hist[0][u], mg_hist[1][u]); mg_poner_texto(mg_graf_leyenda[0], t);
    snprintf(t, sizeof t, "Cama %d / %d", mg_hist[2][u], mg_hist[3][u]); mg_poner_texto(mg_graf_leyenda[1], t);
  }
}

static void mg_graf_atras(lv_obj_t *o, lv_event_t e) { (void)o; if (e == LV_EVENT_RELEASED) mg_cerrar_luego(&mg_graf); }

void magna_grafico_abrir(void) {
  static lv_style_t st_bg, st_ley[2], st_eje;
  static const lv_color_t colores[4] = { LV_COLOR_MAKE(0xFF, 0x4D, 0x4D), LV_COLOR_MAKE(0x8A, 0x30, 0x30),
                                         LV_COLOR_MAKE(0xF0, 0x82, 0x28), LV_COLOR_MAKE(0x80, 0x50, 0x20) };
  lv_obj_t *l;
  int s;
  if (mg_graf) return;
  mg_graf = mg_pantalla_tapa("Temperaturas \xC2\xB7 \xC3\xBAltimos 10 minutos", mg_graf_atras);
  lv_style_copy(&st_bg, &lv_style_plain);
  st_bg.body.main_color = st_bg.body.grad_color = LV_COLOR_MAKE(0x12, 0x12, 0x12);
  st_bg.body.border.width = 1;
  st_bg.body.border.color = LV_COLOR_MAKE(0x46, 0x46, 0x46);
  st_bg.line.color = LV_COLOR_MAKE(0x30, 0x30, 0x30);
  st_bg.line.width = 1;
  st_bg.text.color = LV_COLOR_MAKE(0x96, 0x96, 0x96);
  st_bg.text.font = &magna_fuente_chica;
  st_bg.body.padding.left = st_bg.body.padding.right = st_bg.body.padding.top = st_bg.body.padding.bottom = 0;
  mg_graf_chart = lv_chart_create(mg_graf, (lv_obj_t *)NULL);
  lv_chart_set_style(mg_graf_chart, LV_CHART_STYLE_MAIN, &st_bg);
  lv_obj_set_pos(mg_graf_chart, 44, 40);
  lv_obj_set_size(mg_graf_chart, 426, 200);
  lv_chart_set_type(mg_graf_chart, LV_CHART_TYPE_LINE);
  lv_chart_set_range(mg_graf_chart, 0, 250);
  lv_chart_set_point_count(mg_graf_chart, MG_MUESTRAS);
  lv_chart_set_div_line_count(mg_graf_chart, 4, 0);
  lv_chart_set_series_width(mg_graf_chart, 2);
  lv_chart_set_update_mode(mg_graf_chart, LV_CHART_UPDATE_MODE_SHIFT);
  for (s = 0; s < 4; s++) mg_graf_ser[s] = lv_chart_add_series(mg_graf_chart, colores[s]);
  lv_style_copy(&st_eje, &lv_style_plain);
  for (s = 0; s <= 5; s++) {
    char t[6];
    snprintf(t, sizeof t, "%d", 250 - s * 50);
    l = mg_etiqueta(mg_graf, &magna_fuente_chica, LV_COLOR_MAKE(0x96, 0x96, 0x96), "", &st_eje);
    lv_label_set_text(l, t);
    lv_obj_set_pos(l, 38 - lv_obj_get_width(l), 40 + s * 40 - 8);
  }
  for (s = 0; s < 2; s++) {
    mg_graf_leyenda[s] = mg_etiqueta(mg_graf, &magna_fuente_chica, colores[s * 2], "", &st_ley[s]);
    lv_obj_set_pos(mg_graf_leyenda[s], 50 + s * 170, 250);
  }
  mg_graf_llenar();
}

/* --- nivelación en vivo y mapa (versión con BLTouch) --- */
#define MG_NIVEL_MAX 7
static lv_obj_t *mg_niv, *mg_niv_celda[MG_NIVEL_MAX][MG_NIVEL_MAX], *mg_niv_valor[MG_NIVEL_MAX][MG_NIVEL_MAX], *mg_niv_info[3];
static uint8_t mg_niv_nx, mg_niv_ny;
static lv_style_t mg_niv_st[4];   /* 0 sin medir, 1 verde, 2 amarillo, 3 rojo */

static void mg_niv_atras(lv_obj_t *o, lv_event_t e) { (void)o; if (e == LV_EVENT_RELEASED) mg_cerrar_luego(&mg_niv); }

void magna_nivel_abrir(int nx, int ny) {
  static lv_style_t st_v, st_i[3];
  static const lv_color_t c[4] = { LV_COLOR_MAKE(0x1C, 0x1C, 0x1C), LV_COLOR_MAKE(0x28, 0x8C, 0x46), LV_COLOR_MAKE(0xBE, 0xA0, 0x1E), LV_COLOR_MAKE(0xBE, 0x28, 0x28) };
  int x, y, i;
  lv_coord_t lado;
  if (mg_niv) { lv_obj_del(mg_niv); mg_niv = NULL; }
  if (nx > MG_NIVEL_MAX) nx = MG_NIVEL_MAX;
  if (ny > MG_NIVEL_MAX) ny = MG_NIVEL_MAX;
  if (nx < 1 || ny < 1) return;
  mg_niv_nx = (uint8_t)nx; mg_niv_ny = (uint8_t)ny;
  mg_niv = mg_pantalla_tapa("Nivelaci\xC3\xB3n de la cama (BLTouch)", mg_niv_atras);
  for (i = 0; i < 4; i++) {
    lv_style_copy(&mg_niv_st[i], &lv_style_plain);
    mg_niv_st[i].body.main_color = mg_niv_st[i].body.grad_color = c[i];
    mg_niv_st[i].body.border.width = i ? 0 : 1;
    mg_niv_st[i].body.border.color = LV_COLOR_MAKE(0x50, 0x50, 0x50);
  }
  lado = (lv_coord_t)(220 / (nx > ny ? nx : ny));
  lv_style_copy(&st_v, &lv_style_plain);
  st_v.text.color = LV_COLOR_WHITE;
  st_v.text.font = &magna_fuente_chica;
  for (y = 0; y < ny; y++)
    for (x = 0; x < nx; x++) {
      /* fila 0 arriba = atrás de la cama */
      lv_obj_t *o = lv_obj_create(mg_niv, (lv_obj_t *)NULL);
      lv_obj_set_style(o, &mg_niv_st[0]);
      lv_obj_set_click(o, false);
      lv_obj_set_pos(o, (lv_coord_t)(20 + x * lado), (lv_coord_t)(40 + y * lado));
      lv_obj_set_size(o, lado - 3, lado - 3);
      mg_niv_celda[x][ny - 1 - y] = o;
      mg_niv_valor[x][ny - 1 - y] = lv_label_create(o, (lv_obj_t *)NULL);
      lv_obj_set_style(mg_niv_valor[x][ny - 1 - y], &st_v);
      lv_label_set_text(mg_niv_valor[x][ny - 1 - y], "");
    }
  for (i = 0; i < 3; i++) {
    mg_niv_info[i] = mg_etiqueta(mg_niv, i == 1 ? &magna_fuente_grande : &magna_fuente_chica,
                                 i == 1 ? LV_COLOR_MAKE(0xEE, 0xEE, 0xEE) : LV_COLOR_MAKE(0x96, 0x96, 0x96), "", &st_i[i]);
    lv_obj_set_pos(mg_niv_info[i], 262, (lv_coord_t)(i == 0 ? 50 : i == 1 ? 72 : 112));
  }
}

/* valores en mm (milésimas en enteros para no depender de float en LVGL); NIVEL_SIN = sin medir */
#define MAGNA_NIVEL_SIN (-32768)
void magna_nivel_actualizar(const int16_t *milesimas /* [x * ny + y] */) {
  int x, y, medidos = 0, total;
  int16_t min = 32767, max = -32767;
  char t[48];
  if (!mg_niv) return;
  total = mg_niv_nx * mg_niv_ny;
  for (x = 0; x < mg_niv_nx; x++)
    for (y = 0; y < mg_niv_ny; y++) {
      const int16_t v = milesimas[x * mg_niv_ny + y];
      const int a = v < 0 ? -v : v;
      if (v == MAGNA_NIVEL_SIN) {   /* sin medir (o G29 recién empezó y borró la malla vieja) */
        if (lv_obj_get_style(mg_niv_celda[x][y]) != &mg_niv_st[0]) lv_obj_set_style(mg_niv_celda[x][y], &mg_niv_st[0]);
        mg_poner_texto(mg_niv_valor[x][y], "");
        continue;
      }
      medidos++;
      if (v < min) min = v;
      if (v > max) max = v;
      lv_obj_set_style(mg_niv_celda[x][y], &mg_niv_st[a <= 50 ? 1 : a <= 100 ? 2 : 3]);
      snprintf(t, sizeof t, "%c%d,%02d", v < 0 ? '-' : '+', a / 1000, (a % 1000) / 10);
      mg_poner_texto(mg_niv_valor[x][y], t);
      lv_obj_align(mg_niv_valor[x][y], NULL, LV_ALIGN_CENTER, 0, 0);
    }
  if (medidos < total) {
    snprintf(t, sizeof t, "Midiendo: punto %d de %d", medidos + 1 > total ? total : medidos + 1, total);
    mg_poner_texto(mg_niv_info[0], t);
    mg_poner_texto(mg_niv_info[1], "");
    mg_poner_texto(mg_niv_info[2], "");
  }
  else {
    const int d = max - min;
    mg_poner_texto(mg_niv_info[0], "Diferencia m\xC3\xA1xima");
    snprintf(t, sizeof t, "%d,%02d mm", d / 1000, (d % 1000) / 10);
    mg_poner_texto(mg_niv_info[1], t);
    mg_poner_texto(mg_niv_info[2], d <= 100 ? "Bien: la malla lo compensa" : d <= 300 ? "Se puede mejorar ajustando tornillos" : "Muy torcida: ajust\xC3\xA1 los tornillos");
  }
}

int magna_nivel_abierto(void) { return mg_niv != NULL; }

/* --- piezas (para cancelar una sin parar las demás) --- */
#define MG_PIEZAS 12
static char mg_pieza_nombre[MG_PIEZAS][22];
static uint8_t mg_piezas;
static lv_obj_t *mg_pz, *mg_pz_btn[6];
static void (*mg_pz_cancelar)(int);   /* lo pone la unión con Marlin */
static int (*mg_pz_cancelada)(int);

/* Índice de la pieza con ese nombre (la agrega si es nueva); -1 = no es una pieza ("NONMESH") */
int magna_pieza_indice(const char *nombre) {
  int i;
  if (!nombre || !nombre[0] || !strncmp(nombre, "NONMESH", 7)) return -1;
  for (i = 0; i < mg_piezas; i++) if (!strncmp(mg_pieza_nombre[i], nombre, sizeof mg_pieza_nombre[0] - 1)) return i;
  if (mg_piezas >= MG_PIEZAS) return -1;
  snprintf(mg_pieza_nombre[mg_piezas], sizeof mg_pieza_nombre[0], "%s", nombre);
  return mg_piezas++;
}
int magna_piezas_cantidad(void) { return mg_piezas; }
void magna_piezas_reiniciar(void) { mg_piezas = 0; }
void magna_piezas_funciones(void (*cancelar)(int), int (*cancelada)(int)) { mg_pz_cancelar = cancelar; mg_pz_cancelada = cancelada; }

static void mg_pz_atras(lv_obj_t *o, lv_event_t e) { (void)o; if (e == LV_EVENT_RELEASED) mg_cerrar_luego(&mg_pz); }
static void mg_pz_boton(lv_obj_t *o, lv_event_t e) {
  int i;
  if (e != LV_EVENT_RELEASED || !mg_pz_cancelar) return;
  for (i = 0; i < 6; i++)
    if (mg_pz_btn[i] == o) {
      mg_pz_cancelar(i);
      lv_obj_set_hidden(o, true);
    }
}

void magna_piezas_abrir(void) {
  static lv_style_t st_n[MG_PIEZAS], st_aviso;
  int i;
  if (mg_pz) return;
  for (i = 0; i < 6; i++) mg_pz_btn[i] = NULL;
  mg_pz = mg_pantalla_tapa("Cancelar una pieza (las dem\xC3\xA1s siguen)", mg_pz_atras);
  if (mg_piezas < 2) {
    lv_obj_t *l = mg_etiqueta(mg_pz, &magna_fuente_chica, LV_COLOR_MAKE(0xC8, 0xC8, 0xC8),
      mg_piezas ? "Este gcode tiene una sola pieza." : "Este gcode no tiene piezas marcadas.\nEn Cura hay que agregar un script (ver CURA-PANTALLA.md).", &st_aviso);
    lv_obj_set_pos(l, 20, 60);
    return;
  }
  for (i = 0; i < mg_piezas && i < 6; i++) {
    const int cancelada = mg_pz_cancelada ? mg_pz_cancelada(i) : 0;
    char t[32];
    lv_obj_t *l;
    snprintf(t, sizeof t, "%d  %s", i + 1, mg_pieza_nombre[i]);
    l = mg_etiqueta(mg_pz, &magna_fuente_chica, cancelada ? LV_COLOR_MAKE(0x78, 0x78, 0x78) : LV_COLOR_MAKE(0xEE, 0xEE, 0xEE), t, &st_n[i]);
    lv_obj_set_pos(l, 20, (lv_coord_t)(48 + i * 36));
    if (!cancelada) {
      mg_pz_btn[i] = mg_boton(mg_pz, 330, (lv_coord_t)(40 + i * 36), 130, 32, "Cancelar", mg_pz_boton);
    }
  }
}

/* --- vista en vivo: el recorrido de la boquilla en la capa actual (1 bit por punto, 5 kB) --- */
#define MG_VV 200
static uint8_t mg_vv_buf[(MG_VV / 8) * MG_VV + 8];   /* + paleta de 2 colores (LV_IMG_CF_INDEXED_1BIT) */
static lv_obj_t *mg_vv_canvas;
static uint8_t mg_vv_sucio, mg_vv_activa;
static float mg_vv_capa_z = -1;
static float mg_vv_escala = 200.0f / 230.0f;

void magna_vista_cama(float ancho, float fondo) { mg_vv_escala = (float)(MG_VV - 1) / (ancho > fondo ? ancho : fondo); }

static void mg_vv_punto(int x, int y) {
  if (x < 0 || y < 0 || x >= MG_VV || y >= MG_VV) return;
  mg_vv_buf[8 + y * (MG_VV / 8) + x / 8] |= (uint8_t)(0x80 >> (x & 7));
}

/* Un movimiento con extrusión (G1). Una capa nueva (Z más alta que la anterior que extruyó) borra. */
void magna_vista_linea(float x0, float y0, float x1, float y1, float z) {
  int ax, ay, bx, by, dx, dy, sx, sy, err, n = 0;
  if (z > mg_vv_capa_z + 0.01f) {
    memset(mg_vv_buf + 8, 0, sizeof mg_vv_buf - 8);
    mg_vv_capa_z = z;
  }
  ax = (int)(x0 * mg_vv_escala); ay = MG_VV - 1 - (int)(y0 * mg_vv_escala);
  bx = (int)(x1 * mg_vv_escala); by = MG_VV - 1 - (int)(y1 * mg_vv_escala);
  dx = bx > ax ? bx - ax : ax - bx; dy = -(by > ay ? by - ay : ay - by);
  sx = ax < bx ? 1 : -1; sy = ay < by ? 1 : -1; err = dx + dy;
  for (;;) {
    int e2;
    mg_vv_punto(ax, ay);
    if ((ax == bx && ay == by) || ++n > 600) break;
    e2 = 2 * err;
    if (e2 >= dy) { err += dy; ax += sx; }
    if (e2 <= dx) { err += dx; ay += sy; }
  }
  mg_vv_sucio = 1;
}

void magna_vista_reiniciar(void) { memset(mg_vv_buf + 8, 0, sizeof mg_vv_buf - 8); mg_vv_capa_z = -1; mg_vv_sucio = 1; }

static void (*mg_vv_redibujar_previa)(void);
static void mg_vv_tocar(lv_obj_t *o, lv_event_t e) {
  (void)o;
  if (e != LV_EVENT_RELEASED || !mg_vv_canvas) return;
  mg_vv_activa = !mg_vv_activa;
  lv_obj_set_hidden(mg_vv_canvas, !mg_vv_activa);
  if (!mg_vv_activa && mg_vv_redibujar_previa) mg_vv_redibujar_previa();   /* vuelve la miniatura o el tornillo */
}

/* En la pantalla de impresión: tocar la vista previa cambia entre la miniatura y la vista en vivo */
void magna_vista_crear(lv_obj_t *scr, void (*redibujar_previa)(void)) {
  lv_obj_t *b;
  mg_vv_redibujar_previa = redibujar_previa;
  mg_vv_canvas = lv_canvas_create(scr, (lv_obj_t *)NULL);
  lv_canvas_set_buffer(mg_vv_canvas, mg_vv_buf, MG_VV, MG_VV, LV_IMG_CF_INDEXED_1BIT);
  lv_canvas_set_palette(mg_vv_canvas, 0, LV_COLOR_MAKE(0x0C, 0x0C, 0x0C));
  lv_canvas_set_palette(mg_vv_canvas, 1, LV_COLOR_MAKE(0xFF, 0xFF, 0xFF));
  lv_obj_set_pos(mg_vv_canvas, 2, 36);
  lv_obj_set_click(mg_vv_canvas, false);
  lv_obj_set_hidden(mg_vv_canvas, !mg_vv_activa);
  b = mg_boton_icono(scr, 2, 36, MG_VV, MG_VV, mg_vv_tocar);
  (void)b;
}

void magna_vista_olvidar(void) { mg_vv_canvas = NULL; }

/* una vez por segundo */
static void mg_vv_tick(void) {
  if (mg_vv_canvas && mg_vv_activa && mg_vv_sucio) { lv_obj_invalidate(mg_vv_canvas); mg_vv_sucio = 0; }
}

/* --- botones chicos de la pantalla de impresión (arriba, a la izquierda del candado) --- */
static void mg_b_graf(lv_obj_t *o, lv_event_t e) { (void)o; if (e == LV_EVENT_RELEASED) magna_grafico_abrir(); }
static void mg_b_pz(lv_obj_t *o, lv_event_t e) { (void)o; if (e == LV_EVENT_RELEASED) magna_piezas_abrir(); }

void magna_botones_impresion(lv_obj_t *scr) {
  static const lv_point_t graf[4] = { { 0, 18 }, { 8, 8 }, { 15, 13 }, { 24, 2 } };
  static const lv_point_t ejes[3] = { { 0, 0 }, { 0, 22 }, { 26, 22 } };
  static const lv_point_t c1[5] = { { 0, 0 }, { 9, 0 }, { 9, 9 }, { 0, 9 }, { 0, 0 } };
  lv_obj_t *b = mg_boton_icono(scr, 330, 0, 48, 32, mg_b_graf);
  mg_trazo(b, ejes, 3, 11, 4);
  mg_trazo(b, graf, 4, 13, 4);
  b = mg_boton_icono(scr, 280, 0, 48, 32, mg_b_pz);
  mg_trazo(b, c1, 5, 11, 5);   /* dos cuadraditos = piezas */
  mg_trazo(b, c1, 5, 25, 15);
}

/* Botón del gráfico en la pantalla principal (abajo a la derecha) */
void magna_boton_grafico_principal(lv_obj_t *scr) {
  static const lv_point_t graf[4] = { { 0, 18 }, { 8, 8 }, { 15, 13 }, { 24, 2 } };
  static const lv_point_t ejes[3] = { { 0, 0 }, { 0, 22 }, { 26, 22 } };
  lv_obj_t *b = mg_boton_icono(scr, 404, 262, 60, 44, mg_b_graf);
  mg_trazo(b, ejes, 3, 16, 10);
  mg_trazo(b, graf, 4, 18, 10);
}

/* una vez por segundo desde magna_tick */
void magna_extras33_tick(void) {
  mg_cerrar_pendientes();
  if (mg_graf) mg_graf_llenar();
  mg_vv_tick();
}
