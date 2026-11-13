#!/usr/bin/env bash
# Verifica que los valores clave de la Magna 2 230 sigan en Configuration.h / _adv.h
cd "$(dirname "$0")/.."
C=Marlin/Configuration.h; A=Marlin/Configuration_adv.h; fail=0
chk(){ grep -qE "^\s*#define $1\s+$2" "$3" && echo "ok   $1 = $2" || { echo "MAL  $1 (esperado: $2)"; fail=1; }; }
chk MOTHERBOARD BOARD_MKS_ROBIN_NANO_V1_3_F4 $C
chk EXTRUDERS 2 $C
chk SINGLENOZZLE "" $C
chk TEMP_SENSOR_0 1 $C
chk TEMP_SENSOR_BED 1 $C
chk DEFAULT_AXIS_STEPS_PER_UNIT "\{ 80, 80, 400, 425, 423 \}" $C
chk INVERT_X_DIR false $C
chk INVERT_Y_DIR true $C
chk INVERT_Z_DIR true $C
chk INVERT_E0_DIR true $C
chk INVERT_E1_DIR true $C
chk X_MIN_ENDSTOP_HIT_STATE LOW $C
chk Y_MIN_ENDSTOP_HIT_STATE LOW $C
chk Z_MIN_ENDSTOP_HIT_STATE LOW $C
chk X_BED_SIZE 230 $C
chk Y_BED_SIZE 230 $C
chk Z_MAX_POS 250 $C
chk TFT_LVGL_UI "" $C
chk MKS_ROBIN_TFT35 "" $C
chk LIN_ADVANCE "" $A
chk POWER_LOSS_RECOVERY "" $A
chk S_CURVE_ACCELERATION "" $C
chk MPCTEMP "" $C
chk FILAMENT_RUNOUT_DISTANCE_MM 15 $C
chk TOOLCHANGE_FILAMENT_SWAP "" $A
chk INPUT_SHAPING_X "" $A
chk INPUT_SHAPING_Y "" $A
chk HOTEND_IDLE_TIMEOUT "" $A
chk CANCEL_OBJECTS "" $A
chk SET_PROGRESS_MANUALLY "" $A
grep -qE "^\s*#define PIDTEMP\b" $C && { echo "MAL  PIDTEMP deberia estar desactivado (se usa MPC)"; fail=1; } || echo "ok   PIDTEMP desactivado"
exit $fail
