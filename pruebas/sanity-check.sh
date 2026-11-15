#!/usr/bin/env bash
# Chequeo rápido de la configuración SIN compilar el firmware completo.
# Corre los SanityCheck.h de Marlin con g++ del sistema (no necesita PlatformIO).
# Uso: bash pruebas/sanity-check.sh   (desde la raíz del proyecto)
set -euo pipefail
cd "$(dirname "$0")/.."
cat > /tmp/marlin_chk.cpp <<'CPP'
#include "Marlin/src/inc/MarlinConfig.h"
#include "Marlin/src/inc/Changes.h"
#include <stdint.h>
#include <math.h>
#include "Marlin/src/core/macros.h"
#include "Marlin/src/inc/SanityCheck.h"
#include "Marlin/src/HAL/STM32/inc/SanityCheck.h"
int main(){}
CPP
# El procesador según la placa: V1.3 = STM32F407 (mm2), V1.2 = STM32F103 (mm12)
if grep -qE '^\s*#define MOTHERBOARD BOARD_MKS_ROBIN_NANO\b' Marlin/Configuration.h; then
  MCU="-DSTM32F1 -DSTM32F1xx -DSTM32F103xE -DARDUINO_MARLIN_F103Vx"
else
  MCU="-DSTM32F4 -DSTM32F4xx -DSTM32F407xx -DARDUINO_MARLIN_F4x7Vx"
fi
# (antes el resultado de g++ se perdía con pipefail y siempre decía OK: ahora se guarda y se revisa)
SALIDA=$(g++ -std=gnu++17 -fsyntax-only -D__MARLIN_DEPS__ -DARDUINO_ARCH_STM32 $MCU \
    -I. -IMarlin -IMarlin/src /tmp/marlin_chk.cpp 2>&1 || true)
# En la V1.2 JTAG_DISABLE lo define el core STM32 (que este chequeo no incluye): ese aviso no cuenta
SALIDA=$(echo "$SALIDA" | grep -v "DISABLE_JTAG is not supported" || true)
if echo "$SALIDA" | grep -E "error"; then
  echo "FALLA: hay errores de configuración"; exit 1
fi
echo "OK: la configuración pasa los SanityCheck de Marlin"
