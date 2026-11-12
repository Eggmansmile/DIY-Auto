"""Collision, clearance and design-rule checks for the whole car, from the SolidCraft STEP files in CAD/parts/<n subassembly>/
(not print/). Run from Scripts/cad/ after a change (and after export_sc.py --apply):
    ~/.local/bin/uv run -p 3.12 --with build123d --with trimesh --with networkx --with bd_warehouse python check_all.py
Every overlap should print 0.000; every rule line should say OK. Part list = CAD/manifest.json, dimensions = params.py."""
import json, math
from pathlib import Path
from build123d import *
from lib import *                                   # params + cy/cz/tyre_keys helpers (build123d only)

CAD = Path(__file__).resolve().parents[2] / "CAD"
P = {}
for m in json.loads((CAD / "manifest.json").read_text()):
    f = CAD / "parts" / m["subassembly"] / f"{m['name']}.step"
    P[m["name"]] = import_step(str(f))
ov = lambda a, b: sum(s.volume for s in ((a & b) or Compound(children=[])).solids())   # STEP shapes: a & b is None when disjoint
body = P["body"]

# geometry the old steering.py / frame.py modules provided (constants copied; shapes now come from the STEPs)
SL, ST, SH = SERVO
SERVO_CUT = 0.6                                       # = SERVO_CUT (floor cutout clearance round the servo)
HORN_T, HORN_CAP = 4.0, 1.5
SERVO_Z0 = HORN_Z1 - HORN_CAP - SERVO_SPLINE_Z
TAB_Z0 = SERVO_Z0 + SERVO_TAB["from_base"]
TAB_Z1 = TAB_Z0 + SERVO_TAB["t"]
CLAMP = dict(t=4.5, preload=0.2, bx=12.1, by=11.6)
_d = math.hypot(FAX_X, KING_Y)
ARM = (FAX_X - ARM_L * FAX_X / _d, KING_Y - ARM_L * KING_Y / _d)
PIN = (SERVO_OUT + HORN_R, 0.0)
HORN_LOCK = 17.5
ROD_T = 3.5
EARS = [(X_MOT + s * EAR_X, ey) for ey in EAR_Y for s in (-1, 1)]
clamp_bolts = lambda: [(SERVO_X + s * CLAMP["bx"], sy * CLAMP["by"]) for s in (-1, 1) for sy in (-1, 1)]
servo, horn, bars, cscr = P["servo"], P["servo_horn"], P["servo_clamp"], P["screw_M3x10_servo"]


def turned(shape, deg, sy=1):
    return Pos(FAX_X, sy * KING_Y, 0) * Rot(0, 0, deg) * Pos(-FAX_X, -sy * KING_Y, 0) * shape


def steer_check(nose, wheel_L, lock=LOCK):
    """Knuckle + front wheel turned to -lock, 0, +lock against the nose and the servo. Returns the worst overlap."""
    worst = 0.0
    for deg in (-lock, 0, lock):
        w = turned(P["knuckle_L"] + wheel_L, deg)
        for name, other in (("nose", nose), ("servo+clamp", servo + horn + bars + cscr)):
            v = ov(w, other)
            worst = max(worst, v)
            print(f"steer {deg:+5.0f}°  wheel+knuckle ∩ {name}: {v:.3f} mm3")
    for deg in (-30, -25, -HORN_LOCK, 0, HORN_LOCK, 25, 30):      # horn sweep against the front bridge legs
        h = Pos(SERVO_OUT, 0, 0) * Rot(0, 0, deg) * Pos(-SERVO_OUT, 0, 0) * horn
        v = ov(h, nose)
        print(f"horn {deg:+5.1f}°  ∩ nose: {v:.3f} mm3")
    return worst


def _rz(shape, c, deg):
    return Pos(c[0], c[1], 0) * Rot(0, 0, deg) * Pos(-c[0], -c[1], 0) * shape


