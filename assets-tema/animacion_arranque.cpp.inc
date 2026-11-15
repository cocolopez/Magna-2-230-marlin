// ---- etapa 32: arranque animado (el tornillo del logo se imprime capa por capa) -------------------
// bmp_logo.bin es el logo con el tornillo sin imprimir; las filas del tornillo terminado están en
// bmp_tornillo1..3.bin (RGB565 sin encabezado, DE ABAJO HACIA ARRIBA; las genera generar_assets.py
// junto con las constantes de animacion_arranque.inc). Como todos los íconos, quedan comprimidas en la
// memoria de la pantalla y se leen de corrido con SPIFlash (por eso van de abajo hacia arriba, el mismo
// orden en que sube la animación). Se copian directo a la pantalla (como lcdDrawLogo) y se dibuja la
// boquilla encima. Si faltan las imágenes (assets viejos), el logo queda quieto.
// La simulación de esto mismo en la compu es assets-tema/simular_arranque.py.
#include "animacion_arranque.inc"

static uint32_t magna_dir_imagen(const char *nombre) {   // como lv_get_pic_addr sin tabla hash
  uint8_t cantidad = 0;
  uint32_t leido = 0;
  char n[PIC_NAME_MAX_LEN];
  W25QXX.SPI_FLASH_BufferRead(&cantidad, PIC_COUNTER_ADDR, 1);
  if (cantidad == 0xFF) return 0;
  for (uint8_t i = 0; i < cantidad; i++) {
    uint8_t j = 0;
    for (;;) {
      char c = 0;
      W25QXX.SPI_FLASH_BufferRead((uint8_t *)&c, PIC_NAME_ADDR + leido, 1);
      leido++;
      if (j < sizeof(n) - 1) n[j++] = c;
      if (!c) break;
    }
    n[j < sizeof(n) ? j : sizeof(n) - 1] = 0;
    if (!strcasecmp(n, nombre)) return PIC_DATA_ADDR_TFT35 + uint32_t(i) * PER_PIC_MAX_SPACE_TFT35;
  }
  return 0;
}

static void magna_rect(const int16_t x, const int16_t y, const int16_t w, const int16_t h, const uint16_t color) {
  if (w <= 0 || h <= 0 || x < 0 || y < 0) return;
  SPI_TFT.setWindow(x, y, w, h);
  SPI_TFT.tftio.writeMultiple(color, uint32_t(w) * h);
}

static void magna_fila_pantalla(const int16_t r, const uint16_t ancho) {
  SPI_TFT.setWindow(MAGNA_ANIM_X0, r, ancho, 1);
  SPI_TFT.tftio.writeSequence((uint16_t *)bmp_public_buf, ancho);
}

void magna_arranque_animado() {
  #if HAS_LOGO_IN_FLASH
    uint32_t dir[MAGNA_ANIM_TIRAS];
    for (uint8_t i = 0; i < MAGNA_ANIM_TIRAS; i++) {
      char nombre[24];
      snprintf(nombre, sizeof(nombre), "bmp_tornillo%d.bin", i + 1);
      dir[i] = magna_dir_imagen(nombre);
      if (!dir[i]) return;
    }
    constexpr int16_t ANCHO = MAGNA_ANIM_X1 - MAGNA_ANIM_X0, PASOS = 16;
    constexpr uint16_t GRIS  = ((60 >> 3) << 11) | ((60 >> 2) << 5) | (60 >> 3),
                       ROJO  = ((214 >> 3) << 11) | ((32 >> 2) << 5) | (39 >> 3),
                       PUNTA = ((200 >> 3) << 11) | ((200 >> 2) << 5) | (200 >> 3);
    uint8_t tira = 0;
    uint16_t filas_leidas = 0;                    // de la tira actual
    SPIFlash.beginRead(dir[0]);
    int16_t corte_antes = MAGNA_ANIM_ABAJO;       // filas >= corte: impresas
    for (int16_t k = 1; k <= PASOS; k++) {
      const int16_t corte = MAGNA_ANIM_ABAJO - int16_t(int32_t(MAGNA_ANIM_ABAJO - MAGNA_ANIM_ARRIBA) * k / PASOS);
      // 1) lo nuevo impreso, de abajo hacia arriba (el orden de las tiras)
      for (int16_t r = corte_antes - 1; r >= corte; r--) {
        if (filas_leidas == MAGNA_ANIM_POR_TIRA && tira + 1 < MAGNA_ANIM_TIRAS) { SPIFlash.beginRead(dir[++tira]); filas_leidas = 0; }
        SPIFlash.readData((uint8_t *)bmp_public_buf, ANCHO * 2);
        filas_leidas++;
        magna_fila_pantalla(r, ANCHO);
      }
      // 2) donde estaba la boquilla, arriba del corte: el logo sin imprimir
      for (int16_t r = _MAX(int16_t(MAGNA_ANIM_Y0), int16_t(corte - 36)); r < corte; r++) {
        W25QXX.SPI_FLASH_BufferRead((uint8_t *)bmp_public_buf, PIC_LOGO_ADDR + (uint32_t(r) * TFT_WIDTH + MAGNA_ANIM_X0) * 2, ANCHO * 2);
        magna_fila_pantalla(r, ANCHO);
      }
      // 3) la boquilla (igual que la del logo): franja roja, cuerpo gris y punta clara
      if (k < PASOS) {
        const int16_t ny = corte - 3, nx = MAGNA_ANIM_CENTRO;
        if (ny - 32 >= 0) {
          magna_rect(nx - 17, ny - 32, 35, 3, ROJO);
          magna_rect(nx - 17, ny - 29, 35, 17, GRIS);
          for (int16_t y = ny - 12; y < ny; y++) {
            const int16_t medio = 9 - (y - (ny - 12)) / 2;   // de 9 a 4 px de cada lado
            magna_rect(nx - medio, y, medio * 2 + 1, 1, PUNTA);
          }
        }
      }
      corte_antes = corte;
      hal.watchdog_refresh();
      delay(80);
    }
  #endif
}
