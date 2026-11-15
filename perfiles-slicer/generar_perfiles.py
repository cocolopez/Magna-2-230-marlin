#!/usr/bin/env python3
"""
Genera los perfiles de slicer para las Hellbot Magna 2 (230, y sin probar 300, 400, 400D, 500 y 500D)
con el firmware Marlin de este repo. Los nombres de abajo son los de la 230; los otros modelos usan su número.

Salida (en esta misma carpeta):
  cura/definitions/hellbot_magna2_230_marlin.def.json
  cura/extruders/hellbot_magna2_230_marlin_extruder_0.def.json
  cura/extruders/hellbot_magna2_230_marlin_extruder_1.def.json
  cura/quality/hellbot_magna2_230_marlin/*.inst.cfg   (calidades propias por material)
  prusaslicer/Magna2-230_PrusaSlicer_bundle.ini
  orcaslicer/machine|process|filament/*.json
  gcode-utiles/*.gcode                                  (estacionar / cargar filamentos)

Todos los valores salen de un único lugar (MAQUINA, CAMBIO, PROCESOS, FILAMENTOS)
para que los tres slicers queden coherentes entre sí y con el firmware.

Uso: python3 generar_perfiles.py
"""
import json
import os
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- modelos
# Valores de cada Magna 2. Los de 300/400/500 salen de los firmware oficiales de Hellbot (ver
# docs-magna/MODELOS.md) y NO están probados en una máquina real: solo existe la 230 acá.
#   estacionar: mm que sube cada filamento en el hotend 2 en 1 (por encima de la unión en Y).
#     Bowden: 100 (perfil oficial de Hellbot para la 230). Directo (D): 60, SIN MEDIR: con 100 el
#     filamento saldría de los engranajes del extrusor, que están arriba del hotend.
#   retr: retracción. Bowden 5 mm; directo 1 mm.
MODELOS = {
    "230":  dict(xy=230, z=250, vxy=300, vz=5, axy=2000, cama_max=110, estacionar=100, retr=5.0, retr_petg=1.0, vel_retr=25, probado=True),
    "300":  dict(xy=300, z=400, vxy=200, vz=4, axy=800, cama_max=100, estacionar=100, retr=5.0, retr_petg=1.0, vel_retr=25, probado=False),
    "400":  dict(xy=400, z=400, vxy=100, vz=5, axy=200, cama_max=85, estacionar=100, retr=5.0, retr_petg=1.0, vel_retr=25, probado=False),
    "400D": dict(xy=400, z=400, vxy=100, vz=5, axy=200, cama_max=85, estacionar=60, retr=1.0, retr_petg=0.5, vel_retr=30, probado=False),
    "500":  dict(xy=500, z=500, vxy=100, vz=5, axy=200, cama_max=85, estacionar=100, retr=5.0, retr_petg=1.0, vel_retr=25, probado=False),
    "500D": dict(xy=500, z=500, vxy=100, vz=5, axy=200, cama_max=85, estacionar=60, retr=1.0, retr_petg=0.5, vel_retr=30, probado=False),
}


