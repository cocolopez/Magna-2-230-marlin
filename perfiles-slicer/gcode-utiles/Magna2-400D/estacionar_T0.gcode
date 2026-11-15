; Magna 2 400D - utilidad para T0
M217 S0 ; cambio 2 en 1 manual
M109 S210 ; PLA (subi a 235-240 para PETG/ABS)
T0
G90
M82
; Usalo cuando el filamento T0 llega hasta la boquilla (por ejemplo, recien cargado).
G92 E0
G1 E-60 F1500 ; sube 60 mm, por encima de la union
G92 E0
M104 S0
M84 E
; fin
