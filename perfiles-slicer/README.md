# Perfiles de slicer — Magna 2 230 (Marlin 2.1)

Pensados para **este firmware**: mismos límites de velocidad y aceleración, cama de 230×230×250 y doble extrusor con boquilla única (hotend 2 en 1).

| | Cura 5.10 o superior | PrusaSlicer 2.6+ | OrcaSlicer 2.x |
|---|---|---|---|
| Máquina | ✔ (con la cama y textura de la Magna 2 que trae Cura) | ✔ | ✔ |
| Calidades | Fina 0.12 · Estándar 0.16 · Normal 0.20 · Rápida 0.28 | igual | igual |
| Materiales | PLA, PETG y ABS (calidades propias por material) | PLA, PETG, ABS | PLA, PETG, ABS |
| Cambio 2 en 1 | sí (gcode de cada extrusor) | sí (torre de purga, modo SEMM) | sí (torre de purga, modo SEMM) |

> **Otros modelos:** también hay perfiles para la 300, 400, 400D, 500 y 500D (archivos con su número; en Cura dicen "(sin probar)"). Usan las medidas y límites de su firmware y **no están probados**: solo existe la 230. Las D (extrusor directo) retraen 1 mm y en el cambio 2 en 1 suben cada filamento 60 mm, un valor sin medir (ver `docs-magna/MODELOS.md`). Los gcode útiles de cada modelo están en `gcode-utiles/Magna2-XXX/`.

> Todo sale de `generar_perfiles.py` (los valores están arriba de todo). Si cambiás algo, corré `python3 generar_perfiles.py` y después `python3 ../pruebas/verificar-perfiles.py`.

## Cura

### Por qué no aparecían los perfiles anteriores
1. **Cada versión de Cura tiene su propia carpeta de configuración** (`…\cura\5.10`, `…\cura\5.11`, etc.). Al actualizar Cura, los archivos copiados en la carpeta de la versión vieja no se ven. Hay que copiarlos en la carpeta de la versión que usás. El instalador elige siempre la más nueva.
2. **La velocidad de retracción era 40 mm/s**, más alta que el máximo del extrusor (25 mm/s). Cura la marcaba en rojo y no dejaba laminar. Ahora todas las retracciones van a 25 mm/s.

### Instalar
1. Abrí la versión nueva de Cura **una vez** (crea su carpeta) y cerrala.
2. Dentro de la carpeta `cura` de estos perfiles:
   - **Windows:** doble clic en `instalar-windows.bat`.
   - **Mac / Linux:** `sh instalar-mac-linux.sh`.

   **A mano:** en Cura usá **Ayuda → Mostrar carpeta de configuración** y copiá:
   - `definitions/*.def.json` a `definitions`;
   - `extruders/*.def.json` a `extruders`;
   - la carpeta `quality/hellbot_magna2_230_marlin` dentro de `quality`.

   Si alguna carpeta no existe, creala.
3. Abrí Cura y elegí **Agregar impresora → Agregar una impresora no conectada en red → Hellbot → Hellbot Magna 2 230 Marlin 2.1**. Es una impresora aparte de las "Hellbot Magna 2 230" de fábrica: no la confundas con esas.
4. En cada extrusor elegí el material genérico (**Generic PLA**, **PETG** o **ABS**). Las calidades ajustan solas las temperaturas, el ventilador, la retracción y las velocidades de ese material. Con otras marcas de PLA, PETG o ABS se usan las mismas calidades del tipo.
5. **Opcional:** para que la pantalla muestre el tiempo restante, andá a **Extensiones → Post-procesado → Modificar G-Code → Agregar script → Display Progress On LCD**.

### Qué trae
- **Velocidades:** Hellbot recomienda 50 mm/s y un máximo de 80 mm/s. Los perfiles usan:
  - 50 mm/s en general y 25–35 mm/s en el perímetro exterior;
  - 55–75 mm/s de relleno;
  - 20 mm/s en la primera capa y 150 mm/s de viaje.
- **Aceleraciones:** 1500 mm/s² al imprimir, 1000 en el perímetro exterior, 2000 en los viajes y 800 en la primera capa. El jerk queda a cargo del firmware.
- **Retracción (bowden):**
  - PLA y ABS: 5 mm a 25 mm/s.
  - PETG: 6 mm.
  - Peinado (combing) "sin piel", hasta 20 retracciones por tramo.