def linkage_angles(horn_deg):
    """Knuckle angles (L, R) for a horn angle, solving |arm end - pin| = rod length (bisection near the last root)."""
    t = math.radians(horn_deg)
    pin = (SERVO_OUT + HORN_R * math.cos(t), HORN_R * math.sin(t))
    out = []
    for sy in (1, -1):
        k, a0 = (FAX_X, sy * KING_Y), (ARM[0], sy * ARM[1])
        L = math.dist(a0, PIN)

        def err(f):
            x, y = a0[0] - k[0], a0[1] - k[1]
            a = (k[0] + x * math.cos(f) - y * math.sin(f), k[1] + x * math.sin(f) + y * math.cos(f))
            return math.dist(a, pin) - L
        fs = [math.radians(i / 4) for i in range(-240, 241)]
        roots = [(f0 + f1) / 2 for f0, f1 in zip(fs, fs[1:]) if err(f0) * err(f1) <= 0]
        out.append(math.degrees(min(roots, key=abs)) if roots else float("nan"))
    return out


def linkage(nose, wheel_L, wheel_R, horn_max=None):
    """Turn the horn, solve the loop, move horn + rods + knuckles + wheels and check them against the nose and the servo.
    Returns the worst overlap in mm3 and prints the knuckle angles."""
    horn_max = horn_max or HORN_LOCK
    worst = 0.0
    for hd in (-horn_max, -horn_max / 2, 0, horn_max / 2, horn_max):
        fl, fr = linkage_angles(hd)
        t = math.radians(hd)
        pin = (SERVO_OUT + HORN_R * math.cos(t), HORN_R * math.sin(t))
        moving = {"horn": _rz(horn, (SERVO_OUT, 0), hd)}
        for sy, f, w, name in ((1, fl, wheel_L, "L"), (-1, fr, wheel_R, "R")):
            k = (FAX_X, sy * KING_Y)
            kn = P["knuckle_L"] if sy > 0 else P["knuckle_R"]
            moving[f"knuckle+wheel_{name}"] = _rz(kn + w, k, f)
            x, y = ARM[0] - k[0], sy * ARM[1] - k[1]
            fr_ = math.radians(f)
            a = (k[0] + x * math.cos(fr_) - y * math.sin(fr_), k[1] + x * math.sin(fr_) + y * math.cos(fr_))
            d0 = math.atan2(sy * ARM[1] - PIN[1], ARM[0] - PIN[0])
            d1 = math.atan2(a[1] - pin[1], a[0] - pin[0])
            moving[f"rod_{name}"] = Pos(pin[0] - PIN[0], pin[1] - PIN[1], 0) * _rz(P["tie_rod_L" if sy > 0 else "tie_rod_R"], PIN, math.degrees(d1 - d0))
        for mname, m in moving.items():
            for oname, o in (("nose", nose), ("servo+clamp", servo + bars + cscr)):
                v = ov(m, o)
                worst = max(worst, v)
                if v > 0.001:
                    print(f"  horn {hd:+5.1f}°  {mname} ∩ {oname}: {v:.3f} mm3")
        print(f"horn {hd:+5.1f}°  knuckle L {fl:+5.1f}°  R {fr:+5.1f}°")
    return worst


def mount_check(body):
    """Assembly path: the servo (without horn) goes straight down into the posts, then the horn straight down onto the
    shaft, and the pin bolt and the four clamp screws must be reachable from above. Returns the worst overlap (mm3)."""
    worst = 0.0
    for dz in range(40, -1, -4):
        v = ov(Pos(0, 0, dz) * servo, body)
        worst = max(worst, v)
        if v > 0.001:
            print(f"  servo {dz:2d} mm above its seat ∩ body: {v:.3f} mm3")
    for dz in range(20, 0, -2):
        v = ov(Pos(0, 0, dz) * horn, body + servo)
        worst = max(worst, v)
        if v > 0.001:
            print(f"  horn {dz:2d} mm above the shaft ∩ body/servo: {v:.3f} mm3")
    v = ov(bars, body + servo)
    worst = max(worst, v)
    print(f"clamp bars ∩ body/servo: {v:.3f} mm3")
    cols = [(f"clamp screw {x:.1f}/{y:+.1f}", (x, y), TAB_Z1 + CLAMP["t"], body + servo) for x, y in clamp_bolts()]
    for name, (x, y), z0, others in cols + [("horn pin", PIN, HORN_Z1 + 2 * ROD_T, body + servo + horn)]:
        v = ov(cz(x, y, z0 + 0.5, z0 + 60, 3.5), others)
        worst = max(worst, v)
        print(f"access from above, {name}: {v:.3f} mm3 in the way")
    print(f"servo base z = {SERVO_Z0:.1f} (ground clearance), tabs on the posts at z = {TAB_Z0:.1f}")
    return worst


