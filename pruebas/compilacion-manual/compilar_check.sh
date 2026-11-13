#!/usr/bin/env bash
# Compila (sin linkear) todos los .cpp/.c de Marlin para mks_robin_nano_v1_3_f4 con el
# toolchain/core reales, para detectar errores de compilación sin PlatformIO.
# Uso: compilar_check.sh <dir_proyecto_completo> [modo: syntax|obj]
set -u
P=$(realpath "$1"); MODE=${2:-syntax}
TC=${TC:-$HOME/marlin-tc}; GCC=$TC/xpack-arm-none-eabi-gcc-13.3.1-1.1/bin
CORE=$TC/core; VAR=$P/buildroot/share/PlatformIO/variants/MARLIN_F4x7Vx
OUT=/tmp/cc_out; rm -rf $OUT; mkdir -p $OUT
CPU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
DEFS="-DPLATFORMIO=60118 -DSTM32F407xx -DSTM32F4 -DSTM32F4xx -DARDUINO=10808 -DARDUINO_ARCH_STM32 -DARDUINO_MARLIN_F4x7Vx -DBOARD_NAME=\"MARLIN_F4x7Vx\" -DHAL_UART_MODULE_ENABLED -DUSE_HAL_DRIVER -DUSE_FULL_LL_DRIVER -DVECT_TAB_OFFSET=0x8000 -DF_CPU=168000000L \
 -D__MARLIN_FIRMWARE__ -DNDEBUG -DHAL_STM32 -DPLATFORM_M997_SUPPORT -DTIM_IRQ_PRIO=13 -DADC_RESOLUTION=12 \
 -DMCU_STM32F407VE -DENABLE_HWSERIAL3 -DSTM32_FLASH_SIZE=512 -DTIMER_SERVO=TIM2 -DTIMER_TONE=TIM3 -DSS_TIMER=4 -DHAL_SD_MODULE_ENABLED -DHAL_SRAM_MODULE_ENABLED \
 -DSERIAL_RX_BUFFER_SIZE=128 -DSERIAL_TX_BUFFER_SIZE=64"
INC="-I$P/Marlin -I$P/Marlin/src -I$CORE/cores/arduino -I$CORE/cores/arduino/avr -I$CORE/cores/arduino/stm32 -I$CORE/cores/arduino/stm32/LL -I$CORE/cores/arduino/stm32/usb -I$CORE/cores/arduino/stm32/OpenAMP \
 -I$CORE/system/Drivers/STM32F4xx_HAL_Driver/Inc -I$CORE/system/Drivers/STM32F4xx_HAL_Driver/Src -I$CORE/system/STM32F4xx -I$CORE/system/Drivers/CMSIS/Device/ST/STM32F4xx/Include \
 -I$TC/cmsis/CMSIS/Core/Include -I$VAR -I$TC/lvgl -I$TC/lvgl/src -I$TC/qrcode"
for l in SrcWrapper SPI Wire Servo EEPROM IWatchdog SoftwareSerial; do INC="$INC -I$CORE/libraries/$l/src"; done
[ "$MODE" = syntax ] && M="-fsyntax-only" || M="-c"
CXX="$GCC/arm-none-eabi-g++ $CPU -Os -std=gnu++14 -fno-threadsafe-statics -fno-rtti -fno-exceptions -fno-use-cxa-atexit -ffunction-sections -fdata-sections -w $DEFS $INC"
# lista: src menos otras HAL/tests/config (los archivos de features apagados quedan vacíos por #if)
cd $P/Marlin
python3 -I "$(dirname "$0")/lista_fuentes.py" $P | grep '\.cpp$' > $OUT/list.txt
echo "Archivos: $(wc -l < $OUT/list.txt)"
cat $OUT/list.txt | xargs -P $(nproc) -I{} sh -c "$CXX $M {} -o $OUT/\$(echo {} | tr / _).o 2> $OUT/\$(echo {} | tr / _).err || echo {} >> $OUT/failed.txt"
if [ -s $OUT/failed.txt ]; then echo "FALLARON: $(wc -l < $OUT/failed.txt)"; for f in $(cat $OUT/failed.txt); do grep -h "error" $OUT/$(echo $f | tr / _).err | head -5; done; exit 1; else echo "OK: todo compila"; fi