- **Temperaturas:**

  | Material | Hotend | Hotend, 1ª capa | Cama | Cama, 1ª capa | Ventilador |
  |---|---|---|---|---|---|
  | PLA | 205 °C | 210 °C | 60 °C | 65 °C | 100 % desde la capa 2 |
  | PETG | 235 °C | 240 °C | 75 °C | 80 °C | 30–50 % |
  | ABS | 240 °C | 245 °C | 100 °C | 105 °C | 0–15 % |

  Además, PETG está limitado a 45 mm/s y ABS a 50 mm/s.
- **Relleno y adherencia:** relleno gyroid al 15 % y falda (skirt) de 3 líneas. La falda sirve también de purga después de cargar el filamento.
- **Doble color:**
  - torre de purga de 25 mm con 60 mm³ por cambio (atrás a la derecha);
  - subida de 1 mm después de cada cambio.

## Cómo funciona el cambio de filamento (2 en 1)

La Magna 2 230 tiene **una sola boquilla** con una unión en Y. Para que entre un filamento, el otro tiene que estar **retirado unos 100 mm, por encima de la unión**. Ese valor es el mismo que usa el perfil oficial de Hellbot.

- **Estado de reposo:** los **dos filamentos estacionados** (retirados 100 mm). Las impresiones terminan dejándolos así.
- **Al usar un extrusor:** el slicer lo baja 100 mm en la esquina de adelante a la derecha (X225 Y5) y purga en la falda o en la torre.
- **Al cambiar de extrusor o al terminar:** retira 6 mm en el lugar, sube 1 mm, va a la esquina y retira los 94 mm restantes.
- **Si recién cargaste un filamento hasta la boquilla** (por ejemplo, desde la pantalla), copiá en la SD y ejecutá `gcode-utiles/estacionar_T0.gcode` (o `_T1`). Con `cargar_T0` / `cargar_T1` lo bajás a mano para purgar o cambiar de color.

El cambio lo hace **el slicer**, no el firmware. Todos los gcode de inicio mandan `M217 S0` por si la memoria (EEPROM) guardó otro valor. El motivo: Marlin solo retira el filamento viejo si él mismo lo cargó desde que se prendió la máquina, así que en el primer cambio T0 → T1 no retiraba T0. Para un cambio manual desde la terminal todavía se puede usar `M217 S100` y después `T0` / `T1`.

## PrusaSlicer
Andá a **Archivo → Importar → Importar paquete de configuración** y elegí `prusaslicer/Magna2-230_PrusaSlicer_bundle.ini`.

- Usa el modo de un extrusor con varios materiales (SEMM): la torre de purga hace la descarga y la carga, con el estacionado en 100 mm.
- El gcode de inicio carga el primer filamento y hace la línea de purga. El de fin estaciona el último.
- Ya emite el tiempo restante (M73) y las etiquetas para cancelar objetos (M486).

## OrcaSlicer
Andá a **Archivo → Importar → Importar configuraciones** y elegí todos los `.json` de `orcaslicer/machine`, `orcaslicer/process` y `orcaslicer/filament`. Empezá por el de la máquina. Funciona igual que PrusaSlicer.

## Ajustes finos que vale la pena hacer
- **Linear Advance:** en PrusaSlicer y Orca, cada filamento trae `;M900 K0.0` comentado en su gcode de inicio. Calibrá el K, descomentá la línea y poné tu valor. Con Linear Advance calibrado, la retracción probablemente baje a 3–4 mm.
- **Largo del 2 en 1:** si al cambiar de color el filamento nuevo no entra, subí `largo` en `CAMBIO` (dentro de `generar_perfiles.py`) a 105–110 y regenerá. Si al cargar sale un chorro grande, bajalo.
- **Comprobación:** `pruebas/verificar-perfiles.py` revisa más de 500 puntos:
  - que cada ajuste exista en Cura y que el valor esté dentro de los límites de Cura 5.10;
  - que las calidades estén completas;
  - que lo que se retira coincida con lo que se carga;
  - que todo coincida con el firmware.

  No pude abrir los programas desde acá. Si alguno muestra un aviso al importar, avisá qué dice.
