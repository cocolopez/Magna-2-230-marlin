# Compilación sin PlatformIO (diagnóstico)

Sirve para encontrar errores de compilación sin depender de GitHub Actions (por ejemplo, en un entorno donde PlatformIO no se puede instalar). Usa las mismas versiones que la build real: núcleo STM32 1.9.0, LVGL 6.1.2 MKS y QRCode MKS, con los mismos defines del entorno `mks_robin_nano_v1_3_f4`.

1. `TC=$HOME/marlin-tc bash preparar.sh` baja el compilador y las librerías.
2. `bash ../armar-local.sh` arma el proyecto completo en `build/`.
3. Elegí una de las dos compilaciones:
   - `TC=$HOME/marlin-tc bash compilar_check.sh build` compila todos los `.cpp` sin enlazar. Es rápido y lista todos los errores juntos.
   - `TC=$HOME/marlin-tc bash compilar_full.sh build` compila y enlaza el firmware completo. Muestra el tamaño y el % de flash usado y deja `/tmp/full/Robin_nano35.bin`.

`lista_fuentes.py` replica el filtro de `common-dependencies.py` de Marlin: solo compila las carpetas de las funciones activadas.

Notas:
- El firmware oficial es el que compila GitHub Actions con PlatformIO. Esto es una herramienta de verificación: usa otro GCC (13.3) y no genera la carpeta `assets`.
- Resultado al 13/11/2026: 351.328 bytes, el 71 % de 480 KB. RAM: 80 KB de 128 KB.
