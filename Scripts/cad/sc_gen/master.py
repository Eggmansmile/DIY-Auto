"""Writes Scripts/cad/sc_gen/master.json: the master design CAD/DIY-Auto.sc (printed parts = linked .sc, bought parts = STEP, joints).
Run: python3 master.py && flatpak run --command=solidcraft-cli io.tangencylabs.solidcraft run <master.json> --results --save <CAD/DIY-Auto.sc>
STEP files are already in assembly coordinates; only pcb_kicad.step (raw KiCad frame) gets the placement from freecad_assembly.py.
"""
import json, re
from pathlib import Path
P = Path(__file__).resolve().parents[3]
SC, PARTS = P / "CAD/solidcraft/parts", P / "CAD/parts"
C = []
def add(cmd, **p): C.append({"command": cmd, "params": p})

add("parameters.add", name="LOCK", expression="30 deg", comment="steering lock, = params.py LOCK")
# wheels, tyres and knuckles: a source design <n>_<src>.sc plus a thin design <n>_<oth>.sc that links the source and mirrors it
# (sc_build.py --pair). The thin design holds both bodies, so it is inserted once; the other side's body then leaves it
# into its own component for the joints (it stays linked: Update Links on the master follows the source).
PAIRS = {"rim_rear": "R", "tyre_rear": "R", "rim_front": "R", "tyre_front": "R", "knuckle": "L"}
for n in ["body", "clamp", "tie_rod", "servo_clamp", "servo_horn", "spacer_buck"]:
    add("component.insert_design", path=str(SC / f"{n}.sc"))
for n, src in PAIRS.items():
    oth = "L" if src == "R" else "R"
    add("component.insert_design", path=str(SC / f"{n}_{oth}.sc"), name=f"{n}_{src}")
    add("component.from_bodies", bodies=[f"{n}_{oth}"])

BOUGHT = {"1 frame": ["motor_L", "motor_R", "insert_M3x6_pcb", "insert_M3x6_strap"],
          "2 rear drive": ["bearing_MR105_rear", "pinion", "shim_rear"],
          "3 front wheels": ["bearing_MR105_front"],
          "4 steering": ["insert_M3x6_servo",
                         "servo", "shim_front"],
          "5 electronics": ["battery_2S", "buck_LM2596", "devkit_ESP32"]}
for sub, names in BOUGHT.items():
    for n in names:
        add("file.insert_step", path=str(PARTS / sub / f"{n}.step"), name=n)
# PCB: rotate 180 deg about z, board min corner to (PCB_X0=5, centred, PCB_Z=40)
add("file.insert_step", path=str(PARTS / "5 electronics/pcb_kicad.step"), name="pcb_kicad",
    matrix=[-1, 0, 0, 205, 0, -1, 0, -135, 0, 0, 1, 40])

def J(typ, a, b, pt, z, **kw):
    o = lambda occ: dict(occurrence=occ, point=pt, z=z, x=[1, 0, 0])
    add("joint.create", type=typ, a=o(a), b=o(b), flip=True, **kw)

def occ(n): return f"{n}:1"
for s, sy in (("L", 1), ("R", -1)):
    rim_r, ty_r, rim_f, ty_f, kn = (occ(f"{n}_{s}") for n in ("rim_rear", "tyre_rear", "rim_front", "tyre_front", "knuckle"))
    yr, yf = [0, sy * 40, 35], [150, sy * 40, 20]
    J("revolute", occ("body"), rim_r, yr, [0, 1, 0], name=f"Rear wheel {s}")
    J("rigid", rim_r, ty_r, yr, [0, 1, 0], name=f"Rear tyre {s}")
    J("revolute", occ("body"), kn, [150, sy * 20.5, 20], [0, 0, 1], name=f"Kingpin {s}",
      limits=[["-LOCK", "LOCK"]])
    J("revolute", kn, rim_f, yf, [0, 1, 0], name=f"Front wheel {s}")
    J("rigid", rim_f, ty_f, yf, [0, 1, 0], name=f"Front tyre {s}")
# Bought bolts and nuts from the SolidCraft library (parts.insert), each with a rigid joint to the body that carries it.
# Screw: point = head underside, direction = towards the head. Nut: point = face against the support, direction = towards the tip.
# Positions and head directions come from the old bd_warehouse STEPs (bbox + centre of mass).
def fast(name, fam, size, point, d, carrier, length=None):
    p = dict(family=fam, size=size, point=point, direction=d, name=name)
    if length: p["length"] = length
    add("parts.insert", **p)
    J("rigid", carrier, occ(name), point, d, name=f"Fix {name}")
