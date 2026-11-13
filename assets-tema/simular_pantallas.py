import struct,sys,os
from PIL import Image, ImageDraw, ImageFont
A=sys.argv[1]; out=sys.argv[2]
def load(n):
    b=open(os.path.join(A,f'bmp_{n}.bin'),'rb').read()
    if n=='logo': w,h,o=480,320,0
    else: hd=struct.unpack('<I',b[:4])[0]; w,h,o=(hd>>10)&0x7ff,(hd>>21)&0x7ff,4
    px=struct.unpack('<%dH'%(w*h),b[o:o+w*h*2]); im=Image.new('RGB',(w,h))
    im.putdata([(((p>>11)&31)*255//31,((p>>5)&63)*255//63,(p&31)*255//31) for p in px]); return im
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
def pantalla(items, titulo):
    sc=Image.new('RGB',(480,320),(24,24,24)); d=ImageDraw.Draw(sc)
    d.text((10,6),titulo,font=F,fill=(238,238,238))
    for i,(n,lab) in enumerate(items):
        x=i%4*120+1; y=26+(i//4)*146
        sc.paste(load(n),(x,y)); d.text((x+58,y+120),lab,font=F,fill=(238,238,238),anchor='mm')
    return sc
m1=pantalla([('preHeat','Precalentar'),('mov','Mover'),('zero','Home'),('leveling','Nivelar'),('filamentchange','Filamento'),('extruct','Extrusor'),('more','Más'),('return','Volver')],'Herramientas')
m2=pantalla([('fan','Ventilador'),('speed','Velocidad'),('extru1','Extrusor 1'),('extru2','Extrusor 2'),('wifi','WiFi'),('language','Idioma'),('machine_para','Máquina'),('eeprom_settings','EEPROM')],'Configuración')
# pantalla de impresión simplificada
m3=Image.new('RGB',(480,320),(24,24,24)); d=ImageDraw.Draw(m3)
d.text((10,6),'Imprimiendo: pieza.gcode',font=F,fill=(238,238,238))
for i,(n,t) in enumerate([('ext1_state','210/210°'),('bed_state','60/60°'),('fan_state','100%'),('time_state','01:24'),('zpos_state','12.40'),('speed_state','100%')]):
    x=200+(i%2)*140; y=40+(i//2)*55; m3.paste(load(n),(x,y)); d.text((x+52,y+22),t,font=F,fill=(238,238,238),anchor='lm')
d.rectangle([20,40,180,200],outline=(80,80,80)); d.text((100,120),'vista previa',font=F,fill=(90,90,90),anchor='mm')
d.rectangle([20,215,460,225],fill=(50,50,50)); d.rectangle([20,215,300,225],fill=(214,32,39)); d.text((470,220),'',font=F)
for i,n in enumerate(['operate','pause','stop']):
    m3.paste(load(n),(10+i*155,236))
d.text((10+62,276),'Opciones',font=F,fill=(238,238,238),anchor='lm'); d.text((165+62,276),'Pausa',font=F,fill=(238,238,238),anchor='lm'); d.text((320+62,276),'Detener',font=F,fill=(238,238,238),anchor='lm')
lg=load('logo')
hoja=Image.new('RGB',(980,670),(70,70,70))
for im,(x,y) in zip([lg,m1,m2,m3],[(5,5),(495,5),(5,335),(495,335)]): hoja.paste(im,(x,y))
hoja.save(out)