def configurar(modelo):
    """Arma todos los valores de un modelo (las funciones de abajo los leen de acá)."""
    global ID, MOD, MAQUINA, CAMBIO, INICIO_COMUN, FIN_COMUN, PROCESOS, VIAJE, ACEL_IMPRESION, ACEL_PERIM_EXT
    global ACEL_VIAJE, ACEL_1RA, FILAMENTOS, CARGA_INICIAL, ESTACIONAR_FINAL, CURA_ID, ARCH
    ID = modelo
    MOD = MODELOS[modelo]
    CURA_ID = f"hellbot_magna2_{modelo.lower()}_marlin"
    ARCH = f"Magna2-{modelo}"   # para nombres de archivo
    # ---------------------------------------------------------------- máquina
    MAQUINA = dict(
        nombre=f"Hellbot Magna 2 {ID} Marlin 2.1" + ("" if MOD["probado"] else " (sin probar)"),
        ancho=MOD["xy"], profundo=MOD["xy"], alto=MOD["z"],
        boquilla=0.4, diametro=1.75,
        extrusores=2,                  # doble extrusor, hotend 2 en 1 (una sola boquilla)
        # límites = los del firmware (Configuration.h). E máx 25 mm/s: ninguna retracción puede ir más rápido.
        vmax=dict(x=MOD["vxy"], y=MOD["vxy"], z=MOD["vz"], e=25),
        amax=dict(x=MOD["axy"], y=MOD["axy"], z=100, e=8000),
        jerk=dict(x=10, y=10, z=0.3, e=5),
    )

    # ---------------------------------------------------------------- cambio de filamento 2 en 1
    # El hotend 2 en 1 tiene una unión en Y: para que entre el otro filamento, el activo tiene que
    # subir por encima de la unión. Hellbot usa 100-105 mm en su perfil oficial de Cura
    # (hellbot_magna_2_230_dual: "G1 E-5" + "G1 E-100"). Acá usamos 100 mm en total.
    #
    # Lo hace el SLICER (como el perfil de fábrica), no el firmware: Marlin solo retira el filamento
    # viejo si ya lo "cebó" él mismo en esa sesión, así que el primer T0 -> T1 después de prender la
    # máquina no retiraba T0. Por eso todos los gcode de inicio mandan M217 S0 (apaga el cambio del
    # firmware aunque la EEPROM tenga guardado otro valor).
    #
    # Estado de reposo: LOS DOS filamentos estacionados 100 mm arriba de la punta de la boquilla.
    # Cada impresión los carga cuando los usa y los vuelve a estacionar al terminar.
    CAMBIO = dict(
        largo=MOD["estacionar"],  # mm desde la punta de la boquilla hasta la posición de estacionado
        retraccion_corta=6, # mm que retrae el slicer en el lugar antes de ir a la esquina (Hellbot: 6)
        velocidad=25,       # mm/s (límite E del firmware)
        esquina=(MOD["xy"] - 5, 5),  # X, Y donde descarga/carga (adelante a la derecha, lejos de la torre)
    )
    CAMBIO["resto"] = CAMBIO["largo"] - CAMBIO["retraccion_corta"]

    INICIO_COMUN = [
        f"; --- Magna 2 {ID} inicio ---",
        "; Antes de imprimir: los dos filamentos estacionados (asi quedan al terminar cada impresion).",
        "; Si cargaste filamento a mano hasta la boquilla, corre gcode-utiles/estacionar_T0.gcode o _T1.",
        "M217 S0 ; el cambio 2 en 1 lo hace el slicer, no el firmware",
        "G90 ; absoluto",
        "M82 ; extrusor absoluto",
        "M140 S{BED0} ; cama",
        "M104 S{TEMP0} ; hotend (sin esperar)",
        "G28 ; home",
        "M190 S{BED0}",
        "M109 S{TEMP0}",
        "G92 E0",
        "G1 Z5 F600",
        "; --- fin inicio ---",
    ]
    FIN_COMUN = [
        f"; --- Magna 2 {ID} fin ---",
        "G91 ; relativo",
        "G1 Z10 F600 ; subir",
        "G90",
        f"G1 X0 Y{MOD['xy'] - 10} F3000 ; presentar la pieza",
        "M106 S0 ; ventilador off",
        "M104 S0 ; hotend off",
        "M140 S0 ; cama off",
        "M84 X Y E ; motores off (Z queda trabado)",
        "; --- fin ---",
    ]


    # ---------------------------------------------------------------- procesos
    # Hellbot recomienda 50 mm/s (80 máx.) para la Magna 2 230. Con Input Shaping y MPC del
    # firmware se puede ir un poco más rápido en relleno; los perímetros externos se mantienen
    # lentos porque es un bowden largo con unión 2 en 1.
    PROCESOS = [
        dict(q="fine", peso=1, id="0.12 Fina", capa=0.12, perim=3, top=7, bottom=5, relleno=15,
             v=40, v_ext=25, v_int=40, v_relleno=55, v_1ra=20),
        dict(q="standard", peso=0, id="0.16 Estandar", capa=0.16, perim=3, top=6, bottom=5, relleno=15,
             v=50, v_ext=30, v_int=45, v_relleno=60, v_1ra=20),
        dict(q="normal", peso=-1, id="0.20 Normal", capa=0.20, perim=3, top=5, bottom=4, relleno=15,
             v=50, v_ext=30, v_int=50, v_relleno=65, v_1ra=20),
        dict(q="draft", peso=-2, id="0.28 Rapida", capa=0.28, perim=2, top=4, bottom=3, relleno=12,
             v=60, v_ext=35, v_int=55, v_relleno=75, v_1ra=20),
    ]
    VIAJE = min(150, MOD["vxy"])
    ACEL_IMPRESION = min(1500, MOD["axy"])
    ACEL_PERIM_EXT = min(1000, MOD["axy"])
    ACEL_VIAJE = min(2000, MOD["axy"])
    ACEL_1RA = min(800, MOD["axy"])

    # ---------------------------------------------------------------- filamentos
    # retr = retracción bowden normal (rango típico 3-6 mm); vel_max = tope de velocidad del material
    FILAMENTOS = [
        dict(id="PLA", tipo="PLA", cura="generic_pla", temp=205, temp0=210, cama=60, cama0=65,
             fan_min=100, fan_max=100, fan_desde=2, densidad=1.24, retr=MOD["retr"], vel_retr=MOD["vel_retr"], vel_max=None,
             capa_min=8),
        dict(id="PETG", tipo="PETG", cura="generic_petg", temp=235, temp0=240, cama=75, cama0=80,
             fan_min=30, fan_max=50, fan_desde=3, densidad=1.27, retr=MOD["retr"] + MOD["retr_petg"], vel_retr=MOD["vel_retr"], vel_max=45,
             capa_min=10),
        dict(id="ABS", tipo="ABS", cura="generic_abs", temp=240, temp0=245, cama=min(100, MOD["cama_max"]), cama0=min(105, MOD["cama_max"]),
             fan_min=0, fan_max=15, fan_desde=3, densidad=1.04, retr=MOD["retr"], vel_retr=MOD["vel_retr"], vel_max=50,
             capa_min=12),
    ]


    # carga del primer filamento (PrusaSlicer/Orca) y estacionado del último al terminar
    CARGA_INICIAL = [
        "T[initial_tool]",
        "; carga el primer filamento desde la posicion de estacionado y purga",
        "G92 E0",
        f"G1 E{CAMBIO['largo']} F{CAMBIO['velocidad'] * 60}",
        "G92 E0",
        "G1 X5 Y20 Z0.3 F5000",
        "G1 X5 Y200 Z0.3 F1500 E15 ; linea de purga",
        "G1 X5.4 Y200 Z0.3 F5000",
        "G1 X5.4 Y20 Z0.3 F1500 E30 ; segunda linea",
        "G92 E0",
        "G1 Z2.0 F600",
    ]
    ESTACIONAR_FINAL = [
        "; estaciona el ultimo filamento arriba de la union 2 en 1",
        "G92 E0",
        f"G1 E-{CAMBIO['largo']} F{CAMBIO['velocidad'] * 60}",
        "G92 E0",
    ]



