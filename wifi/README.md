# Firmware del módulo WiFi (MKS Robin WiFi, ESP8266)

`MksWifi.bin` es el firmware **oficial de Makerbase, versión CS1.0.4_200227** (la última publicada).
- Origen: https://github.com/makerbase-mks/MKS-WIFI/tree/master/firmware_release (`MksWifi_CS1.0.4_200227.zip`).
- Verificado: es idéntico byte a byte al del repositorio de Makerbase (347.664 bytes) y es una imagen ESP8266 válida (empieza con 0xE9).
- Placa: MKS Robin Nano V1.3, que usa el módulo MKS Robin WiFi con ESP8266. El actualizador de Marlin solo puede grabar firmware de ESP8266.

**No usar** el `MksWifi.BIN` del paquete de charlieburgos: es un firmware para ESP32, en otro formato, y no sirve para este módulo.

## Cómo se instala (opcional)
La compilación lo deja en la carpeta `opcional-wifi/` del artefacto. Solo hace falta si querés actualizar o reparar el WiFi:
1. Copiá `MksWifi.bin` a la raíz de la SD (se puede poner junto con `Robin_nano35.bin` y `assets`).
2. Prendé la impresora: después de cargar los íconos aparece el diálogo de actualización del WiFi. **No la apagues** mientras tanto.
3. Al terminar, el archivo se renombra a `MKSWIFI.CUR`.
