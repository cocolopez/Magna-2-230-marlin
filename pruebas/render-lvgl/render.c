/* Prueba de render: dibuja pantallas con la librería LVGL 6.1.2 de MKS (la misma de la pantalla,
   con su lv_conf.h), usando los íconos del tema leídos desde archivo ("F:/bmp_xxx.bin") y el MISMO
   código que se pega en el firmware (decoracion_menus.inc, estilo_dialogos.inc, fuente_grande.inc).
   Guarda el framebuffer 480x320 RGB565.

   Uso: render <carpeta_assets> <salida.raw> [pantalla]
     pantalla: principal (por defecto) | menu | mas | carga | calentando | imprimiendo

   La letra normal de la pantalla (16 px, guardada en su memoria SPI) se simula con Roboto 16
   (fuente_normal.inc, la genera verificar_render.py en /tmp). */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "lvgl.h"
#include "decoracion_menus.inc"   /* assets-tema/: el mismo código que se pega en draw_ui.cpp */
#include "estilo_dialogos.inc"
#include "fuente_grande.inc"
#include "creditos.inc"
#include "fuente_normal.inc"      /* /tmp: Roboto 16, solo para la prueba */

static const char *DIR_ASSETS;
static uint16_t fb[480*320];
static void flush(lv_disp_drv_t *d, const lv_area_t *a, lv_color_t *c){
  for(int y=a->y1;y<=a->y2;y++) for(int x=a->x1;x<=a->x2;x++){ fb[y*480+x]=c->full; c++; }
  lv_disp_flush_ready(d);
}
typedef struct { FILE *f; long base; } mf_t;
static lv_fs_res_t f_open(lv_fs_drv_t *drv, void *fp, const char *path, lv_fs_mode_t m){
  char p[512]; snprintf(p,sizeof p,"%s/%s",DIR_ASSETS,path[0]=='/'?path+1:path);
  FILE *f=fopen(p,"rb"); if(!f) return LV_FS_RES_NOT_EX; ((mf_t*)fp)->f=f; return LV_FS_RES_OK; }
static lv_fs_res_t f_close(lv_fs_drv_t *drv, void *fp){ fclose(((mf_t*)fp)->f); return LV_FS_RES_OK; }
static lv_fs_res_t f_read(lv_fs_drv_t *drv, void *fp, void *buf, uint32_t btr, uint32_t *br){
  *br=fread(buf,1,btr,((mf_t*)fp)->f); if(*br<btr) memset((char*)buf+*br,0,btr-*br); *br=btr; return LV_FS_RES_OK; }
static lv_fs_res_t f_seek(lv_fs_drv_t *drv, void *fp, uint32_t pos){
  fseek(((mf_t*)fp)->f,pos,SEEK_SET);
  return LV_FS_RES_OK; }
static lv_fs_res_t f_tell(lv_fs_drv_t *drv, void *fp, uint32_t *p){ *p=ftell(((mf_t*)fp)->f); return LV_FS_RES_OK; }

static lv_style_t lbl;   /* como tft_style_label_rel: texto blanco con la letra normal */

static lv_obj_t *etiqueta(lv_obj_t *par, const char *t){
  lv_obj_t *l=lv_label_create(par,(lv_obj_t*)NULL); lv_label_set_text(l,t); lv_obj_set_style(l,&lbl); return l; }

/* botón de ícono como lv_big_button_create de MKS: imagen 117x140 y texto abajo */
static void boton(lv_obj_t *s, const char *img, const char *txt, int col, int fila){
  lv_obj_t *b=lv_imgbtn_create(s,NULL); lv_imgbtn_set_src(b,LV_BTN_STATE_REL,img); lv_imgbtn_set_src(b,LV_BTN_STATE_PR,img);
  lv_obj_set_pos(b,2+col*119,36+fila*142); lv_btn_set_layout(b,LV_LAYOUT_OFF);  /* como lv_imgbtn_create de MKS */
  if(txt){ lv_obj_t *l=etiqueta(b,txt); lv_obj_align(l,b,LV_ALIGN_IN_BOTTOM_MID,0,-20); }  /* BUTTON_TEXT_Y_OFFSET */
}

