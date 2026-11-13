#!/usr/bin/env python3
"""
Genera los perfiles de slicer para la Hellbot Magna 2 230 con el firmware Marlin de este repo.

Salida (en esta misma carpeta):
  cura/definitions/hellbot_magna2_230_marlin.def.json
  cura/extruders/hellbot_magna2_230_marlin_extruder_0.def.json
  cura/extruders/hellbot_magna2_230_marlin_extruder_1.def.json
  prusaslicer/Magna2-230_PrusaSlicer_bundle.ini
  orcaslicer/machine|process|filament/*.json

Todos los valores de la máquina salen de un único lugar (MAQUINA, PROCESOS, FILAMENTOS)
para que los tres slicers queden coherentes entre sí y con el firmware.

Uso: python3 generar_perfiles.py
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- máquina
MAQUINA = dict(
    nombre="Hellbot Magna 2 230 (Marlin 2.1)",
    ancho=230, profundo=230, alto=250,
    boquilla=0.4, diametro=1.75,
    extrusores=2,                  # doble extrusor, hotend 2 en 1 (una sola boquilla)
    retraccion=5.0, vel_retraccion=40,   # bowden; bajar a ~3-4 mm cuando calibres Linear Advance
    zhop=0.2,
    # límites = los del firmware (Configuration.h)
    vmax=dict(x=300, y=300, z=5, e=25),
    amax=dict(x=2000, y=2000, z=100, e=8000),
    jerk=dict(x=10, y=10, z=0.3, e=5),
)

# El cambio de filamento entre T0 y T1 lo hace el FIRMWARE (TOOLCHANGE_FILAMENT_SWAP, M217),
# por eso todos los perfiles ponen la retracción de cambio de herramienta del slicer en 0.

INICIO_COMUN = [
    "; --- Magna 2 230 inicio ---",
    "G90 ; absoluto",
    "M82 ; extrusor absoluto",
    "M140 S{BED0} ; cama",
    "M104 S{TEMP0} ; hotend (sin esperar)",
    "G28 ; home",
    "M190 S{BED0}",
    "M109 S{TEMP0}",
    "G92 E0",
    "G1 Z2.0 F600",
    "G1 X5 Y20 Z0.3 F5000",
    "G1 X5 Y200 Z0.3 F1500 E15 ; linea de purga",
    "G1 X5.4 Y200 Z0.3 F5000",
    "G1 X5.4 Y20 Z0.3 F1500 E30 ; segunda linea",
    "G92 E0",
    "G1 Z2.0 F600",
    "; --- fin inicio ---",
]
FIN_COMUN = [
    "; --- Magna 2 230 fin ---",
    "G91 ; relativo",
    "G1 E-2 F2400 ; retraer",
    "G1 Z10 F600 ; subir",
    "G90",
    "G1 X0 Y220 F3000 ; presentar la pieza",
    "M106 S0 ; ventilador off",
    "M104 S0 ; hotend off",
    "M140 S0 ; cama off",
    "M84 X Y E ; motores off (Z queda trabado)",
    "; --- fin ---",
]

# ---------------------------------------------------------------- procesos
PROCESOS = [
    # nombre, capa, perimetros, capas sup/inf, relleno %, vel perim, vel relleno, vel 1ra capa
    dict(id="0.12 Fina", capa=0.12, perim=3, top=7, bottom=5, relleno=15, v_perim=40, v_relleno=60, v_1ra=20),
    dict(id="0.20 Normal", capa=0.20, perim=3, top=5, bottom=4, relleno=15, v_perim=50, v_relleno=70, v_1ra=25),
    dict(id="0.28 Borrador", capa=0.28, perim=2, top=4, bottom=3, relleno=12, v_perim=55, v_relleno=80, v_1ra=25),
]
VIAJE = 150
ACEL_IMPRESION = 1500
ACEL_VIAJE = 2000

# ---------------------------------------------------------------- filamentos
FILAMENTOS = [
    dict(id="PLA", tipo="PLA", temp=205, temp0=210, cama=60, cama0=65, fan_min=100, fan_max=100, fan_desde=2, densidad=1.24),
    dict(id="PETG", tipo="PETG", temp=235, temp0=240, cama=75, cama0=80, fan_min=30, fan_max=50, fan_desde=3, densidad=1.27),
    dict(id="ABS", tipo="ABS", temp=240, temp0=245, cama=100, cama0=105, fan_min=0, fan_max=15, fan_desde=3, densidad=1.04),
]


def gcode(lineas, temp0, bed0):
    return "\n".join(lineas).replace("{TEMP0}", temp0).replace("{BED0}", bed0)


def escribir(ruta, contenido):
    ruta = os.path.join(AQUI, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)
    print("  ", os.path.relpath(ruta, AQUI))


# ================================================================== CURA
def cura():
    m = MAQUINA
    base = "hellbot_magna2_230_marlin"
    defin = {
        "version": 2,
        "name": m["nombre"],
        "inherits": "fdmprinter",
        "metadata": {
            "visible": True,
            "author": "Perfil Magna 2 230 (Marlin 2.1)",
            "manufacturer": "Hellbot",
            "file_formats": "text/x-gcode",
            "has_materials": True,
            "machine_extruder_trains": {"0": base + "_extruder_0", "1": base + "_extruder_1"},
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
            "machine_extruders_shared_nozzle_initial_retraction": {"default_value": 0},
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
            "machine_start_gcode": {"default_value": gcode(INICIO_COMUN, "{material_print_temperature_layer_0}", "{material_bed_temperature_layer_0}")},
            "machine_end_gcode": {"default_value": gcode(FIN_COMUN, "0", "0")},
            "layer_height": {"default_value": 0.2},
            "layer_height_0": {"value": 0.2},
            "wall_line_count": {"value": 3},
            "top_layers": {"value": 5},
            "bottom_layers": {"value": 4},
            "infill_sparse_density": {"value": 15},
            "speed_print": {"value": 60},
            "speed_wall_0": {"value": 40},
            "speed_wall_x": {"value": 50},
            "speed_infill": {"value": 70},
            "speed_travel": {"value": VIAJE},
            "speed_layer_0": {"value": 25},
            "acceleration_enabled": {"value": True},
            "acceleration_print": {"value": ACEL_IMPRESION},
            "acceleration_travel": {"value": ACEL_VIAJE},
            "retraction_enable": {"value": True},
            "retraction_amount": {"value": m["retraccion"]},
            "retraction_speed": {"value": m["vel_retraccion"]},
            "retraction_hop_enabled": {"value": False},
            "retraction_combing": {"value": "'noskin'"},
            "switch_extruder_retraction_amount": {"value": 0},
            "prime_tower_enable": {"value": True},
            "prime_tower_size": {"value": 20},
            "prime_tower_min_volume": {"value": 60},
            "adhesion_type": {"value": "'skirt'"},
            "skirt_line_count": {"value": 2},
            "material_diameter": {"default_value": m["diametro"]},
        },
    }
    escribir(f"cura/definitions/{base}.def.json", json.dumps(defin, indent=2, ensure_ascii=False))
    for n in range(2):
        ext = {
            "version": 2,
            "name": f"Extrusor {n + 1}",
            "inherits": "fdmextruder",
            "metadata": {"machine": base, "position": str(n)},
            "overrides": {
                "extruder_nr": {"default_value": n},
                "machine_nozzle_size": {"default_value": m["boquilla"]},
                "material_diameter": {"default_value": m["diametro"]},
                "machine_nozzle_offset_x": {"default_value": 0.0},
                "machine_nozzle_offset_y": {"default_value": 0.0},
                "machine_extruder_start_code": {"default_value": f"; T{n} activo (el firmware hace el cambio de filamento)"},
            },
        }
        escribir(f"cura/extruders/{base}_extruder_{n}.def.json", json.dumps(ext, indent=2, ensure_ascii=False))


# ================================================================== PRUSASLICER
def ini_val(v):
    return str(v).replace("\n", "\\n")


def prusa():
    m = MAQUINA
    two = lambda v: f"{v},{v}"
    out = ["# Bundle PrusaSlicer - Hellbot Magna 2 230 (Marlin 2.1)",
           "# Importar: Archivo > Importar > Importar paquete de configuracion (Import Config Bundle)", ""]
    pname = "Magna 2 230 Marlin 2.1"
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
        "cooling_tube_length": 0,
        "cooling_tube_retraction": 0,
        "parking_pos_retraction": 0,
        "extra_loading_move": 0,
        "high_current_on_filament_swap": 0,
        "retract_length": two(m["retraccion"]),
        "retract_speed": two(m["vel_retraccion"]),
        "deretract_speed": two(0),
        "retract_lift": two(m["zhop"]),
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
        "start_gcode": ini_val(gcode(INICIO_COMUN, "[first_layer_temperature[initial_tool]]", "[first_layer_bed_temperature[initial_tool]]")),
        "end_gcode": ini_val(gcode(FIN_COMUN, "0", "0")),
        "toolchange_gcode": "T[next_extruder] ; el firmware retira/carga el filamento (M217)",  # PrusaSlicer no emite T si este campo no esta vacio
    }
    out.append(f"[printer:{pname}]")
    out += [f"{k} = {v}" for k, v in printer.items()]
    out.append("")
    for p in PROCESOS:
        out.append(f"[print:{p['id']} - Magna 2 230]")
        cfg = {
            "layer_height": p["capa"], "first_layer_height": 0.2,
            "perimeters": p["perim"], "top_solid_layers": p["top"], "bottom_solid_layers": p["bottom"],
            "fill_density": f"{p['relleno']}%", "fill_pattern": "grid",
            "perimeter_speed": p["v_perim"], "external_perimeter_speed": max(25, p["v_perim"] - 15),
            "infill_speed": p["v_relleno"], "solid_infill_speed": p["v_relleno"] - 10,
            "top_solid_infill_speed": 35, "travel_speed": VIAJE, "first_layer_speed": p["v_1ra"],
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
        out.append(f"[filament:{f['id']} - Magna 2 230]")
        cfg = {
            "filament_type": f["tipo"], "filament_diameter": m["diametro"], "filament_density": f["densidad"],
            "temperature": f["temp"], "first_layer_temperature": f["temp0"],
            "bed_temperature": f["cama"], "first_layer_bed_temperature": f["cama0"],
            "fan_always_on": 1 if f["fan_min"] > 0 else 0, "cooling": 1,
            "min_fan_speed": f["fan_min"], "max_fan_speed": f["fan_max"], "disable_fan_first_layers": f["fan_desde"] - 1,
            "filament_cooling_moves": 0, "filament_load_time": 0, "filament_unload_time": 0,
            "filament_unloading_speed": 40, "filament_unloading_speed_start": 40, "filament_loading_speed": 20,
            "filament_loading_speed_start": 20,
            "start_filament_gcode": ini_val("; Linear Advance: descomentar y poner tu K calibrado\n;M900 K0.0"),
        }
        out += [f"{k} = {v}" for k, v in cfg.items()]
        out.append("")
    out += ["[presets]", f"printer = {pname}", "print = 0.20 Normal - Magna 2 230", "filament = PLA - Magna 2 230", ""]
    escribir("prusaslicer/Magna2-230_PrusaSlicer_bundle.ini", "\n".join(out))


# ================================================================== ORCASLICER
def orca():
    m = MAQUINA
    two = lambda v: [str(v), str(v)]
    mname = "Magna 2 230 Marlin 2.1 0.4"
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
        "cooling_tube_length": "0", "cooling_tube_retraction": "0", "parking_pos_retraction": "0",
        "extra_loading_move": "0", "high_current_on_filament_swap": "0",
        "retraction_length": two(m["retraccion"]), "retraction_speed": two(m["vel_retraccion"]),
        "deretraction_speed": two(0), "z_hop": two(m["zhop"]),
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
        "machine_start_gcode": gcode(INICIO_COMUN, "[nozzle_temperature_initial_layer]", "[bed_temperature_initial_layer_single]"),
        "machine_end_gcode": gcode(FIN_COMUN, "0", "0"),
        "use_relative_e_distances": "0",
    }
    escribir("orcaslicer/machine/Magna2-230_machine.json", json.dumps(machine, indent=2, ensure_ascii=False))
    for p in PROCESOS:
        name = f"{p['id']} - Magna 2 230"
        proc = {
            "type": "process", "name": name, "from": "User", "inherits": "",
            "print_settings_id": name, "version": "2.1.0.0",
            "compatible_printers": [mname],
            "layer_height": str(p["capa"]), "initial_layer_print_height": "0.2",
            "wall_loops": str(p["perim"]), "top_shell_layers": str(p["top"]), "bottom_shell_layers": str(p["bottom"]),
            "sparse_infill_density": f"{p['relleno']}%", "sparse_infill_pattern": "grid",
            "outer_wall_speed": str(max(25, p["v_perim"] - 15)), "inner_wall_speed": str(p["v_perim"]),
            "sparse_infill_speed": str(p["v_relleno"]), "internal_solid_infill_speed": str(p["v_relleno"] - 10),
            "top_surface_speed": "35", "travel_speed": str(VIAJE), "initial_layer_speed": str(p["v_1ra"]),
            "initial_layer_infill_speed": str(p["v_1ra"] + 10),
            "default_acceleration": str(ACEL_IMPRESION), "outer_wall_acceleration": "1000",
            "travel_acceleration": str(ACEL_VIAJE), "initial_layer_acceleration": "800",
            "skirt_loops": "2", "skirt_distance": "3",
            "enable_prime_tower": "1", "prime_tower_width": "40", "prime_volume": "45",
            "wipe_tower_x": ["170"], "wipe_tower_y": ["170"],
            "gcode_label_objects": "1",
        }
        escribir(f"orcaslicer/process/{p['id'].replace(' ', '_')}_Magna2-230.json", json.dumps(proc, indent=2, ensure_ascii=False))
    for f in FILAMENTOS:
        name = f"{f['id']} - Magna 2 230"
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
            "filament_start_gcode": ["; Linear Advance: descomentar y poner tu K calibrado\n;M900 K0.0"],
        }
        escribir(f"orcaslicer/filament/{f['id']}_Magna2-230.json", json.dumps(fil, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("Generando perfiles:")
    cura()
    prusa()
    orca()
    print("Listo.")
