"""Subassembly 1 — frame: body (floor, rear axle towers, motor saddles + gear plate, PCB standoffs) + 2 strap clamps.

v2 (2026-09-26, Ruben: "the blocks can be smaller"): the solid motor block became two U-saddles, a gear plate
that ties the motor boss to the axle tower (fixes the 24 mm gear centre distance), and a 3.0 mm strap clamp (v5)
split at the motor axis. Plastic per motor mount: 20.6 cm³ instead of 35.5.
Fasteners from bd_warehouse: 8x Hilitchi M3x6 insert + 8x ISO 4762 M3x10 (straps), 4x Hilitchi M3x6 insert (PCB).
M3 everywhere since 2026-10-24 (Ruben has no M2).
build() returns {name: Part}; assemble.py collects all subassemblies.
"""
import math
from build123d import *
from bd_warehouse.fastener import HeatSetNut, InsertHole, SocketHeadCapScrew, ClearanceHole
from lib import *
import steering

R_POCKET = CAN_W / 2 + 0.2
R_OUT = R_POCKET + MOUNT_WALL
EARS = [(X_MOT + s * EAR_X, ey) for ey in EAR_Y for s in (-1, 1)]


def motor_can(extra=0.0):
    return cy(X_MOT, CAN_FACE - CAN_L, CAN_FACE, AXLE_Z, CAN_W / 2 + extra) & \
        box(X_MOT - 20, X_MOT + 20, 0, 60, AXLE_Z - CAN_H / 2 - extra, AXLE_Z + CAN_H / 2 + extra)


def motor_solid():
    """Solid stand-in for the motor STL (measured from it): can 24 x 18.3 x 30.3, front boss Ø6.1 x 1.9,
    shaft Ø2 sticking out 7.6, rear bushing Ø6.34 x 3.4."""
    m = motor_can()
    m += cy(X_MOT, CAN_FACE, CAN_FACE + 1.9, AXLE_Z, 3.06)
    m += cy(X_MOT, CAN_FACE, CAN_FACE + 7.6, AXLE_Z, 1.0)
    m += cy(X_MOT, CAN_FACE - CAN_L - 3.4, CAN_FACE - CAN_L, AXLE_Z, 3.17)
    return m


def pocket(top_preload=0.0):
    """Can + 0.2 mm; top_preload lowers the flat top so the strap presses on the can."""
    return cy(X_MOT, CRADLE_Y0 - 1, CAN_FACE, AXLE_Z, R_POCKET) & \
        box(X_MOT - 20, X_MOT + 20, -1, 60, AXLE_Z - CAN_H / 2 - 0.2, AXLE_Z + CAN_H / 2 - top_preload)


def ear(x, y, z0, z1):
    """Round ear at (x, y) joined back to the motor axis."""
    return cz(x, y, z0, z1, EAR_R) + box(min(x, X_MOT), max(x, X_MOT), y - EAR_R, y + EAR_R, z0, z1)


def teardrop_x(x0, x1, y, z, r):
    """45° peak on top of a horizontal hole along x (radius r): the square of side r, turned 45°, sits on the axis."""
    return Pos((x0 + x1) / 2, y, z + r / 2 ** 0.5) * Rot(45, 0, 0) * Box(x1 - x0, r, r)