def cargar(n, previa=0):
    """Baja el filamento n desde la posición de estacionado. 'previa' = lo que después
    des-retrae el propio slicer (así el total siempre es CAMBIO['largo'])."""
    x, y = CAMBIO["esquina"]
    return [
        f"; --- cargar T{n} (hotend 2 en 1) ---",
        f"G1 X{x} Y{y} F6000 ; esquina de cambio",
        "G92 E0",
        f"G1 E{CAMBIO['largo'] - previa} F{CAMBIO['velocidad'] * 60} ; baja desde la union",
        "G92 E0",
        "G91", "G1 Z-1 F600 ; vuelve a la altura (sube 1 mm al estacionar)", "G90",
    ]


def descargar(n, previa=0):
    """Estaciona el filamento n arriba de la unión. 'previa' = lo que ya retrajo el slicer."""
    x, y = CAMBIO["esquina"]
    return [
        f"; --- estacionar T{n} (hotend 2 en 1) ---",
        "G91", "G1 Z1 F600 ; despega la boquilla de la pieza", "G90",
        f"G1 X{x} Y{y} F6000 ; esquina de cambio",
        "G92 E0",
        f"G1 E-{CAMBIO['largo'] - previa} F{CAMBIO['velocidad'] * 60} ; sube por encima de la union",
        "G92 E0",
    ]


def gcode(lineas, temp0, bed0):
    return "\n".join(lineas).replace("{TEMP0}", temp0).replace("{BED0}", bed0)