print("--- rear wheel stack")
stack_r = P["axle_bolt_M5x40"] + P["nut_M5_rear"] + P["shim_rear"]
for k in ("rim_rear_L", "rim_rear_R", "tyre_rear_L", "body", "bearing_MR105_rear", "pinion", "motor_L", "clamp_L", "pcb_envelope", "battery_2S", "buck_LM2596"):
    print(f"bolt+nut+shim ∩ {k}: {ov(stack_r, P[k]):.3f} mm3")
print("--- front wheel stack")
stack_f = P["axle_bolt_M5x20"] + P["nut_M5_front"] + P["shim_front"]
for k in ("rim_front_L", "tyre_front_L", "bearing_MR105_front", "knuckle_L", "knuckle_R", "body"):
    print(f"bolt+nut+shim ∩ {k}: {ov(stack_f, P[k]):.3f} mm3")
print("--- keys: rim ∩ tyre is the 0.3 mm stretch fit (TYRE_FIT); the keys themselves must sit inside their grooves")
for k, x, z, r, y0, y1 in (("rear_L", 0, AXLE_Z, RIM_R, RW_Y0 + 1, RW_Y1 - 1), ("front_L", FAX_X, FAX_Z, FRIM_R, FW_Y0 + 1, FW_Y1 - 1)):
    keys = tyre_keys(x, z, r, y0, y1) - cy(x, y0 - 1, y1 + 1, z, r - TYRE_FIT)     # the rib part above the fit radius
    print(f"keys {k} ∩ tyre: {ov(keys, P['tyre_' + k]):.3f} mm3")
print("--- steering at lock, with the axle stack on the knuckle")
wl = P["rim_front_L"] + P["tyre_front_L"] + P["bearing_MR105_front"] + stack_f
wl = Compound(children=[s for s in wl.solids() if s.center().Y > 0])
wr = mirror(wl, about=Plane.XZ)
print("check worst:", steer_check(body, wl))
print("linkage worst:", linkage(body, wl, wr))
kp = P["kingpin_M4x30"] + P["nut_M4_kingpin"]
for k in ("body", "servo", "servo_horn", "tie_rod_L", "tie_rod_R", "screw_M4_steering", "nut_M4_steering"):
    print(f"kingpin+nut ∩ {k}: {ov(kp, P[k]):.3f} mm3")
for k in ("body", "servo", "knuckle_L", "knuckle_R", "servo_horn", "servo_clamp", "screw_M3x10_servo"):
    print(f"M4 pivot bolts+nuts ∩ {k}: {ov(P['screw_M4_steering'] + P['nut_M4_steering'], P[k]):.3f} mm3")
for k in ("servo_horn", "tie_rod_L", "tie_rod_R", "pcb_envelope"):
    print(f"servo clamp+screws ∩ {k}: {ov(P['servo_clamp'] + P['screw_M3x10_servo'], P[k]):.3f} mm3")
print(f"servo ∩ body: {ov(P['servo'], body):.3f} mm3   horn ∩ body: {ov(P['servo_horn'], body):.3f} mm3")
print("--- assembly path servo + horn")
print("mount worst:", mount_check(body))
print("--- electronics")
for k in ("body", "pcb_envelope"):
    print(f"battery ∩ {k}: {ov(P['battery_2S'], P[k]):.3f} mm3")
for k in ("body", "motor_L", "motor_R", "clamp_L", "clamp_R", "battery_2S"):
    print(f"buck LM2596 ∩ {k}: {ov(P['buck_LM2596'], P[k]):.3f} mm3")

print("--- design rules (v5): solid plastic around every insert, tool paths")
def ring_wall(x, y, ztop, depth, shape):
    """thickest full ring (step 0.25) around a vertical insert hole that is still all plastic"""
    t = 0.0
    while t < 5:
        ring = cz(x, y, ztop - depth + 0.5, ztop - 0.3, M3_INSERT / 2 + t + 0.25) - cz(x, y, ztop - depth, ztop, M3_INSERT / 2 + 0.05)
        if ring.volume - ov(ring, shape) > 0.02 * ring.volume:
            break
        t += 0.25
    return t
