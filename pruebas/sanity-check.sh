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
g++ -std=gnu++17 -fsyntax-only -D__MARLIN_DEPS__ -DARDUINO_ARCH_STM32 \
    -DSTM32F4 -DSTM32F4xx -DSTM32F407xx -DARDUINO_MARLIN_F4x7Vx \
    -I. -IMarlin -IMarlin/src /tmp/marlin_chk.cpp 2>&1 | grep -E "error" && { echo "FALLA: hay errores de configuración"; exit 1; } || echo "OK: la configuración pasa los SanityCheck de Marlin"