def escribir(ruta, contenido):
    ruta = os.path.join(AQUI, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fin_linea = "\r\n" if ruta.endswith(".bat") else "\n"  # cmd.exe necesita CRLF
    with open(ruta, "w", encoding="utf-8", newline=fin_linea) as f:
        f.write(contenido)
    print("  ", os.path.relpath(ruta, AQUI))



# ================================================================== CURA
CURA_SETTING_VERSION = 25   # Cura 5.10 / 5.11. Cura 5.12+ lo actualiza solo al cargarlo.


def cura_quality(nombre, archivo, quality_type, peso, valores, material=None):
    meta = [
        "[general]",
        "version = 4",
        f"name = {nombre}",
        f"definition = {CURA_ID}",
        "",
        "[metadata]",
        f"setting_version = {CURA_SETTING_VERSION}",
        "type = quality",
        f"quality_type = {quality_type}",
        f"weight = {peso}",
    ]
    meta.append(f"material = {material}" if material else "global_quality = True")
    meta += ["", "[values]"]
    meta += [f"{k} = {v}" for k, v in valores.items()]
    escribir(f"cura/quality/{CURA_ID}/{archivo}.inst.cfg", "\n".join(meta) + "\n")


def cura():
    m = MAQUINA
    c = CAMBIO
    # limpiar calidades viejas para no dejar archivos huérfanos
    # (las calidades viejas se borran una sola vez en __main__, antes de generar todos los modelos)

    inicio = [
        f"; --- Magna 2 {ID} (Marlin 2.1) inicio ---",
        ";  Antes de imprimir: los DOS filamentos estacionados 100 mm arriba de la boquilla",
        ";  (asi quedan solos al terminar cada impresion). Si cargaste uno a mano hasta la",
        ";  boquilla, imprimi primero gcode-utiles/estacionar_T0.gcode (o _T1).",
        "M217 S0 ; el cambio 2 en 1 lo hace Cura, no el firmware",
        "G90",
        "M82",
        "M140 S{material_bed_temperature_layer_0}",
        "M104 T0 S{material_print_temperature_layer_0, initial_extruder_nr}",
        "M104 T1 S{material_print_temperature_layer_0, initial_extruder_nr}",
        "G28 ; home",
        "M190 S{material_bed_temperature_layer_0}",
        "M109 S{material_print_temperature_layer_0, initial_extruder_nr}",
        "G92 E0",
        "G1 Z5 F600",
        "; Cura carga el primer filamento (gcode de inicio del extrusor) y purga con el skirt",
        "; --- fin inicio ---",
    ]
    fin = list(FIN_COMUN)
    fin.insert(1, "; (Cura ya estaciono el ultimo filamento con el gcode final del extrusor)")

    defin = {
        "version": 2,
        "name": m["nombre"],
        "inherits": "fdmprinter",
        "metadata": {
            "visible": True,
            "author": f"Magna 2 {ID} Marlin",
            "manufacturer": "Hellbot",
            "file_formats": "text/x-gcode",
            # (la cama y la textura de la 230 se agregan abajo: Cura las trae para la 230 oficial)
            "has_materials": True,
            "has_machine_quality": True,
            "preferred_quality_type": "normal",
            "preferred_material": "generic_pla",
            "quality_definition": CURA_ID,
            "machine_extruder_trains": {"0": CURA_ID + "_extruder_0", "1": CURA_ID + "_extruder_1"},
        },
        "overrides": {
            "machine_name": {"default_value": m["nombre"]},
            "machine_width": {"default_value": m["ancho"]},
            "machine_depth": {"default_value": m["profundo"]},
            "machine_height": {"default_value": m["alto"]},
            "machine_heated_bed": {"default_value": True},
            "machine_center_is_zero": {"default_value": False},
            "machine_gcode_flavor": {"default_value": "RepRap (Marlin/Sprinter)"},
            "machine_extruder_count": {"default_value": 2},
            "machine_extruders_share_heater": {"default_value": True},
            "machine_extruders_share_nozzle": {"default_value": True},
            # Cura arranca suponiendo cada filamento retraído c['retraccion_corta'] mm y des-retrae
            # eso solo; el resto (c['resto']) lo baja el gcode de inicio del extrusor.
            "machine_extruders_shared_nozzle_initial_retraction": {"default_value": c["retraccion_corta"]},
            "machine_max_feedrate_x": {"default_value": m["vmax"]["x"]},
            "machine_max_feedrate_y": {"default_value": m["vmax"]["y"]},
            "machine_max_feedrate_z": {"default_value": m["vmax"]["z"]},
            "machine_max_feedrate_e": {"default_value": m["vmax"]["e"]},
            "machine_max_acceleration_x": {"default_value": m["amax"]["x"]},
            "machine_max_acceleration_y": {"default_value": m["amax"]["y"]},
            "machine_max_acceleration_z": {"default_value": m["amax"]["z"]},
            "machine_max_acceleration_e": {"default_value": m["amax"]["e"]},
            "machine_max_jerk_xy": {"default_value": m["jerk"]["x"]},
            "machine_max_jerk_z": {"default_value": m["jerk"]["z"]},
            "machine_max_jerk_e": {"default_value": m["jerk"]["e"]},
            "machine_acceleration": {"default_value": ACEL_IMPRESION},
            "machine_start_gcode": {"default_value": "\n".join(inicio)},
            "machine_end_gcode": {"default_value": gcode(fin, "0", "0")},
            "material_diameter": {"default_value": m["diametro"]},

            # ---- valores por defecto de impresión (las calidades ajustan capa y velocidades)
            "layer_height_0": {"value": 0.2},
            "line_width": {"value": "machine_nozzle_size"},
            "wall_line_count": {"value": 3},
            "optimize_wall_printing_order": {"value": True},
            "z_seam_type": {"value": "'sharpest_corner'"},
            "z_seam_corner": {"value": "'z_seam_corner_weighted'"},
            "infill_pattern": {"value": "'gyroid'"},
            "infill_sparse_density": {"value": 15},
            "infill_before_walls": {"value": False},
            "speed_travel": {"value": VIAJE},
            "speed_layer_0": {"value": 20},
            "speed_travel_layer_0": {"value": 100},
            "speed_print_layer_0": {"value": "speed_layer_0"},
            "skirt_brim_speed": {"value": "speed_layer_0"},
            "acceleration_enabled": {"value": True},
            "acceleration_print": {"value": ACEL_IMPRESION},
            "acceleration_wall_0": {"value": ACEL_PERIM_EXT},
            "acceleration_travel": {"value": ACEL_VIAJE},
            "acceleration_layer_0": {"value": ACEL_1RA},
            "acceleration_travel_layer_0": {"value": ACEL_VIAJE},
            "jerk_enabled": {"value": False},          # el firmware usa su jerk clásico
            "retraction_enable": {"value": True},
            "retraction_amount": {"value": 5},
            "retraction_speed": {"value": 25},
            "retraction_retract_speed": {"value": 25},
            "retraction_prime_speed": {"value": 25},
            "retraction_min_travel": {"value": 1.5},
            "retraction_count_max": {"value": 20},
            "retraction_extrusion_window": {"value": "retraction_amount"},
            "retraction_hop_enabled": {"value": False},
            "retraction_combing": {"value": "'noskin'"},
            "retraction_combing_max_distance": {"value": 30},
            "travel_avoid_other_parts": {"value": True},
            "travel_avoid_distance": {"value": 1},
            "cool_fan_enabled": {"value": True},
            "cool_min_layer_time": {"value": 8},
            "cool_min_speed": {"value": 15},
            "support_angle": {"value": 55},
            "support_z_distance": {"value": "layer_height"},
            "adhesion_type": {"value": "'skirt'"},
            "skirt_line_count": {"value": 3},
            "skirt_gap": {"value": 5},
            "skirt_brim_minimal_length": {"value": 300},
            "brim_width": {"value": 6},
            # ---- doble extrusión 2 en 1
            "switch_extruder_retraction_amount": {"value": c["retraccion_corta"]},
            "switch_extruder_retraction_speeds": {"value": c["velocidad"]},
            "switch_extruder_retraction_speed": {"value": c["velocidad"]},
            "switch_extruder_prime_speed": {"value": c["velocidad"]},
            "retraction_hop_after_extruder_switch": {"value": True},
            "retraction_hop_after_extruder_switch_height": {"value": 1},
            "prime_tower_enable": {"value": True},
            "prime_tower_size": {"value": 25},
            "prime_tower_min_volume": {"value": 60},
            "prime_tower_position_x": {"value": "machine_width - 30"},
            "prime_tower_position_y": {"value": "machine_depth - 30"},
            "ooze_shield_enabled": {"value": False},
        },
    }
    if ID == "230":
        defin["metadata"].update({"platform": "Hellbot_Magna_2_230.obj", "platform_texture": "Magna2_230.png",
                                  "has_textured_buildplate": True})
    escribir(f"cura/definitions/{CURA_ID}.def.json", json.dumps(defin, indent=2, ensure_ascii=False))

    for n in range(2):
        ext = {
            "version": 2,
            "name": f"Extrusor {n + 1}",
            "inherits": "fdmextruder",
            "metadata": {"machine": CURA_ID, "position": str(n)},
            "overrides": {
                "extruder_nr": {"default_value": n, "maximum_value": "1"},
                "machine_nozzle_size": {"default_value": m["boquilla"]},
                "material_diameter": {"default_value": m["diametro"]},
                "machine_nozzle_offset_x": {"default_value": 0.0},
                "machine_nozzle_offset_y": {"default_value": 0.0},
                # Cura usa esto cada vez que activa este extrusor (también el primero de la impresión)
                "machine_extruder_start_code": {"default_value": "\n".join(cargar(n, previa=c["retraccion_corta"]))},
                # ... y esto cada vez que lo deja (también al terminar la impresión)
                "machine_extruder_end_code": {"default_value": "\n".join(descargar(n, previa=c["retraccion_corta"]))},
                "machine_extruder_start_code_duration": {"default_value": round(c["resto"] / c["velocidad"] + 2)},
                "machine_extruder_end_code_duration": {"default_value": round(c["resto"] / c["velocidad"] + 2)},
            },
        }
        escribir(f"cura/extruders/{CURA_ID}_extruder_{n}.def.json", json.dumps(ext, indent=2, ensure_ascii=False))

    # ---- calidades globales: altura de capa y cantidades de paredes/capas
    nombres = {"fine": "Fina 0.12", "standard": "Estandar 0.16", "normal": "Normal 0.20", "draft": "Rapida 0.28"}
    for p in PROCESOS:
        cura_quality(nombres[p["q"]], f"{CURA_ID}_global_{p['q']}", p["q"], p["peso"], {
            "layer_height": p["capa"],
            "layer_height_0": 0.2,
            "wall_line_count": p["perim"],
            "top_layers": p["top"],
            "bottom_layers": p["bottom"],
            "infill_sparse_density": p["relleno"],
            "support_interface_height": "=layer_height * 4",
        })
    # ---- calidades por material: temperaturas, ventilador, retracción y velocidades
    for f in FILAMENTOS:
        for p in PROCESOS:
            tope = f["vel_max"] or 999
            vals = {
                "material_print_temperature": f["temp"],
                "material_print_temperature_layer_0": f["temp0"],
                "material_initial_print_temperature": "=material_print_temperature - 5",
                "material_final_print_temperature": "=material_print_temperature - 5",
                "material_bed_temperature": f["cama"],
                "material_bed_temperature_layer_0": f["cama0"],
                "cool_fan_speed_min": f["fan_min"],
                "cool_fan_speed_max": f["fan_max"],
                "cool_fan_full_layer": f["fan_desde"],
                "cool_min_layer_time": f["capa_min"],
                "retraction_amount": f["retr"],
                "retraction_speed": f["vel_retr"],
                "speed_print": min(p["v"], tope),
                "speed_infill": min(p["v_relleno"], tope),
                "speed_wall_0": min(p["v_ext"], tope),
                "speed_wall_x": min(p["v_int"], tope),
                "speed_topbottom": min(p["v_ext"] + 5, tope),
                "speed_support": min(p["v"], tope),
                "speed_layer_0": p["v_1ra"],
            }
            if f["tipo"] == "ABS":
                vals["cool_fan_enabled"] = "=cool_fan_speed_max > 0"
            nombre = nombres[p["q"]]
            cura_quality(nombre, f"{CURA_ID}_{f['id'].lower()}_{p['q']}", p["q"], p["peso"], vals,
                         material=f["cura"])

    # ---- instaladores
    escribir("cura/instalar-windows.bat", INSTALAR_BAT)
    escribir("cura/instalar-mac-linux.sh", INSTALAR_SH)
    os.chmod(os.path.join(AQUI, "cura/instalar-mac-linux.sh"), 0o755)


INSTALAR_BAT = r"""@echo off
rem Instala los perfiles "Hellbot Magna 2 ... Marlin 2.1" (230, 300, 400, 400D, 500, 500D) en la version MAS NUEVA de Cura instalada.
rem Cerra Cura antes de correrlo. Abri Cura al menos una vez despues de instalarlo/actualizarlo.
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$base = Join-Path $env:APPDATA 'cura';" ^
  "if (-not (Test-Path $base)) { Write-Host 'No encontre la carpeta de Cura. Abri Cura una vez y volve a correr esto.'; exit 1 };" ^
  "$v = Get-ChildItem $base -Directory | Where-Object { $_.Name -match '^\d+\.\d+$' } | Sort-Object { [version]$_.Name } | Select-Object -Last 1;" ^
  "if (-not $v) { Write-Host 'No encontre ninguna version de Cura en' $base; exit 1 };" ^
  "$d = $v.FullName; Write-Host 'Instalando en' $d;" ^
  "New-Item -ItemType Directory -Force (Join-Path $d 'definitions'),(Join-Path $d 'extruders'),(Join-Path $d 'quality') | Out-Null;" ^
  "Copy-Item 'definitions\*.def.json' (Join-Path $d 'definitions') -Force;" ^
  "Copy-Item 'extruders\*.def.json' (Join-Path $d 'extruders') -Force;" ^
  "Copy-Item 'quality\*' (Join-Path $d 'quality') -Recurse -Force;" ^
  "Write-Host 'Listo. Abri Cura > Agregar impresora > No conectada en red > Hellbot > Hellbot Magna 2 (tu modelo) Marlin 2.1'"
pause
"""

INSTALAR_SH = r"""#!/bin/sh
# Instala los perfiles "Hellbot Magna 2 ... Marlin 2.1" (230, 300, 400, 400D, 500, 500D) en la version MAS NUEVA de Cura.
# Cerra Cura antes de correrlo. Uso: sh instalar-mac-linux.sh
set -e
cd "$(dirname "$0")"
for base in "$HOME/Library/Application Support/cura" "$HOME/.local/share/cura" \
            "$HOME/.var/app/com.ultimaker.cura/data/cura"; do
  [ -d "$base" ] || continue
  v=$(ls "$base" | grep -E '^[0-9]+\.[0-9]+$' | sort -t. -k1,1n -k2,2n | tail -n 1)
  [ -n "$v" ] || continue
  d="$base/$v"
  echo "Instalando en $d"
  mkdir -p "$d/definitions" "$d/extruders" "$d/quality"
  cp definitions/*.def.json "$d/definitions/"
  cp extruders/*.def.json "$d/extruders/"
  cp -R quality/* "$d/quality/"
  echo "Listo. Abri Cura > Agregar impresora > No conectada en red > Hellbot > Hellbot Magna 2 (tu modelo) Marlin 2.1"
  exit 0
done
echo "No encontre la carpeta de configuracion de Cura. Abri Cura una vez y volve a correr esto."
exit 1
"""


# ================================================================== GCODE UTILES
def utiles():
    t = 210
    for n in range(2):
        cab = [f"; Magna 2 {ID} - utilidad para T{n}", "M217 S0 ; cambio 2 en 1 manual", f"M109 S{t} ; PLA (subi a 235-240 para PETG/ABS)",
               f"T{n}", "G90", "M82"]
        pie = ["M104 S0", "M84 E", "; fin"]
        carpeta = "gcode-utiles" if ID == "230" else f"gcode-utiles/{ARCH}"
        escribir(f"{carpeta}/estacionar_T{n}.gcode", "\n".join(
            cab + [f"; Usalo cuando el filamento T{n} llega hasta la boquilla (por ejemplo, recien cargado).",
                   "G92 E0", f"G1 E-{CAMBIO['largo']} F{CAMBIO['velocidad'] * 60} ; sube {CAMBIO['largo']} mm, por encima de la union",
                   "G92 E0"] + pie) + "\n")
        escribir(f"{carpeta}/cargar_T{n}.gcode", "\n".join(
            cab + [f"; Baja T{n} desde la posicion de estacionado y purga un poco.",
                   "; El OTRO filamento tiene que estar estacionado.",
                   "G92 E0", f"G1 E{CAMBIO['largo']} F{CAMBIO['velocidad'] * 60}",
                   "G1 E120 F180 ; purga 20 mm", "G92 E0"] + pie) + "\n")


# ================================================================== PRUSASLICER
def ini_val(v):
    return str(v).replace("\n", "\\n")


def prusa():
    m = MAQUINA
    two = lambda v: f"{v},{v}"
    out = [f"# Bundle PrusaSlicer - Hellbot Magna 2 {ID} (Marlin 2.1)" + ("" if MOD["probado"] else " - SIN PROBAR en una maquina real"),
           "# Importar: Archivo > Importar > Importar paquete de configuracion (Import Config Bundle)", ""]
    pname = f"Magna 2 {ID} Marlin 2.1"
    printer = {
        "printer_technology": "FFF",
        "printer_model": "",
        "bed_shape": f"0x0,{m['ancho']}x0,{m['ancho']}x{m['profundo']},0x{m['profundo']}",
        "max_print_height": m["alto"],
        "gcode_flavor": "marlin2",
        "use_relative_e_distances": 0,
        "nozzle_diameter": two(m["boquilla"]),
        "extruder_offset": "0x0,0x0",
        "extruder_colour": "#FF8000;#2080FF",
        "single_extruder_multi_material": 1,
        "cooling_tube_length": 10,
        "cooling_tube_retraction": 20,
        "parking_pos_retraction": CAMBIO["largo"],  # descarga total en cada cambio (2 en 1)
        "extra_loading_move": -2,
        "single_extruder_multi_material_priming": 0,
        "high_current_on_filament_swap": 0,
        "retract_length": two(FILAMENTOS[0]["retr"]),
        "retract_speed": two(FILAMENTOS[0]["vel_retr"]),
        "deretract_speed": two(0),
        "retract_lift": two(0.2),
        "retract_lift_below": two(m["alto"] - 1),
        "retract_length_toolchange": two(0),
        "retract_restart_extra_toolchange": two(0),
        "wipe": two(0),
        "machine_limits_usage": "emit_to_gcode",
        "machine_max_feedrate_x": m["vmax"]["x"], "machine_max_feedrate_y": m["vmax"]["y"],
        "machine_max_feedrate_z": m["vmax"]["z"], "machine_max_feedrate_e": m["vmax"]["e"],
        "machine_max_acceleration_x": m["amax"]["x"], "machine_max_acceleration_y": m["amax"]["y"],
        "machine_max_acceleration_z": m["amax"]["z"], "machine_max_acceleration_e": m["amax"]["e"],
        "machine_max_acceleration_extruding": m["amax"]["x"],
        "machine_max_acceleration_retracting": m["amax"]["x"],
        "machine_max_acceleration_travel": m["amax"]["x"],
        "machine_max_jerk_x": m["jerk"]["x"], "machine_max_jerk_y": m["jerk"]["y"],
        "machine_max_jerk_z": m["jerk"]["z"], "machine_max_jerk_e": m["jerk"]["e"],
        "remaining_times": 1,          # M73 (SET_PROGRESS_MANUALLY en el firmware)
        "start_gcode": ini_val(gcode(INICIO_COMUN + CARGA_INICIAL, "[first_layer_temperature[initial_tool]]", "[first_layer_bed_temperature[initial_tool]]")),
        "end_gcode": ini_val(gcode(ESTACIONAR_FINAL + FIN_COMUN, "0", "0")),
        "toolchange_gcode": "T[next_extruder] ; la torre de purga descarga/carga el filamento (2 en 1)",
    }
    out.append(f"[printer:{pname}]")
    out += [f"{k} = {v}" for k, v in printer.items()]
    out.append("")
    for p in PROCESOS:
        out.append(f"[print:{p['id']} - Magna 2 {ID}]")
        cfg = {
            "layer_height": p["capa"], "first_layer_height": 0.2,
            "perimeters": p["perim"], "top_solid_layers": p["top"], "bottom_solid_layers": p["bottom"],
            "fill_density": f"{p['relleno']}%", "fill_pattern": "grid",
            "perimeter_speed": p["v_int"], "external_perimeter_speed": p["v_ext"],
            "infill_speed": p["v_relleno"], "solid_infill_speed": p["v_relleno"] - 10,
            "top_solid_infill_speed": p["v_ext"] + 5, "travel_speed": VIAJE, "first_layer_speed": p["v_1ra"],
            "default_acceleration": ACEL_IMPRESION, "perimeter_acceleration": 1000,
            "infill_acceleration": ACEL_IMPRESION, "travel_acceleration": ACEL_VIAJE,
            "first_layer_acceleration": 800,
            "skirts": 2, "skirt_distance": 3,
            "wipe_tower": 1, "wipe_tower_x": 170, "wipe_tower_y": 170, "wipe_tower_width": 40,
            "wipe_tower_rotation_angle": 0,
            "gcode_label_objects": "firmware",   # M486 (CANCEL_OBJECTS)
            "avoid_crossing_perimeters": 0,
        }
        out += [f"{k} = {v}" for k, v in cfg.items()]
        out.append("")
    for f in FILAMENTOS:
        out.append(f"[filament:{f['id']} - Magna 2 {ID}]")
        cfg = {
            "filament_type": f["tipo"], "filament_diameter": m["diametro"], "filament_density": f["densidad"],
            "temperature": f["temp"], "first_layer_temperature": f["temp0"],
            "bed_temperature": f["cama"], "first_layer_bed_temperature": f["cama0"],
            "fan_always_on": 1 if f["fan_min"] > 0 else 0, "cooling": 1,
            "min_fan_speed": f["fan_min"], "max_fan_speed": f["fan_max"], "disable_fan_first_layers": f["fan_desde"] - 1,
            "filament_cooling_moves": 0, "filament_load_time": 0, "filament_unload_time": 0,
            "filament_unloading_speed": CAMBIO["velocidad"], "filament_unloading_speed_start": CAMBIO["velocidad"],
            "filament_loading_speed": 20, "filament_loading_speed_start": 20,
            "retract_length": f["retr"], "retract_speed": f["vel_retr"],
            "max_volumetric_speed": 10 if f["tipo"] == "PLA" else 8,
            "start_filament_gcode": ini_val("; Linear Advance: descomentar y poner tu K calibrado\n;M900 K0.0"),
        }
        out += [f"{k} = {v}" for k, v in cfg.items()]
        out.append("")
    out += ["[presets]", f"printer = {pname}", f"print = 0.20 Normal - Magna 2 {ID}", f"filament = PLA - Magna 2 {ID}", ""]
    escribir(f"prusaslicer/{ARCH}_PrusaSlicer_bundle.ini", "\n".join(out))


# ================================================================== ORCASLICER
def orca():
    m = MAQUINA
    two = lambda v: [str(v), str(v)]
    mname = f"Magna 2 {ID} Marlin 2.1 0.4"
    machine = {
        "type": "machine", "name": mname, "from": "User", "inherits": "",
        "printer_settings_id": mname, "printer_technology": "FFF", "version": "2.1.0.0",
        "printable_area": ["0x0", f"{m['ancho']}x0", f"{m['ancho']}x{m['profundo']}", f"0x{m['profundo']}"],
        "printable_height": str(m["alto"]),
        "gcode_flavor": "marlin2",
        "nozzle_diameter": two(m["boquilla"]),
        "extruder_offset": ["0x0", "0x0"],
        "extruder_colour": ["#FF8000", "#2080FF"],
        "single_extruder_multi_material": "1",
        "cooling_tube_length": "10", "cooling_tube_retraction": "20", "parking_pos_retraction": str(CAMBIO["largo"]),
        "extra_loading_move": "-2", "high_current_on_filament_swap": "0",
        "retraction_length": two(FILAMENTOS[0]["retr"]), "retraction_speed": two(FILAMENTOS[0]["vel_retr"]),
        "deretraction_speed": two(0), "z_hop": two(0.2),
        "retract_length_toolchange": two(0), "retract_restart_extra_toolchange": two(0),
        "emit_machine_limits_to_gcode": "1",
        "machine_max_speed_x": [str(m["vmax"]["x"])], "machine_max_speed_y": [str(m["vmax"]["y"])],
        "machine_max_speed_z": [str(m["vmax"]["z"])], "machine_max_speed_e": [str(m["vmax"]["e"])],
        "machine_max_acceleration_x": [str(m["amax"]["x"])], "machine_max_acceleration_y": [str(m["amax"]["y"])],
        "machine_max_acceleration_z": [str(m["amax"]["z"])], "machine_max_acceleration_e": [str(m["amax"]["e"])],
        "machine_max_acceleration_extruding": [str(m["amax"]["x"])],
        "machine_max_acceleration_retracting": [str(m["amax"]["x"])],
        "machine_max_acceleration_travel": [str(m["amax"]["x"])],
        "machine_max_jerk_x": [str(m["jerk"]["x"])], "machine_max_jerk_y": [str(m["jerk"]["y"])],
        "machine_max_jerk_z": [str(m["jerk"]["z"])], "machine_max_jerk_e": [str(m["jerk"]["e"])],
        "machine_start_gcode": gcode(INICIO_COMUN + CARGA_INICIAL, "[nozzle_temperature_initial_layer]", "[bed_temperature_initial_layer_single]"),
        "machine_end_gcode": gcode(ESTACIONAR_FINAL + FIN_COMUN, "0", "0"),
        "change_filament_gcode": "T[next_extruder] ; la torre de purga descarga/carga el filamento (2 en 1)",
        "use_relative_e_distances": "0",
    }
    escribir(f"orcaslicer/machine/{ARCH}_machine.json", json.dumps(machine, indent=2, ensure_ascii=False))
    for p in PROCESOS:
        name = f"{p['id']} - Magna 2 {ID}"
        proc = {
            "type": "process", "name": name, "from": "User", "inherits": "",
            "print_settings_id": name, "version": "2.1.0.0",
            "compatible_printers": [mname],
            "layer_height": str(p["capa"]), "initial_layer_print_height": "0.2",
            "wall_loops": str(p["perim"]), "top_shell_layers": str(p["top"]), "bottom_shell_layers": str(p["bottom"]),
            "sparse_infill_density": f"{p['relleno']}%", "sparse_infill_pattern": "grid",
            "outer_wall_speed": str(p["v_ext"]), "inner_wall_speed": str(p["v_int"]),
            "sparse_infill_speed": str(p["v_relleno"]), "internal_solid_infill_speed": str(p["v_relleno"] - 10),
            "top_surface_speed": str(p["v_ext"] + 5), "travel_speed": str(VIAJE), "initial_layer_speed": str(p["v_1ra"]),
            "initial_layer_infill_speed": str(p["v_1ra"] + 10),
            "default_acceleration": str(ACEL_IMPRESION), "outer_wall_acceleration": "1000",
            "travel_acceleration": str(ACEL_VIAJE), "initial_layer_acceleration": "800",
            "skirt_loops": "2", "skirt_distance": "3",
            "enable_prime_tower": "1", "prime_tower_width": "40", "prime_volume": "45",
            "wipe_tower_x": ["170"], "wipe_tower_y": ["170"],
            "gcode_label_objects": "1",
        }
        escribir(f"orcaslicer/process/{p['id'].replace(' ', '_')}_{ARCH}.json", json.dumps(proc, indent=2, ensure_ascii=False))
    for f in FILAMENTOS:
        name = f"{f['id']} - Magna 2 {ID}"
        fil = {
            "type": "filament", "name": name, "from": "User", "inherits": "",
            "filament_settings_id": [name], "version": "2.1.0.0",
            "compatible_printers": [mname],
            "filament_type": [f["tipo"]], "filament_diameter": [str(m["diametro"])], "filament_density": [str(f["densidad"])],
            "nozzle_temperature": [str(f["temp"])], "nozzle_temperature_initial_layer": [str(f["temp0"])],
            "nozzle_temperature_range_low": [str(f["temp"] - 15)], "nozzle_temperature_range_high": [str(f["temp"] + 20)],
            "hot_plate_temp": [str(f["cama"])], "hot_plate_temp_initial_layer": [str(f["cama0"])],
            "textured_plate_temp": [str(f["cama"])], "textured_plate_temp_initial_layer": [str(f["cama0"])],
            "fan_min_speed": [str(f["fan_min"])], "fan_max_speed": [str(f["fan_max"])],
            "close_fan_the_first_x_layers": [str(f["fan_desde"] - 1)],
            "filament_cooling_moves": ["0"], "filament_load_time": ["0"], "filament_unload_time": ["0"],
            "filament_unloading_speed": [str(CAMBIO["velocidad"])], "filament_unloading_speed_start": [str(CAMBIO["velocidad"])],
            "filament_loading_speed": ["20"], "filament_loading_speed_start": ["20"],
            "filament_retraction_length": [str(f["retr"])], "filament_retraction_speed": [str(f["vel_retr"])],
            "filament_max_volumetric_speed": ["10" if f["tipo"] == "PLA" else "8"],
            "filament_start_gcode": ["; Linear Advance: descomentar y poner tu K calibrado\n;M900 K0.0"],
        }
        escribir(f"orcaslicer/filament/{f['id']}_{ARCH}.json", json.dumps(fil, indent=2, ensure_ascii=False))


configurar("230")  # al importarlo (pruebas/verificar-perfiles.py) quedan los valores de la 230

if __name__ == "__main__":
    # limpiar calidades viejas para no dejar archivos huérfanos
    shutil.rmtree(os.path.join(AQUI, "cura", "quality"), ignore_errors=True)
    for modelo in MODELOS:
        configurar(modelo)
        print(f"Generando perfiles Magna 2 {modelo}" + ("" if MOD["probado"] else " (SIN PROBAR)") + ":")
        cura()
        prusa()
        orca()
        utiles()
    configurar("230")
    print("Listo.")
