/* Prueba de render: dibuja con la librería LVGL 6.1.2 de MKS (la misma de la pantalla, con su lv_conf.h)
   la pantalla principal usando los íconos del tema leídos desde archivo ("F:/bmp_xxx.bin"), y guarda el
   framebuffer 480x320 RGB565. Sirve para detectar íconos con formato inválido ANTES de flashear
   (por ejemplo cf=5, que se ve verde y repetido).
   Uso: render <carpeta_assets> <salida.raw> [menu]
   Con "menu" dibuja la pantalla Ajustes con la decoración marcada (decoracion_menus.inc). */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "lvgl.h"
#include "decoracion_menus.inc"   /* assets-tema/: el mismo código que se pega en draw_ui.cpp */
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
int main(int argc,char**argv){
  DIR_ASSETS=argv[1];
  lv_init();
  static lv_disp_buf_t db; static lv_color_t buf[480*17];
  lv_disp_buf_init(&db,buf,NULL,480*17);
  lv_disp_drv_t dd; lv_disp_drv_init(&dd); dd.flush_cb=flush; dd.buffer=&db; lv_disp_drv_register(&dd);
  lv_fs_drv_t fd; memset(&fd,0,sizeof fd); lv_fs_drv_init(&fd); fd.file_size=sizeof(mf_t); fd.letter='F';
  fd.open_cb=f_open; fd.close_cb=f_close; fd.read_cb=f_read; fd.seek_cb=f_seek; fd.tell_cb=f_tell; lv_fs_drv_register(&fd);
  static lv_style_t scr; lv_style_copy(&scr,&lv_style_scr);
  scr.body.main_color=LV_COLOR_MAKE(0x14,0x14,0x14); scr.body.grad_color=LV_COLOR_MAKE(0x5C, 0x0E, 0x14);
  lv_obj_t *s=lv_obj_create(NULL,NULL); lv_obj_set_style(s,&scr); lv_scr_load(s);
  if(argc>3 && !strcmp(argv[3],"menu")){
    /* pantalla Ajustes: decoración detrás, título, 8 íconos en 2 filas (misma grilla que MKS) */
    static lv_style_t lbl; lv_style_copy(&lbl,&lv_style_plain); lbl.text.color=LV_COLOR_WHITE; lbl.text.font=LV_FONT_DEFAULT;
    magna_decorar_menu(s,true,false);
    lv_obj_t *tit=lv_label_create(s,(lv_obj_t*)NULL); lv_label_set_text(tit,"Ready>Settings"); lv_obj_set_style(tit,&lbl); lv_obj_set_pos(tit,3,5);
    /* como hace draw_move_motor.cpp: toma el primer hijo de la pantalla como título y lo achica.
       Tiene que ser el título de verdad (la decoración no puede crear objetos). */
    if(lv_obj_get_child_back(s,NULL)!=tit){ fprintf(stderr,"el primer hijo de la pantalla no es el titulo\n"); return 3; }
    lv_obj_set_width(lv_obj_get_child_back(s,NULL),480-101);
    magna_marca_titulo(s,tit,&lbl);
    const char *m[]={"F:/bmp_preHeat.bin","F:/bmp_extruct.bin","F:/bmp_mov.bin","F:/bmp_zero.bin",
                     "F:/bmp_leveling.bin","F:/bmp_filamentchange.bin","F:/bmp_more.bin","F:/bmp_return.bin"};
    for(int i=0;i<8;i++){ lv_obj_t *b=lv_imgbtn_create(s,NULL); lv_imgbtn_set_src(b,LV_BTN_STATE_REL,m[i]); lv_imgbtn_set_src(b,LV_BTN_STATE_PR,m[i]);
      lv_obj_set_pos(b,2+(i%4)*119,36+(i/4)*142); }
  } else {
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