def build():
    n3 = HeatSetNut(*INSERT_M3, simple=True)
    m3x10 = SocketHeadCapScrew("M3-0.5", 10, "iso4762", simple=True)   # strap: ear 4.5 + 5.5 into the insert
    z_lo = FLOOR_Z1 - 0.01

    # lower half per side: gear plate (into the tower), 2 saddles, back stop, 4 ears
    lower = box(GEAR_PLATE_X0, TOWER[0] + 0.1, CAN_FACE, WALL_Y1, z_lo, AXLE_Z + 10)
    for y0, y1 in SADDLES:
        lower += box(X_MOT - R_OUT, X_MOT + R_OUT, y0, y1 + 0.01, z_lo, SPLIT)
    lower += box(X_MOT - R_OUT, X_MOT + R_OUT, CRADLE_Y0, CRADLE_Y0 + 2.01, z_lo, 29.0)      # stays below the bushing
    for x, y in EARS:
        lower += ear(x, y, z_lo, SPLIT)
    lower -= pocket()
    lower -= cy(X_MOT, CAN_FACE - 1, WALL_Y1 + 1, AXLE_Z, 3.6)                              # bearing boss Ø7.2
    tower = box(TOWER[0], TOWER[1], TOWER[2], WALL_Y1, z_lo, TOWER_TOP)
    tower -= cy(0, TOWER[2] - 1, WALL_Y1 + 1, AXLE_Z, AXLE_PRESS / 2)                        # M5 axle bolt, snug
    n = NUT_M5                                                                                  # nut slot, open at the top
    tower -= box(-n["af"] / 2 - n["gap"], n["af"] / 2 + n["gap"], REAR_NUT_Y0 - n["gap"], REAR_NUT_Y0 + n["h_nyl"] + n["gap"],
                 AXLE_Z - n["af"] / math.sqrt(3) - n["gap"], TOWER_TOP + 1)
    tower += cy(0, WALL_Y1 - 0.01, GY0, AXLE_Z, RACE_R) - cy(0, WALL_Y1 - 1, GY0 + 1, AXLE_Z, AXLE_PRESS / 2)  # race collar

    outline = HALF_OUTLINE + [(x, -y) for x, y in reversed(HALF_OUTLINE)]
    floor = Pos(0, 0, FLOOR_Z0) * extrude(Polygon(*outline, align=None), FLOOR_Z1 - FLOOR_Z0, dir=(0, 0, 1))
    if NOSE_Z1 < FLOOR_Z1:                                           # nose thinner than the floor (steering beam sits on it)
        floor -= box(NOSE_X0, 500, -100, 100, NOSE_Z1, FLOOR_Z1 + 1)
    body = floor + both(lower + tower)
    for x, y in PCB_HOLES:
        body += cz(x, y, z_lo, PCB_Z, STANDOFF_R)
    # subassembly 5: bosses for the LM2596 module between the motors (v3: 2S pack, no switch — the JST plug is the switch)
    # 2026-11-05: LM2596 moved onto the PCB, no buck bosses on the floor any more
    # battery stops around the 2S pack: end walls with a notch for the leads, 10 mm side legs at each end
    bx0, bx1, bhw, _ = BATT
    g, w, h, nt = BATT_STOP["gap"], BATT_STOP["wall"], BATT_STOP["h"], BATT_STOP["notch"]
    yo = bhw + g + w
    for xa, xb in ((bx0 - g - w, bx0 - g), (bx1 + g, bx1 + g + w)):
        body += box(xa, xb, -yo, yo, z_lo, FLOOR_Z1 + h) - box(xa - 1, xb + 1, -nt / 2, nt / 2, FLOOR_Z1, FLOOR_Z1 + h + 1)
    for sy in (-1, 1):
        yi = sy * (bhw + g)
        for xa, xb in ((bx0 - g - w, bx0 + 10), (bx1 - 10, bx1 + g + w)):
            body += box(xa, xb, min(yi, sy * yo), max(yi, sy * yo), z_lo, FLOOR_Z1 + h)
    # elastic band hooks: J-profile post beside the pack, tip points outward with a 45° underside (prints without support)
    k = HOOK
    for sy in (-1, 1):
        a = yo + 1.0
        prof = [(a, z_lo), (a + k["t"], z_lo), (a + k["t"], k["top"] - 2.5 - k["tip"]), (a + k["t"] + k["tip"], k["top"] - 2.5),
                (a + k["t"] + k["tip"], k["top"]), (a, k["top"])]
        for xh in k["x"]:
            hook = extrude(Plane.YZ.offset(xh - k["w"] / 2) * Polygon(*prof, align=None), k["w"])
            body += hook if sy > 0 else mirror(hook, about=Plane.XZ)
    # gear plate rib behind the motor (v5): the 2 mm plate can't get thicker (pinion + rim gear), so a rib stops it flexing
    body += both(box(GEAR_PLATE_X0 - 3.5, GEAR_PLATE_X0 + 0.01, 36.0, WALL_Y1, z_lo, AXLE_Z + 10))
    # subassembly 4 (steering): front beam with the kingpin holes, 2 servo towers
    st_add, st_cut = steering.body_features()
    body = body + st_add - st_cut
    # build everything BEFORE the with-block: a Box made inside BuildPart is added to the part automatically
    with BuildPart() as bp:
        add(body)
        with Locations(*[(x, y, PCB_Z) for x, y in PCB_HOLES]):
            InsertHole(n3, depth=9)
        with Locations(*[(x, s * y, SPLIT) for x, y in EARS for s in (1, -1)]):
            InsertHole(n3, depth=7)
    body = bp.part
    body -= box(bx0 - g, bx1 + g, -bhw - g, bhw + g, FLOOR_Z1 - BATT_SEAT, FLOOR_Z1 + 1)   # battery pocket

    # strap clamp: can-shaped shell over the top half + 4 ears
    top = AXLE_Z + CAN_H / 2 + MOUNT_WALL
    strap = cy(X_MOT, CRADLE_Y0 + 2.2, CAN_FACE - 0.2, AXLE_Z, R_OUT) & \
        box(X_MOT - 20, X_MOT + 20, 0, 60, SPLIT, top)
    for x, y in EARS:
        strap += ear(x, y, SPLIT, SPLIT + EAR_T)
    strap -= pocket(CLAMP_PRELOAD)
    with BuildPart() as cp:
        add(strap)
        with Locations(*[(x, y, SPLIT + EAR_T) for x, y in EARS]):
            ClearanceHole(m3x10)
    clamp = cp.part

    flip = Rot(180, 0, 0)
    ins2 = [Pos(x, s * y, SPLIT) * flip * n3 for x, y in EARS for s in (1, -1)]
    scr2 = [Pos(x, s * y, SPLIT + EAR_T) * m3x10 for x, y in EARS for s in (1, -1)]
    ins3 = [Pos(x, y, PCB_Z) * flip * n3 for x, y in PCB_HOLES]
    ms = motor_solid()

    return {
        "body": Part(body, "#8fa3b8", "printed", 1, "ASA black, one piece (v5: chassis + nose merged), floor on the bed"),
        "clamp_L": Part(clamp, "#e8833a", "printed", 1, "ASA black, split face on the bed"),
        "clamp_R": Part(mirror(clamp, about=Plane.XZ), "#e8833a", "printed", 1, "ASA black, split face on the bed"),
        "insert_M3x6_strap": Part(Compound(children=ins2), "#c9a227", "fastener", 8, "HEAT-SET INSERT M3x6: body, top of the 8 motor-saddle ears (press in with the soldering iron before the motor goes in)"),
        "screw_M3x10_strap": Part(Compound(children=scr2), "#303030", "fastener", 8, "BOLT M3x10 socket head: through the motor strap clamp into the ear insert"),
        "insert_M3x6_pcb": Part(Compound(children=ins3), "#c9a227", "fastener", 4, "HEAT-SET INSERT M3x6: body, top of the 4 PCB standoffs"),
        "motor_L": Part(ms, "#c0c4c8", "reference", 1, "DC motor 24x18.3 can (STL in CAD/ref)"),
        "motor_R": Part(mirror(ms, about=Plane.XZ), "#c0c4c8", "reference", 1, "DC motor 24x18.3 can (STL in CAD/ref)"),
    }