SC_, NUT = "socket_head_cap_screw", "hex_nut"
UP, DN = [0, 0, 1], [0, 0, -1]
for i, (x, y) in enumerate([(-42.5, 17), (-42.5, -17), (-7.5, 17), (-7.5, -17), (-42.5, 29.8), (-42.5, -29.8), (-7.5, 29.8), (-7.5, -29.8)]):
    fast(f"screw_M3x10_strap_{i}", SC_, "M3", [x, y, 39.5], UP, occ("body"), 10)
for i, (x, y) in enumerate([(106.3, -11.6), (106.3, 11.6), (130.5, -11.6), (130.5, 11.6)]):
    fast(f"screw_M3x10_servo_{i}", SC_, "M3", [x, y, 27.3], UP, occ("body"), 10)
for i, (x, y) in enumerate([(26.41, 29.5), (56.38, 13.5)]):
    fast(f"screw_M3x10_buck_{i}", SC_, "M3", [x, y, 46.2], UP, occ("spacer_buck"), 10)
    fast(f"nut_M3_buck_{i}", NUT, "M3", [x, y, 40.0], DN, occ("spacer_buck"))
for i, (x, y) in enumerate([(8.5, 31.5), (8.5, -31.5), (101.5, 31.5), (101.5, -31.5)]):
    fast(f"screw_M3x6_pcb_{i}", SC_, "M3", [x, y, 41.6], UP, occ("body"), 6)
for s, sy in (("L", 1), ("R", -1)):
    fast(f"axle_bolt_M5x40_{s}", SC_, "M5", [0, sy * 72.5, 35], [0, sy, 0], occ("body"), 40)
    fast(f"nut_M5_rear_{s}", NUT, "M5", [0, sy * 42.2, 35], [0, -sy, 0], occ("body"))
    kn = occ(f"knuckle_{s}")
    fast(f"axle_bolt_M5x20_{s}", SC_, "M5", [150, sy * 46.5, 20], [0, sy, 0], kn, 20)
    fast(f"nut_M5_front_{s}", NUT, "M5", [150, sy * 30.4, 20], [0, -sy, 0], kn)
    fast(f"kingpin_M4x30_{s}", SC_, "M4", [150, sy * 20.5, 10.6], DN, occ("body"), 30)
    for k, z in enumerate((29.4, 32.6)):
        fast(f"nut_M4_kingpin_{s}{k}", NUT, "M4", [150, sy * 20.5, z], UP, occ("body"))
# steering: middle screw on the servo horn, outer two on the knuckles (y>0 = L)
for nm, x, y, L, z0, car in (("mid", 140.1, 0, 20, 32.0, "servo_horn"), ("L", 140.09, 19.15, 25, 25.4, "knuckle_L"),
                             ("R", 140.09, -19.15, 30, 25.4, "knuckle_R")):
    fast(f"screw_M4_steering_{nm}", SC_, "M4", [x, y, z0], DN, occ(car), L)
    zn = {"mid": 43.0, "L": 39.5, "R": 43.0}[nm]
    for k in range(2):
        fast(f"nut_M4_steering_{nm}{k}", NUT, "M4", [x, y, zn + 3.2 * k], UP, occ(car))
# Browser tree: one folder component per group; each top-level component moves into its folder (joints stay, world position is kept).
RULES = [("Tyres", r"^tyre_"),
         ("Front axle & steering", r"knuckle|rim_front|_front|tie_rod|servo|M5x20|kingpin|steering"),
         ("Motors & drive", r"motor_|^clamp|screw_M3x10_strap_|pinion|rim_rear|_rear|M5x40"),
         ("PCB & electronics", r"pcb_kicad|devkit|buck|battery|screw_M3x6_pcb"),
         ("Body", r"^(body|insert_M3x6_(pcb|strap))")]
for g, _ in RULES:
    add("component.create", name=g, parent=0, activate=False)
top = [c["params"]["name"] for c in C if c["command"] in ("file.insert_step", "parts.insert")]
top += ["body", "clamp", "tie_rod", "servo_clamp", "servo_horn", "spacer_buck"] + [f"{n}_{s}" for n in PAIRS for s in "LR"]
for n in top:
    g = next(g for g, rx in RULES if re.search(rx, n))  # StopIteration = part without a group
    add("occurrence.reparent", occurrence=occ(n), parent=g)
(Path(__file__).parent / "master.json").write_text(json.dumps({"commands": C}, indent=1))
print(len(C), "commands")
