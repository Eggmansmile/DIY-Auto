"""Collision, clearance and design-rule checks for the whole car. Run from Scripts/cad/ after a change:
    ~/.local/bin/uv run -p 3.12 --with build123d --with bd_warehouse python check_all.py
Every overlap should print 0.000; every rule line should say OK."""
from build123d import *
from lib import *
import frame, rear_drive, front_wheels, steering, electronics

P = {}
for m in (frame, rear_drive, front_wheels, steering, electronics):
    P.update({k: v.shape for k, v in m.build().items()})
ov = lambda a, b: sum(s.volume for s in (a & b).solids())
body = P["body"]

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
print("check worst:", steering.check(body, wl))
print("linkage worst:", steering.linkage(body, wl, wr))
kp = P["kingpin_M4x30"] + P["nut_M4_kingpin"]
for k in ("body", "servo", "servo_horn", "tie_rod_L", "tie_rod_R", "screw_M4_steering", "nut_M4_steering"):
    print(f"kingpin+nut ∩ {k}: {ov(kp, P[k]):.3f} mm3")
for k in ("body", "servo", "knuckle_L", "knuckle_R", "servo_horn", "servo_clamp", "screw_M3x10_servo"):
    print(f"M4 pivot bolts+nuts ∩ {k}: {ov(P['screw_M4_steering'] + P['nut_M4_steering'], P[k]):.3f} mm3")
for k in ("servo_horn", "tie_rod_L", "tie_rod_R", "pcb_envelope"):
    print(f"servo clamp+screws ∩ {k}: {ov(P['servo_clamp'] + P['screw_M3x10_servo'], P[k]):.3f} mm3")
print(f"servo ∩ body: {ov(P['servo'], body):.3f} mm3   horn ∩ body: {ov(P['servo_horn'], body):.3f} mm3")
print("--- assembly path servo + horn")
print("mount worst:", steering.mount_check(body))
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
inserts = [("motor ear", x, s * y, SPLIT, 7) for x, y in frame.EARS for s in (1, -1)] + \
          [("PCB standoff", x, y, PCB_Z, 9) for x, y in PCB_HOLES] + \
          [("servo tower", x, y, steering.TAB_Z1 - steering.CLAMP["preload"], 7) for x, y in steering.clamp_bolts()]
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
for nm, pts, zh in (("strap screw", [(x, s * y) for x, y in frame.EARS for s in (1, -1)], SPLIT + EAR_T + 3.5),
                    ("servo clamp screw", steering.clamp_bolts(), steering.TAB_Z1 + steering.CLAMP["t"] + 3.5)):
    for x, y in pts:
        if ov(cz(x, y, zh, zh + 60, 2.0), others) > 0.01:
            bad += 1; print(f"LOW hex key path {nm} ({x:.1f},{y:.1f}) blocked")
print("design rules:", "OK" if bad == 0 else f"{bad} problems")
print("--- thickness audit: the floor must be solid z FLOOR_Z0..FLOOR_Z1 over the whole outline (nose included, 2026-11-07: nose was 3 mm)")
g = steering.SERVO_CUT
C_CH = steering.CLAMP['bx'] + steering.CLAMP['by'] + (M3_INSERT / 2 + INSERT_WALL) * 2 ** 0.5   # 45° knuckle relief on the front corners cuts through the whole floor
thin = []
for x in range(-44, int(HALF_OUTLINE[-1][0]) - 2, 4):
    ymax = min(y for xx, y in HALF_OUTLINE if xx >= x) if x >= -44 else 0
    for y in range(-int(ymax) + 3, int(ymax) - 2, 4):
        inside_cut = abs(x - SERVO_X) < SERVO[0] / 2 + g + 1 and abs(y) < SERVO[1] / 2 + g + 1
        in_batt = BATT[0] - 2 < x < BATT[1] + 2 and abs(y) < BATT[2] / 2 + 3
        in_relief = (x - SERVO_X) + abs(y) > C_CH
        x1 = SERVO_X - steering.CLAMP['x1']
        in_cable = x1 - 5.5 < x < x1 and abs(y) < 4      # servo cable slot behind the rear tower
        if inside_cut or in_batt or in_relief or in_cable or x < GEAR_PLATE_X0 + 6:
            continue
        for z in (FLOOR_Z0 + 0.5, FLOOR_Z1 - 0.5):
            if not body.is_inside(Vector(x, y, z)):
                thin.append((x, y, z))
print("floor audit:", "OK" if not thin else f"FAIL {len(thin)} points not solid: {sorted({(a, b) for a, b, _ in thin})}")
print("--- lowest points (ground = 0, tyres excluded)")
low = sorted((v.bounding_box().min.Z, k) for k, v in P.items() if not k.startswith("tyre"))[:5]
print([(round(z, 2), k) for z, k in low])