/* botón de diálogo como lv_button_btn_create de MKS (100x50) */
static void boton_dialogo(lv_obj_t *s, int x, int y, const char *txt){
  static lv_style_t rel; lv_style_copy(&rel,&lv_style_plain);
  rel.body.main_color=rel.body.grad_color=LV_COLOR_MAKE(0x7A,0x12,0x16); rel.body.radius=3; rel.text.color=LV_COLOR_WHITE; rel.text.font=&magna_fuente_normal;
  lv_obj_t *b=lv_btn_create(s,NULL); lv_obj_set_pos(b,x,y); lv_obj_set_size(b,100,50);
  lv_btn_set_style(b,LV_BTN_STYLE_REL,&rel); lv_btn_set_style(b,LV_BTN_STYLE_PR,&rel);
  lv_obj_t *l=lv_label_create(b,(lv_obj_t*)NULL); lv_label_set_text(l,txt);
}

int main(int argc,char**argv){
  const char *modo = argc>3 ? argv[3] : "principal";
  DIR_ASSETS=argv[1];
  lv_init();
  static lv_disp_buf_t db; static lv_color_t buf[480*17];
  lv_disp_buf_init(&db,buf,NULL,480*17);
  lv_disp_drv_t dd; lv_disp_drv_init(&dd); dd.flush_cb=flush; dd.buffer=&db; lv_disp_drv_register(&dd);
  lv_fs_drv_t fd; memset(&fd,0,sizeof fd); lv_fs_drv_init(&fd); fd.file_size=sizeof(mf_t); fd.letter='F';
  fd.open_cb=f_open; fd.close_cb=f_close; fd.read_cb=f_read; fd.seek_cb=f_seek; fd.tell_cb=f_tell; lv_fs_drv_register(&fd);
  static lv_style_t scr; lv_style_copy(&scr,&lv_style_scr);
  scr.body.main_color=LV_COLOR_MAKE(0x14,0x14,0x14); scr.body.grad_color=LV_COLOR_MAKE(0x5C, 0x0E, 0x14);
  scr.text.color=LV_COLOR_WHITE; scr.text.font=&magna_fuente_normal;
  lv_obj_t *s=lv_obj_create(NULL,NULL); lv_obj_set_style(s,&scr); lv_scr_load(s);
  lv_style_copy(&lbl,&lv_style_plain); lbl.text.color=LV_COLOR_WHITE; lbl.text.font=&magna_fuente_normal;

  if(!strcmp(modo,"menu") || !strcmp(modo,"mas")){
    const int mas = !strcmp(modo,"mas");
    magna_decorar_menu(s,true,false);
    lv_obj_t *tit=etiqueta(s, mas ? "Inicio>Ajustes>Mas" : "Ready>Settings"); lv_obj_set_pos(tit,3,5);
    /* como hace draw_move_motor.cpp: toma el primer hijo de la pantalla como título y lo achica.
       Tiene que ser el título de verdad (la decoración no puede crear objetos). */
    if(lv_obj_get_child_back(s,NULL)!=tit){ fprintf(stderr,"el primer hijo de la pantalla no es el titulo\n"); return 3; }
    lv_obj_set_width(lv_obj_get_child_back(s,NULL),480-101);
    magna_marca_titulo(s,tit,&lbl);
    if(mas){
      /* misma grilla que draw_more.cpp: Gcode, custom1-3 / custom4-6, Atrás */
      const char *im[]={"F:/bmp_custom1.bin","F:/bmp_custom2.bin","F:/bmp_custom3.bin","F:/bmp_custom4.bin","F:/bmp_custom5.bin","F:/bmp_custom6.bin"};
      const char *tx[]={"Calib. hotend","Calib. cama","Estacionar 1","Estacionar 2","Cargar 1","Cargar 2"};
      boton(s,"F:/bmp_machine_para.bin","Gcode",0,0);
      for(int i=0;i<6;i++) boton(s,im[i],tx[i],(i+1)%4,(i+1)/4);
      boton(s,"F:/bmp_return.bin","Atras",3,1);
    } else {
      const char *m[]={"F:/bmp_preHeat.bin","F:/bmp_extruct.bin","F:/bmp_mov.bin","F:/bmp_zero.bin",
                       "F:/bmp_leveling.bin","F:/bmp_filamentchange.bin","F:/bmp_more.bin","F:/bmp_return.bin"};
      for(int i=0;i<8;i++) boton(s,m[i],NULL,i%4,i/4);
    }
  }
  else if(!strcmp(modo,"carga") || !strcmp(modo,"calentando")){
    /* draw_dialog.cpp: texto centrado, botón Cancelar en BTN_OK_X + 90, BTN_OK_Y (250 en el tema) */
    const int carga = !strcmp(modo,"carga");
    lv_obj_t *t=etiqueta(s, carga ? "Cargando filamento,\npor favor espere." : "Calentando el extrusor,\npor favor espere...");
    lv_obj_align(t,NULL,LV_ALIGN_CENTER,0, carga ? -70 : -20);
    magna_texto_grande(t);
    if(carga){
      lv_obj_t *b=lv_bar_create(s,NULL); lv_obj_set_pos(b,40,160); lv_obj_set_size(b,400,34);
      magna_estilo_barra(b,NULL); lv_bar_set_value(b,60,LV_ANIM_OFF);
    } else {
      lv_obj_t *tt=etiqueta(s,"Extrusor1: 154/210");
      magna_texto_grande(tt); lv_obj_align(tt,NULL,LV_ALIGN_CENTER,0,-95);
    }
    boton_dialogo(s,280+90-100,250,"Cancelar");
  }
  else if(!strcmp(modo,"imprimiendo")){
    /* draw_printing.cpp: barra en 205,36 de 270x40 con el porcentaje adentro */
    lv_obj_t *b=lv_bar_create(s,NULL); lv_obj_set_pos(b,205,36); lv_obj_set_size(b,270,40);
    lv_obj_t *p=lv_label_create(b,(lv_obj_t*)NULL); lv_label_set_text(p,"45%");
    magna_estilo_barra(b,&magna_fuente_grande); lv_obj_align(p,b,LV_ALIGN_CENTER,0,0);
    lv_bar_set_value(b,45,LV_ANIM_OFF);
    lv_obj_t *e=etiqueta(s,"Extrusor1: 210/210   Cama: 60/60\nTiempo: 01:23:45   Z: 12.40"); lv_obj_set_pos(e,205,100);
  }
  else if(!strcmp(modo,"acerca")){
    /* draw_about.cpp: datos de Marlin centrados, botón Atrás abajo a la derecha y los créditos */
    const char *t[]={"Robin_nano","Marlin 2.1.3-b3 (2026-11-14)","github.com/MarlinFirmware/Marlin",
                     "UUID: cede2a2f-41a2-4748-9b12-c55c62f367ff","Protocol: 1.0"};
    for(int i=0;i<5;i++){ lv_obj_t *l=etiqueta(s,t[i]); lv_obj_align(l,NULL,LV_ALIGN_CENTER,0,-80+30*i); }
    boton(s,"F:/bmp_return.bin","Atras",3,1);
    magna_creditos(s,&lbl,1);
  }
  else {
    const char *ims[]={"F:/bmp_tool.bin","F:/bmp_set.bin","F:/bmp_printing.bin"}; int xs[]={20,180,340};
    for(int i=0;i<3;i++){ lv_obj_t *b=lv_imgbtn_create(s,NULL); lv_imgbtn_set_src(b,LV_BTN_STATE_REL,ims[i]); lv_imgbtn_set_src(b,LV_BTN_STATE_PR,ims[i]); lv_obj_set_pos(b,xs[i],90); }
    lv_obj_t *e=lv_imgbtn_create(s,NULL); lv_imgbtn_set_src(e,LV_BTN_STATE_REL,"F:/bmp_ext1_state.bin"); lv_obj_set_pos(e,20,260);
    lv_obj_t *p=lv_imgbtn_create(s,NULL); lv_imgbtn_set_src(p,LV_BTN_STATE_REL,"F:/bmp_pause.bin"); lv_obj_set_pos(p,180,240);
    lv_obj_t *t=lv_imgbtn_create(s,NULL); lv_imgbtn_set_src(t,LV_BTN_STATE_REL,"F:/bmp_enable.bin"); lv_obj_set_pos(t,360,270);
  }
  for(int k=0;k<5;k++){ lv_tick_inc(10); lv_task_handler(); }
  FILE *o=fopen(argv[2],"wb"); fwrite(fb,2,480*320,o); fclose(o); return 0;
}
/* stubs de la vista previa de gcode que MKS agregó a lv_draw_map (no se usan en esta prueba) */
uint32_t lv_open_gcode_file(char *p){ return 0; }
void lv_gcode_file_read(uint8_t *b){ }
void lv_close_gcode_file(void){ }
