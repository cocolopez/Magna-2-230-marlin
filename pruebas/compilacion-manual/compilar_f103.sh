#!/usr/bin/env bash
# Versión para la Robin Nano V1.2 (STM32F103VE, 72 MHz, 64 KB de RAM, bootloader de 28 KB). Uso: compilar_f103.sh <proyecto_completo>
# Compila y enlaza el firmware completo (Marlin + core STM32 1.9.0 + LVGL + QRCode) sin PlatformIO.
# Uso: compilar_full.sh <proyecto_completo>
set -u
P=$(realpath "$1"); TC=${TC:-$HOME/marlin-tc}; GCC=$TC/xpack-arm-none-eabi-gcc-13.3.1-1.1/bin
CORE=$TC/core; VAR=$P/buildroot/share/PlatformIO/variants/MARLIN_F103Vx
O=${O:-/tmp/full12}; rm -rf $O; mkdir -p $O/obj
CPU="-mcpu=cortex-m3 -mthumb"
DEFS="-DPLATFORMIO=60118 -DSTM32F103xE -DSTM32F1 -DSTM32F1xx -DARDUINO=10808 -DARDUINO_ARCH_STM32 -DARDUINO_MARLIN_F103Vx -DBOARD_NAME=\"MARLIN_F103Vx\" -DHAL_UART_MODULE_ENABLED -DUSE_HAL_DRIVER -DUSE_FULL_LL_DRIVER -DVECT_TAB_OFFSET=0x7000 -DF_CPU=72000000L \
 -D__MARLIN_FIRMWARE__ -DNDEBUG -DHAL_STM32 -DPLATFORM_M997_SUPPORT -DTIM_IRQ_PRIO=13 -DADC_RESOLUTION=12 \
 -DMCU_STM32F103VE -DENABLE_HWSERIAL3 -DTIMER_SERVO=TIM2 -DTIMER_TONE=TIM3 -DSS_TIMER=4 -DHAL_SD_MODULE_ENABLED -DHAL_SRAM_MODULE_ENABLED \
 -DSERIAL_RX_BUFFER_SIZE=128 -DSERIAL_TX_BUFFER_SIZE=64"
INC="-I$P/Marlin -I$P/Marlin/src -I$CORE/cores/arduino -I$CORE/cores/arduino/avr -I$CORE/cores/arduino/stm32 -I$CORE/cores/arduino/stm32/LL -I$CORE/cores/arduino/stm32/usb -I$CORE/cores/arduino/stm32/OpenAMP \
 -I$CORE/system/Drivers/STM32F1xx_HAL_Driver/Inc -I$CORE/system/Drivers/STM32F1xx_HAL_Driver/Src -I$CORE/system/STM32F1xx -I$CORE/system/Drivers/CMSIS/Device/ST/STM32F1xx/Include -I$CORE/system/Drivers/CMSIS/Device/ST/STM32F1xx/Source/Templates/gcc \
 -I$TC/cmsis/CMSIS/Core/Include -I$VAR -I$TC/lvgl -I$TC/lvgl/src -I$TC/qrcode"
for l in SrcWrapper SPI Wire Servo IWatchdog EEPROM; do INC="$INC -I$CORE/libraries/$l/src"; done
COMMON="$CPU -Os -g0 -ffunction-sections -fdata-sections -w -nostdlib --param max-inline-insns-single=500 $DEFS $INC"
CXX="$GCC/arm-none-eabi-g++ $COMMON -std=gnu++14 -fno-threadsafe-statics -fno-rtti -fno-exceptions -fno-use-cxa-atexit"
CC="$GCC/arm-none-eabi-gcc $COMMON -std=gnu11 -include stdint.h"
: > $O/src.txt
python3 -I "$(dirname "$0")/lista_fuentes.py" $P | sed "s#^#$P/Marlin/#" >> $O/src.txt
find $CORE/cores/arduino $CORE/libraries/SrcWrapper/src $CORE/libraries/SPI/src $CORE/libraries/Wire/src $CORE/libraries/Servo/src $CORE/libraries/IWatchdog/src $CORE/libraries/EEPROM/src -type f \( -name '*.c' -o -name '*.cpp' -o -name '*.S' \) >> $O/src.txt
find $VAR -name '*.c' -o -name '*.cpp' | grep -v '/variants/MARLIN_F103Vx/.*\.ld' >> $O/src.txt
find $TC/lvgl/src -name '*.c' >> $O/src.txt
find $TC/qrcode -maxdepth 1 -name '*.c' >> $O/src.txt
echo "Fuentes: $(wc -l < $O/src.txt)"
comp() { f="$1"; o="$O/obj/$(echo "$f" | md5sum | cut -c1-12).o"
  case "$f" in *.cpp) $CXX -c "$f" -o "$o" ;; *.c) $CC -c "$f" -o "$o" ;; *.S) $GCC/arm-none-eabi-gcc $CPU $DEFS $INC -x assembler-with-cpp -c "$f" -o "$o" ;; esac 2> "$o.err" || echo "$f" >> $O/failed.txt; }
export -f comp; export CXX CC GCC CPU DEFS INC O
xargs -P $(nproc) -I{} bash -c 'comp "$@"' _ {} < $O/src.txt
if [ -s $O/failed.txt ]; then echo "FALLARON $(wc -l < $O/failed.txt):"; while read f; do echo "== $f"; grep -m5 error "$O/obj/$(echo "$f" | md5sum | cut -c1-12).o.err"; done < $O/failed.txt; exit 1; fi
$GCC/arm-none-eabi-g++ $CPU -Os -Wl,--gc-sections -Wl,--defsym=LD_FLASH_OFFSET=0x7000 -Wl,--defsym=LD_MAX_SIZE=524288 -Wl,--defsym=LD_MAX_DATA_SIZE=65536 \
  -T $VAR/ldscript.ld --specs=nano.specs -Wl,-Map=$O/firmware.map -Wl,--entry=Reset_Handler \
  $O/obj/*.o -Wl,--start-group -lc -lm -lgcc -lstdc++ -Wl,--end-group -o $O/firmware.elf 2> $O/link.err || { echo "ERROR DE ENLAZADO:"; grep -E "error|undefined|overflow" $O/link.err | head -20; exit 1; }
$GCC/arm-none-eabi-objcopy -O binary $O/firmware.elf $O/Robin_nano35.bin
$GCC/arm-none-eabi-size $O/firmware.elf
B=$(stat -c%s $O/Robin_nano35.bin); echo "Robin_nano35.bin = $B bytes; disponible = $((524288-28672)) bytes (512K - bootloader 28K); uso = $((B*100/(524288-28672)))%"
