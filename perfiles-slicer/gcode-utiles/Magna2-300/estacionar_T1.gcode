; Magna 2 300 - utilidad para T1
M217 S0 ; cambio 2 en 1 manual
M109 S210 ; PLA (subi a 235-240 para PETG/ABS)
T1
G90
M82
; Usalo cuando el filamento T1 llega hasta la boquilla (por ejemplo, recien cargado).
G92 E0
G1 E-100 F1500 ; sube 100 mm, por encima de la union
G92 E0
M104 S0
M84 E
; fin
