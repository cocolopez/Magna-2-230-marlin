/* Prueba de render: dibuja pantallas con la librería LVGL 6.1.2 de MKS (la misma de la pantalla,
   con su lv_conf.h), usando los íconos del tema leídos desde archivo ("F:/bmp_xxx.bin") y el MISMO
   código que se pega en el firmware (decoracion_menus.inc, estilo_dialogos.inc, fuente_grande.inc).
   Guarda el framebuffer 480x320 RGB565.

   Uso: render <carpeta_assets> <salida.raw> [pantalla]
     pantalla: principal (por defecto) | menu | mas | carga | calentando | imprimiendo | acerca
               | impresion2 (pantalla de impresión de la etapa 30: barra, línea de capa/faltan/fin y hora)
               | principal2 (principal con hora grande, fecha e íconos de WiFi y Telegram)
               | textos (prueba los textos de magna_extras.inc, sin dibujar; sale con 1 si falla)
               | resumen | mensaje | bloqueo | ambiente (etapa 31)
               | grafico | nivel | piezas | vivo (etapa 33)

   La letra normal de la pantalla (16 px, guardada en su memoria SPI) se simula con Roboto 16
   (fuente_normal.inc, la genera verificar_render.py en /tmp). */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "lvgl.h"
#include "decoracion_menus.inc"   /* assets-tema/: el mismo código que se pega en draw_ui.cpp */
#include "estilo_dialogos.inc"
#include "fuente_grande.inc"
#include "creditos.inc"
#include "fuente_normal.inc"      /* /tmp: Roboto 16, solo para la prueba */
#include "fuente_chica.inc"
#include "fuente_enorme.inc"
#include "magna_extras.inc"      /* etapa 30: hora, capas, línea de información */

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

static int fallas;
static void igual(const char *nombre, const char *obtenido, const char *esperado){
  const int ok=!strcmp(obtenido,esperado); if(!ok) fallas++;
  printf("%s %s: \"%s\"%s%s%s\n", ok?"OK   ":"FALLA", nombre, obtenido, ok?"":" (esperado \"", ok?"":esperado, ok?"":"\")"); }

static int probar_textos(void){
  char t[80]; int h,m,d;
  magna_texto_info(t,sizeof t,57,210,8100,1,21,25); igual("todo",t,"Capa 57/210 \xC2\xB7 faltan 2:15 \xC2\xB7 fin 23:40");
  magna_texto_info(t,sizeof t,-1,-1,8100,0,0,0);    igual("sin capas ni hora",t,"faltan 2:15");
  magna_texto_info(t,sizeof t,12,-1,-1,1,10,0);     igual("solo capa",t,"Capa 12");
  magna_texto_info(t,sizeof t,5,9,3600,1,23,30);    igual("fin pasada la medianoche",t,"Capa 5/9 \xC2\xB7 faltan 1:00 \xC2\xB7 fin 00:30");
  magna_texto_info(t,12,57,210,8100,1,21,25);       igual("no se pasa del lugar",t,"Capa 57/210");
  snprintf(t,sizeof t,"%ld",(long)magna_faltan(0,3600,50)); igual("estimado: 50% en 1 h",t,"3600");
  snprintf(t,sizeof t,"%ld",(long)magna_faltan(900,3600,50)); igual("el del slicer manda",t,"900");
  snprintf(t,sizeof t,"%ld",(long)magna_faltan(0,30,50)); igual("muy pronto para estimar",t,"-1");
  snprintf(t,sizeof t,"%d",magna_hora(1000,&h,&m,&d)); igual("sin M258 no hay hora",t,"0");
  magna_hora_poner(75900,6,14,11,1,1000);          /* sábado 14/11 21:05:00 */
  magna_hora(1000+4*60*1000,&h,&m,&d); snprintf(t,sizeof t,"%02d:%02d %d",h,m,d); igual("4 minutos después",t,"21:09 6");
  magna_hora(1000+3*3600*1000u,&h,&m,&d); snprintf(t,sizeof t,"%02d:%02d %d",h,m,d); igual("pasa la medianoche",t,"00:05 0");
  magna_texto_fecha(t,sizeof t,6); igual("fecha",t,"s\xC3\xA1" "b 14/11");
  magna_texto_duracion(t,sizeof t,3*3600+42*60+5); igual("duración",t,"3 h 42 min");
  magna_texto_duracion(t,sizeof t,42*60); igual("duración corta",t,"42 min");
  magna_texto_duracion(t,sizeof t,20); igual("duración muy corta",t,"menos de 1 min");
  magna_texto_filamento(t,sizeof t,16100,124); igual("filamento",t,"48 g \xC2\xB7 16,1 m");
  magna_texto_costo(t,sizeof t,16100,124,18000); igual("costo",t,"$ 864");
  magna_texto_costo(t,sizeof t,161000,124,18000); igual("costo con miles",t,"$ 8.643");
  magna_texto_costo(t,sizeof t,16100,124,0); igual("sin precio no hay costo",t,"");
  printf("%d fallas\n",fallas);
  return fallas?1:0;
}

