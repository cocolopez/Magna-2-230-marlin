; Magna 2 400 - utilidad para T1
M217 S0 ; cambio 2 en 1 manual
M109 S210 ; PLA (subi a 235-240 para PETG/ABS)
T1
G90
M82
; Baja T1 desde la posicion de estacionado y purga un poco.
; El OTRO filamento tiene que estar estacionado.
G92 E0
G1 E100 F1500
G1 E120 F180 ; purga 20 mm
G92 E0
M104 S0
M84 E
; fin