inserts = [("motor ear", x, s * y, SPLIT, 7) for x, y in EARS for s in (1, -1)] + \
          [("PCB standoff", x, y, PCB_Z, 9) for x, y in PCB_HOLES] + \
          [("servo tower", x, y, TAB_Z1 - CLAMP["preload"], 7) for x, y in clamp_bolts()]
bad = 0
for nm, x, y, zt, d in inserts:
    w = ring_wall(x, y, zt, d, body)
    bad += w < INSERT_WALL
    print(f"{'OK ' if w >= INSERT_WALL else 'LOW'} insert wall {nm:12s} ({x:6.1f},{y:6.1f}): {w:.2f} mm")
    iron = cz(x, y, zt + 0.3, zt + 40, 3.5)                           # soldering iron tip + insert Ø7, before assembly
    if ov(iron, body) > 0.01:
        bad += 1; print(f"LOW iron path {nm} ({x:.1f},{y:.1f}) blocked")
# order: inserts → motors + straps → servo + clamp bars → horn, knuckles, tie rods → PCB. So only parts already in place count.
others = Compound(children=[P[k] for k in ("body", "motor_L", "motor_R", "clamp_L", "clamp_R", "servo", "servo_clamp", "battery_2S", "buck_LM2596")])
for nm, pts, zh in (("strap screw", [(x, s * y) for x, y in EARS for s in (1, -1)], SPLIT + EAR_T + 3.5),
                    ("servo clamp screw", clamp_bolts(), TAB_Z1 + CLAMP["t"] + 3.5)):
    for x, y in pts:
        if ov(cz(x, y, zh, zh + 60, 2.0), others) > 0.01:
            bad += 1; print(f"LOW hex key path {nm} ({x:.1f},{y:.1f}) blocked")
print("design rules:", "OK" if bad == 0 else f"{bad} problems")
print("--- thickness audit: the floor must be solid z FLOOR_Z0..FLOOR_Z1 over the whole outline (nose included, 2026-11-07: nose was 3 mm)")
g = SERVO_CUT
C_CH = CLAMP['bx'] + CLAMP['by'] + (M3_INSERT / 2 + INSERT_WALL) * 2 ** 0.5   # 45° knuckle relief on the front corners cuts through the whole floor
thin = []
for x in range(-44, int(HALF_OUTLINE[-1][0]) - 2, 4):
    ymax = min(y for xx, y in HALF_OUTLINE if xx >= x) if x >= -44 else 0
    for y in range(-int(ymax) + 3, int(ymax) - 2, 4):
        inside_cut = abs(x - SERVO_X) < SERVO[0] / 2 + g + 1 and abs(y) < SERVO[1] / 2 + g + 1
        in_batt = BATT[0] - 2 < x < BATT[1] + 2 and abs(y) < BATT[2] / 2 + 3
        in_relief = (x - SERVO_X) + abs(y) > C_CH
        in_cable = SERVO_X < x < SERVO_X + SERVO[0] / 2 + g + 4 and abs(y) < 4   # servo cable V-notch (front end)
        if inside_cut or in_batt or in_relief or in_cable or x < GEAR_PLATE_X0 + 6:
            continue
        for z in (FLOOR_Z0 + 0.5, FLOOR_Z1 - 0.5):
            if not body.is_inside(Vector(x, y, z)):
                thin.append((x, y, z))
for sy in (1, -1):                                  # 2026-11-10: the beam end must exist round each kingpin
    for dx, dy in ((BEAM_R - 0.8, 0), (-(BEAM_R - 0.8), 0), (0, sy * (BEAM_R - 0.8))):
        if not body.is_inside(Vector(FAX_X + dx, sy * KING_Y + dy, (BEAM_Z0 + BEAM_Z1) / 2)):
            thin.append((FAX_X + dx, sy * KING_Y + dy, "beam end"))
print("floor audit:", "OK" if not thin else f"FAIL {len(thin)} points not solid: {sorted({(a, b) for a, b, _ in thin})}")
print("--- lowest points (ground = 0, tyres excluded)")
low = sorted((v.bounding_box().min.Z, k) for k, v in P.items() if not k.startswith("tyre"))[:5]
print([(round(z, 2), k) for z, k in low])