int main(int argc,char**argv){
  const char *modo = argc>3 ? argv[3] : "principal";
  if(!strcmp(modo,"textos")) return probar_textos();
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
  else if(!strcmp(modo,"impresion2")){
    /* draw_printing.cpp con la etapa 30: barra en 205,32, línea debajo, filas de íconos y botones */
    magna_hora_poner(76200,6,14,11,1,0); magna_capas_poner(56,210);   /* 21:10; capa 57 de 210 */
    magna_reloj_crear();
    lv_obj_t *pv=lv_img_create(s,NULL); lv_obj_set_pos(pv,2,36); (void)pv;
    lv_obj_t *tt=etiqueta(s,"Imprimiendo"); lv_obj_set_pos(tt,3,5);
    lv_obj_t *b=lv_bar_create(s,NULL); lv_obj_set_pos(b,205,32); lv_obj_set_size(b,270,40);
    lv_obj_t *p=lv_label_create(b,(lv_obj_t*)NULL); lv_label_set_text(p,"45%");
    magna_estilo_barra(b,&magna_fuente_grande); lv_obj_align(p,b,LV_ALIGN_CENTER,0,0);
    lv_bar_set_value(b,45,LV_ANIM_OFF);
    lv_obj_t *info=magna_info_crear(s); magna_info_actualizar(info,0,8100,0,45);
    const char *ic[]={"F:/bmp_time_state.bin","F:/bmp_zpos_state.bin","F:/bmp_ext1_state.bin","F:/bmp_fan_state.bin","F:/bmp_bed_state.bin"};
    const char *tx[]={"01:23:45","12.400","210/210","100%","60/60"}; int xs[]={206,350,206,350,206}, ys[]={86,86,136,136,186};
    for(int i=0;i<5;i++){ lv_obj_t *o=lv_img_create(s,NULL); lv_img_set_src(o,ic[i]); lv_obj_set_pos(o,xs[i],ys[i]);
      lv_obj_t *l=etiqueta(s,tx[i]); lv_obj_set_pos(l,xs[i]+44,ys[i]+10); }
    const char *bt[]={"F:/bmp_pause.bin","F:/bmp_stop.bin","F:/bmp_operate.bin"};
    for(int i=0;i<3;i++){ lv_obj_t *o=lv_img_create(s,NULL); lv_img_set_src(o,bt[i]); lv_obj_set_pos(o,5+160*i,240); }
    magna_reloj_mostrar(0,1);
  }
  else if(!strcmp(modo,"principal2")){
    magna_hora_poner(76200,6,14,11,1,0);
    const char *ims[]={"F:/bmp_tool.bin","F:/bmp_set.bin","F:/bmp_printing.bin"}; int xs[]={20,180,340};
    for(int i=0;i<3;i++){ lv_obj_t *b=lv_imgbtn_create(s,NULL); lv_imgbtn_set_src(b,LV_BTN_STATE_REL,ims[i]); lv_imgbtn_set_src(b,LV_BTN_STATE_PR,ims[i]); lv_obj_set_pos(b,xs[i],90); }
    lv_obj_t *ti=etiqueta(s,"M A G N A  2"); lv_obj_set_pos(ti,24,30);
    magna_principal_crear(s); magna_principal_actualizar(0,1);
    magna_reloj_crear(); magna_reloj_mostrar(0,0);
  }
  else if(!strcmp(modo,"resumen")){
    /* draw_dialog.cpp, impresión terminada: título arriba (letra grande), resumen y botón Confirmar */
    magna_opciones_poner(-1,18000,124);
    lv_obj_t *t=etiqueta(s,"Impresi\xC3\xB3n terminada"); lv_obj_align(t,NULL,LV_ALIGN_CENTER,0,-20); magna_texto_grande(t);
    magna_resumen(s,t,3*3600+42*60,16100);
    boton_dialogo(s,280+90-100,250,"Confirmar");
  }
  else if(!strcmp(modo,"mensaje") || !strcmp(modo,"bloqueo") || !strcmp(modo,"ambiente")){
    const char *ims[]={"F:/bmp_tool.bin","F:/bmp_set.bin","F:/bmp_printing.bin"}; int xs[]={20,180,340};
    for(int i=0;i<3;i++){ lv_obj_t *b=lv_imgbtn_create(s,NULL); lv_imgbtn_set_src(b,LV_BTN_STATE_REL,ims[i]); lv_imgbtn_set_src(b,LV_BTN_STATE_PR,ims[i]); lv_obj_set_pos(b,xs[i],90); }
    magna_hora_poner(76200,6,14,11,1,0);
    if(!strcmp(modo,"mensaje")) magna_mensaje("Cambi\xC3\xA1 el filamento a PETG negro");
    else if(!strcmp(modo,"bloqueo")) { magna_candado_crear(s); magna_bloquear(); }
    else { lv_obj_t *info=magna_info_crear(s); magna_info_actualizar(info,0,9300,0,45); magna_ambiente_mostrar(0); }
  }
  else if(!strcmp(modo,"grafico") || !strcmp(modo,"nivel") || !strcmp(modo,"piezas")){
    magna_hora_poner(76200,6,14,11,1,0);
    if(!strcmp(modo,"grafico")){
      for(int k=0;k<80;k++){ int e=k<20?30+k*9:208+(k%7==0); int c=k<40?25+k:60; magna_hist_agregar(e,210,c,60); }
      magna_grafico_abrir();
    } else if(!strcmp(modo,"nivel")){
      static const int16_t v[25]={ 30,0,20,60,120,  -20,-40,-10,20,80,  -50,-60,-30,0,50,  -20,-40,-10,30,80,  60,20,0,70,110 };
      int16_t m[25]; for(int x=0;x<5;x++) for(int y=0;y<5;y++) m[x*5+y]= (x*5+y<18)? v[y*5+x] : MAGNA_NIVEL_SIN;
      magna_nivel_abrir(5,5); magna_nivel_actualizar(m);
    } else {
      magna_pieza_indice("soporte_A"); magna_pieza_indice("soporte_B"); magna_pieza_indice("tapa"); magna_pieza_indice("NONMESH"); magna_pieza_indice("clip");
      magna_piezas_abrir();
    }
    magna_reloj_crear(); magna_reloj_mostrar(0,1);
  }
  else if(!strcmp(modo,"vivo")){
    magna_vista_cama(230,230);
    for(int k=0;k<=36;k++){ double a0=k*10*3.14159/180, a1=(k+1)*10*3.14159/180;
      magna_vista_linea(115+60*cos(a0),115+60*sin(a0),115+60*cos(a1),115+60*sin(a1),0.4); }
    for(int y=70;y<=160;y+=8) magna_vista_linea(60,y,170,y,0.4);
    magna_vista_crear(s,NULL);
    { lv_event_send(lv_obj_get_child(s,NULL),LV_EVENT_RELEASED,NULL); }   /* tocar: mostrar la vista en vivo */
    lv_obj_t *b=lv_bar_create(s,NULL); lv_obj_set_pos(b,205,32); lv_obj_set_size(b,270,40); magna_estilo_barra(b,&magna_fuente_grande); lv_bar_set_value(b,45,LV_ANIM_OFF);
    magna_botones_impresion(s); magna_candado_crear(s);
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
