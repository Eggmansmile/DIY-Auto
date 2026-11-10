"""Subassembly 4 — steering: C-hub knuckles on an M3 kingpin (v2 geometry), SM-S2309S servo UPRIGHT on 2 posts,
its body through a cutout in the nose floor, horn on top (2026-10-01: upside down it could not be assembled, the horn
was trapped between the floor and the bridge). Printed tie rods on M4 bolts + 2 jammed plain M4 nuts (v5, no locknuts), front axles = M5x20 bolts. M3 everywhere since 2026-10-24 (no M2):
the servo tab holes are too small for M3, so a printed clamp bar presses each tab onto its tower (2x M3 into inserts).
v3b (2026-09-28, found with the FreeCAD simulation): single horn arm pointing FORWARD, both tie rods on one pin at
x = SERVO_OUT + HORN_R, so they run almost parallel to the axle. The old ±y cross horn splayed the wheels and locked
at 8°. The right rod sits on top of the left one at the pin. The steering arms sit in the plane of the upper lug,
with a boss up to the horn plane (HORN_Z1).

body_features() returns what the nose gets (front beam with kingpin holes, 2 servo posts with pilot holes, floor cutout);
frame.py adds it before the chassis/nose split. build() returns the separate parts {name: Part}.
Steering arms point at the middle of the rear axle (Ackermann). check() turns knuckle + wheel to ±LOCK,
linkage() solves the 4-bar loop per horn angle and checks the moving parts in that pose, mount_check() lowers the
servo and the horn from above along their assembly path.
"""
import math
from build123d import *
from bd_warehouse.fastener import SocketHeadCapScrew, HexNut, HeatSetNut
from lib import *

ZL0, ZL1 = BEAM_Z0 - GAP - LUG_T, BEAM_Z1 + GAP + LUG_T        # knuckle lugs, 10.6 .. 29.4
LUG_R = 6.0                                                      # lug round the M4 kingpin (3.75 mm wall)
Y_FOOT = KING_Y - 5.5                                            # knuckle print bed: lug ends + arm boss cut flat here
_d = math.hypot(FAX_X, KING_Y)
ARM = (FAX_X - ARM_L * FAX_X / _d, KING_Y - ARM_L * KING_Y / _d)   # steering arm end (left), towards the rear axle centre
SL, ST, SH = SERVO
ROD = dict(t=3.5, w=7.0, boss_r=5.0, hole_d=M4_FREE)            # v5: printed tie rod 3.5 x 7 on top of arm boss and horn; M4 turns free in 4.5
PIN = (SERVO_OUT + HORN_R, 0.0)                                  # horn hole: both tie rods, right rod on top
HORN_LOCK = 17.5                                                 # horn ±17.5° → inner knuckle 30° (linkage ratio ≈ 1.6); firmware SERVO_RANGE 145 µs
ARM_BOSS_R = 5.0                                                 # arm end boss, M4 through, head underneath (2.75 mm wall)
SERVO_CUT = 0.6                                                  # clearance around the servo body in the floor cutout (2026-11-10: 0.4 -> 0.6, servo had to be forced in)
HORN = dict(t=4.0, hub_r=6.0, bore=SERVO_SPLINE_D + 0.02, cap=1.5, w=9.0)          # printed horn: bore ≈ spline + 0.02 → press fit after FDM undersize
SERVO_Z0 = HORN_Z1 - HORN["cap"] - SERVO_SPLINE_Z               # servo base: spline top just under the horn cap (2026-11-05: measured servo)
SERVO_TOP = SERVO_Z0 + SH                                        # flat body top
BOSS_TOP = SERVO_Z0 + SERVO_BOSS_Z                               # raised round top around the shaft
TAB_Z0 = SERVO_Z0 + SERVO_TAB["from_base"]                       # tab underside (face towards the base) = post top
TAB_Z1 = TAB_Z0 + SERVO_TAB["t"]
# servo clamp (no M2): tower per tab from 11.9 (body + 0.45) to 19.5 from SERVO_X, |y| <= 14; the tab rests on it at TAB_Z0,
# the raised sides (|y| > 6.45) stop 0.2 under the tab top so the bar preloads the tab; M3 inserts at 15.7 / ±10.2
# v5: towers end at 16.7 from SERVO_X (front one clears the knuckle arm at lock and the pin nut); the inserts sit beside
# the servo body (|y| 11.1, x 12.1) in side blocks that reach in to xs = 7.5, so each has 2.5 mm of plastic; bars 4.5 thick
CLAMP = dict(x0=SL / 2 + SERVO_CUT + 0.05, xs=7.5, x1=16.7, hw=16.4, side=ST / 2 + SERVO_CUT + 0.05, slot=ST / 2 + 0.5, t=4.5, preload=0.2, bx=12.1, by=11.6)


def body_features():
    """(add, cut) for the nose: beam on a pedestal, servo posts."""
    add = box(FAX_X - BEAM_R, FAX_X + BEAM_R, -KING_Y, KING_Y, BEAM_Z0, BEAM_Z1)
    add += both(cz(FAX_X, KING_Y, BEAM_Z0, BEAM_Z1, BEAM_R))
    if NOSE_Z1 < BEAM_Z0:                            # pedestal only when the nose is lower than the beam
        add += box(FAX_X - BEAM_R, FAX_X + BEAM_R, -12, 12, NOSE_Z1 - 0.01, BEAM_Z0 + 0.01)
    c = CLAMP
    for s in (-1, 1):                                # rear (chassis side of the split) and front tower
        xa, xb = sorted((SERVO_X + s * c["x0"], SERVO_X + s * c["x1"]))
        add += box(xa, xb, -c["hw"], c["hw"], NOSE_Z1 - 0.01, TAB_Z0)
        add += both(box(xa, xb, c["slot"], c["hw"], TAB_Z0 - 0.01, TAB_Z1 - c["preload"]))
        xa, xb = sorted((SERVO_X + s * c["xs"], SERVO_X + s * c["x1"]))      # side blocks beside the servo body
        add += both(box(xa, xb, c["side"], c["hw"], NOSE_Z1 - 0.01, TAB_Z1 - c["preload"]))
    cut = both(cz(FAX_X, KING_Y, BEAM_Z0 - 1, BEAM_Z1 + 1, M4_FREE / 2))
    for x, y in clamp_bolts():
        cut += cz(x, y, TAB_Z1 - c["preload"] - 7, TAB_Z1, M3_INSERT / 2)   # M3x6 insert, blind 7
    cut += tower_chamfer()
    g = SERVO_CUT                                    # the body hangs through the floor
    cut += box(SERVO_X - SL / 2 - g, SERVO_X + SL / 2 + g, -ST / 2 - g, ST / 2 + g, FLOOR_Z0 - 1, NOSE_Z1 + 0.5)
    # 2026-11-10: servo cable leaves the body end below the floor: runs under it and up through this slot (between rear tower and battery stop wall)
    cut += box(SERVO_X - c["x1"] - 4.5, SERVO_X - c["x1"] - 1, -3, 3, FLOOR_Z0 - 1, NOSE_Z1 + 0.5)
    return add, cut


def tower_chamfer():
    """Reliefs on the front tower + bar. 45° cut on the outer front corners of the front tower + bar: the knuckle foot passes there at lock.
    The plane sits INSERT_WALL + insert radius from the insert axis, so the wall stays 2.5 mm."""
    c = CLAMP
    C = c["bx"] + c["by"] + (M3_INSERT / 2 + INSERT_WALL) * 2 ** 0.5     # plane x' + y' = C (relative to SERVO_X)
    k = Pos(SERVO_X + C / 2 + 10.6, C / 2 + 10.6, 25) * Rot(0, 0, 45) * Box(30, 30, 60)
    # relief where the pin bolt head / a nut under the horn sweeps (pin radius HORN_R, ±HORN_LOCK + margin)
    ring = cz(SERVO_OUT, 0, TAB_Z1 - c["preload"] - 0.6, 60, HORN_R + 5.0) - cz(SERVO_OUT, 0, 0, 61, HORN_R - 4.3)
    sweep = ring & box(SERVO_OUT, SERVO_OUT + 30, -c["side"], c["side"], 0, 61)   # 2026-11-05: was ±9.5, left 0.1-0.5 mm slivers at the inserts
    return both(k) + sweep


def clamp_bolts():
    return [(SERVO_X + s * CLAMP["bx"], sy * CLAMP["by"]) for s in (-1, 1) for sy in (-1, 1)]


def servo_clamp():
    """Two flat bars over the tabs (print flat), 4 M3 inserts in the towers, 4 M3x10 from above. Returns (bars, inserts, screws)."""
    c = CLAMP
    bars = None
    for s in (-1, 1):
        xa, xb = sorted((SERVO_X + s * c["x0"], SERVO_X + s * c["x1"]))
        b = box(xa, xb, -c["hw"], c["hw"], TAB_Z1, TAB_Z1 + c["t"])
        xa, xb = sorted((SERVO_X + s * c["xs"], SERVO_X + s * c["x1"]))      # ears over the side blocks, beside the body
        b += both(box(xa, xb, c["side"], c["hw"], TAB_Z1, TAB_Z1 + c["t"]))
        bars = b if bars is None else bars + b
    bars -= tower_chamfer()
    for x, y in clamp_bolts():
        bars -= cz(x, y, TAB_Z1 - 1, TAB_Z1 + c["t"] + 1, M3_FREE / 2)
    bars -= cz(SERVO_OUT, 0, TAB_Z1 - 1, TAB_Z1 + c["t"] + 1, SERVO_BOSS_D / 2 + 0.4)   # notch for the raised servo top (2026-11-05)
    n3 = HeatSetNut(*INSERT_M3, simple=True)
    scr = SocketHeadCapScrew("M3-0.5", 10, "iso4762", simple=True)   # bar 4.5 + 5.5 into the insert
    ins = [Pos(x, y, TAB_Z1 - c["preload"]) * Rot(180, 0, 0) * n3 for x, y in clamp_bolts()]
    scrs = [Pos(x, y, TAB_Z1 + c["t"]) * scr for x, y in clamp_bolts()]
    return bars, Compound(children=ins), Compound(children=scrs)


def knuckle():
    """v5: M4 kingpin, 4 mm lugs (r 6 round the pin), 4 mm arm 7 wide, spacer on the inner race integrated again.
    Prints standing on its inner side: the lug ends and the arm boss are cut flat at Y_FOOT (the bed), the plate bridges
    the 10.8 mm beam gap, the spacer points up."""
    kn = box(FAX_X - PLATE_HW, FAX_X + PLATE_HW, PLATE_Y0, PLATE_Y1, ZL0, ZL1)          # side plate
    for z0 in (ZL0, BEAM_Z1 + GAP):                                                     # upper and lower lug
        kn += box(FAX_X - LUG_R, FAX_X + LUG_R, KING_Y, PLATE_Y1, z0, z0 + LUG_T) + cz(FAX_X, KING_Y, z0, z0 + LUG_T, LUG_R)
    kn += cy(FAX_X, PLATE_Y1, FW_Y0, FAX_Z, RACE_R)                                     # spacer on the inner race only
    kn += bar((FAX_X - 4.0, PLATE_Y1 - 3.0), ARM, ARM_Z0, ARM_Z1, 7)                  # steering arm
    kn += cz(*ARM, ARM_Z0, HORN_Z1, ARM_BOSS_R)                                        # boss up to the tie rod plane
    # web from the boss to the plate, down to the bed: carries the tall boss and stiffens the arm
    kn += box(ARM[0] - ARM_BOSS_R, ARM[0] + ARM_BOSS_R, Y_FOOT, PLATE_Y1, ARM_Z1 - 0.01, HORN_Z1)
    kn -= cz(FAX_X, KING_Y, ZL0 - 1, ZL1 + 1, M4_FREE / 2)                            # kingpin M4
    kn -= cy(FAX_X, PLATE_Y0 - 1, FW_Y0 + 0.01, FAX_Z, AXLE_PRESS / 2)                # M5 axle bolt, snug
    kn -= hex_pocket(FAX_X, PLATE_Y0 - 0.01, FRONT_NUT_Y1, FAX_Z, NUT_M5["af"] + NUT_M5["gap"])   # M5 nut, from the inside
    kn -= cz(*ARM, ARM_Z0 - 1, HORN_Z1 + 1, ROD["hole_d"] / 2)                         # M4 through, head under the arm
    kn -= box(FAX_X - LUG_R - 1, FAX_X + LUG_R + 1, KING_Y - 8, PLATE_Y0, BEAM_Z0 - GAP, BEAM_Z1 + GAP)   # room for the beam end
    kn -= box(FAX_X - 30, FAX_X + 30, KING_Y - 30, Y_FOOT, 0, 60)                     # flat feet = print bed
    return kn


def servo():
    s = box(SERVO_X - SL / 2, SERVO_X + SL / 2, -ST / 2, ST / 2, SERVO_Z0, SERVO_TOP)
    s += box(SERVO_X - SERVO_TAB["span"] / 2, SERVO_X + SERVO_TAB["span"] / 2, -ST / 2, ST / 2, TAB_Z0, TAB_Z1)
    for x in (SERVO_X - SERVO_TAB["hole_dx"], SERVO_X + SERVO_TAB["hole_dx"]):   # tab holes (not used: too small for M3)
        s -= cz(x, 0, TAB_Z0 - 1, TAB_Z1 + 1, 1.1)
    s += cz(SERVO_OUT, 0, SERVO_TOP - 0.01, BOSS_TOP, SERVO_BOSS_D / 2) & box(SERVO_X - SL / 2, SERVO_OUT + 10, -ST / 2, ST / 2, 0, 99)   # raised boss
    s += cz(SERVO_OUT, 0, BOSS_TOP - 0.01, SERVO_Z0 + SERVO_SPLINE_Z, SERVO_SPLINE_D / 2)   # spline, facing up
    h = HORN                                                     # printed: hub pressed on the spline, arm forward, closed cap
    horn = bar((SERVO_OUT, 0), (PIN[0] + 3.5, 0), HORN_Z1 - h["t"], HORN_Z1, h["w"])
    horn += cz(SERVO_OUT, 0, BOSS_TOP + 0.3, HORN_Z1, h["hub_r"])
    horn -= cz(SERVO_OUT, 0, BOSS_TOP, HORN_Z1 - h["cap"], h["bore"] / 2)
    horn -= cz(*PIN, HORN_Z1 - h["t"] - 1, HORN_Z1 + 1, ROD["hole_d"] / 2)
    return s, horn


def tie_rod(sy=1):
    """Flat PETG bar from the horn pin to the arm end. Left rod lies on the arm and horn, the right rod on top of it
    at the pin, with a boss down to its arm. Both print with their flat top on the bed."""
    p0, p1 = PIN, (ARM[0], sy * ARM[1])
    t = ROD["t"]
    z0 = HORN_Z1 if sy > 0 else HORN_Z1 + t
    r = bar(p0, p1, z0, z0 + t, ROD["w"]) + cz(*p0, z0, z0 + t, ROD["boss_r"]) + cz(*p1, HORN_Z1, z0 + t, ROD["boss_r"])
    for p in (p0, p1):
        r -= cz(*p, HORN_Z1 - 1, z0 + t + 1, ROD["hole_d"] / 2)
    return r


def pivot_screws():
    """M4 bolts from BELOW (head under the horn / arm boss), 2 plain M4 nuts jammed on top of the rods (no locknuts;
    everything tightens from above). Lengths: stack + 2 nuts + 1 mm, rounded up to a stock length."""
    t = ROD["t"]
    jam = HexNut("M4-0.7", "iso4032", simple=True).bounding_box().size.Z
    stock = lambda L: next(n for n in (16, 20, 25, 30, 35, 40) if n >= L)
    joints = [(PIN, HORN_Z1 - HORN["t"], HORN_Z1 + 2 * t), ((ARM[0], ARM[1]), ARM_Z0, HORN_Z1 + t),
              ((ARM[0], -ARM[1]), ARM_Z0, HORN_Z1 + 2 * t)]                   # (x, y), bottom of the stack, top of the stack
    lens = [stock(top - bot + 2 * jam + 1) for _, bot, top in joints]
    screws = [Pos(*p, bot) * Rot(180, 0, 0) * SocketHeadCapScrew("M4-0.7", L, "iso4762", simple=True)
              for (p, bot, _), L in zip(joints, lens)]
    nuts = [Pos(*p, top + k * jam) * HexNut("M4-0.7", "iso4032", simple=True) for p, _, top in joints for k in (0, 1)]
    return Compound(children=screws), Compound(children=nuts), lens


def front_axle():
    """Left front axle: M5x20 bolt from the outside, shim on the inner race, plain M5 nut in the pocket of the knuckle
    plate (a nylock would hit the beam end when steering; use threadlocker). Returns (bolt, nut, shim)."""
    n = NUT_M5
    return (axle_bolt(FAX_X, FW_Y1 + SHIM[2], FAX_Z, AXLE_BOLT_FRONT),
            axle_nut(FAX_X, FRONT_NUT_Y1 - n["h"], FAX_Z, n["h"], n["af"]),
            shim(FAX_X, FW_Y1, FAX_Z))


def build():
    kn = knuckle()
    sv, horn = servo()
    fbolt, fnut, sh = front_axle()
    pscr, pnut, plens = pivot_screws()
    bars, cins, cscr = servo_clamp()
    bolt = SocketHeadCapScrew(*KINGPIN, "iso4762", simple=True)
    nut = HexNut(KINGPIN[0], "iso4032", simple=True)
    # head down under the lower lug, 2 jammed nuts on top: the bolt end points up instead of towards the ground
    kp = [Pos(FAX_X, sy * KING_Y, ZL0) * Rot(180, 0, 0) * bolt for sy in (1, -1)]
    jam = HexNut(KINGPIN[0], "iso4032", simple=True).bounding_box().size.Z
    kp_nut = [Pos(FAX_X, sy * KING_Y, ZL1 + k * jam) * nut for sy in (1, -1) for k in (0, 1)]   # 2 nuts jammed (no locknuts)
    R = lambda s: mirror(s, about=Plane.XZ)
    return {
        "knuckle_L": Part(kn, "#e8833a", "printed", 1, "ASA black, stands on its flat feet (inner side down), spacer up"),
        "knuckle_R": Part(R(kn), "#e8833a", "printed", 1, "ASA black, stands on its flat feet (inner side down), spacer up"),
        "axle_bolt_M5x20": Part(Compound(children=[fbolt, R(fbolt)]), "#303030", "fastener", 2, "BOLT M5x20 socket head: front axle from the wheel side, threadlocker"),
        "nut_M5_front": Part(Compound(children=[fnut, R(fnut)]), "#b8bcc2", "fastener", 2, "PLAIN NUT M5 (no insert): in the hex pocket on the inside of the knuckle, before the knuckle goes on"),
        "shim_front": Part(Compound(children=[sh, R(sh)]), "#b8bcc2", "bought", 2, "Shim washer 5x7x0.5 stainless (inner race only)"),
        "servo": Part(sv, "#1a1a1a", "bought", 1, "SpringRC SM-S2309S (have), upright, body through the floor, tabs held down by the 2 printed clamp bars"),
        "servo_clamp": Part(bars, "#e8833a", "printed", 2, "ASA black, 2 flat bars 4.5 mm over the servo tabs (one STL holds both)"),
        "insert_M3x6_servo": Part(cins, "#c9a227", "fastener", 4, "HEAT-SET INSERT M3x6: body, top of the 2 servo towers (4x), before the servo goes in"),
        "screw_M3x10_servo": Part(cscr, "#303030", "fastener", 4, "BOLT M3x10 socket head: through the servo clamp bars into the tower inserts"),
        "servo_horn": Part(horn, "#e8833a", "printed", 1, "ASA black, printed horn 4 mm: press onto the 4.76 spline (bore 4.78) (drop of CA if loose); the tie rods on the pin keep it down; top face on the bed"),
        "tie_rod_L": Part(tie_rod(1), "#e8833a", "printed", 1, "ASA black, 3.5 x 7 flat, top on the bed; pivots on M4 + 2 jammed nuts, must turn freely"),
        "tie_rod_R": Part(tie_rod(-1), "#e8833a", "printed", 1, "ASA black, 3.5 x 7 flat, top on the bed; pivots on M4 + 2 jammed nuts, must turn freely"),
        "screw_M4_steering": Part(pscr, "#303030", "fastener", 3, f"BOLT M4x{plens[0]} (horn pin) + M4x{plens[1]} (left arm) + M4x{plens[2]} (right arm): from below, head under the horn / arm boss"),
        "nut_M4_steering": Part(pnut, "#b8bcc2", "fastener", 6, "2 PLAIN NUTS M4 per pivot, on top of the tie rods: jam them (first snug, back off 1/8, lock the second); the rods must turn freely"),
        "kingpin_M4x30": Part(Compound(children=kp), "#303030", "fastener", 2, "BOLT M4x30 socket head: kingpin, head down through both knuckle lugs and the beam"),
        "nut_M4_kingpin": Part(Compound(children=kp_nut), "#b8bcc2", "fastener", 4, "2 PLAIN NUTS M4 per kingpin, on top: first one until the play is gone, back off 1/8 turn, hold it and lock the second against it"),
    }


def turned(shape, deg, sy=1):
    return Pos(FAX_X, sy * KING_Y, 0) * Rot(0, 0, deg) * Pos(-FAX_X, -sy * KING_Y, 0) * shape


def check(nose, wheel_L, lock=LOCK):
    """Knuckle + front wheel turned to -lock, 0, +lock against the nose and the servo. Returns the worst overlap."""
    sv, horn = servo()
    bars, _, cscr = servo_clamp()
    worst = 0.0
    for deg in (-lock, 0, lock):
        w = turned(knuckle() + wheel_L, deg)
        for name, other in (("nose", nose), ("servo+clamp", sv + horn + bars + cscr)):
            v = sum(s.volume for s in (w & other).solids())
            worst = max(worst, v)
            print(f"steer {deg:+5.0f}°  wheel+knuckle ∩ {name}: {v:.3f} mm3")
    for deg in (-30, -25, -HORN_LOCK, 0, HORN_LOCK, 25, 30):      # horn sweep against the front bridge legs
        h = Pos(SERVO_OUT, 0, 0) * Rot(0, 0, deg) * Pos(-SERVO_OUT, 0, 0) * horn
        v = sum(s.volume for s in (h & nose).solids())
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
    Returns the worst overlap in mm3 and prints the knuckle angles (the table for the note)."""
    sv, horn = servo()
    bars, _, cscr = servo_clamp()
    kn = knuckle()
    horn_max = horn_max or HORN_LOCK
    worst = 0.0
    for hd in (-horn_max, -horn_max / 2, 0, horn_max / 2, horn_max):
        fl, fr = linkage_angles(hd)
        t = math.radians(hd)
        pin = (SERVO_OUT + HORN_R * math.cos(t), HORN_R * math.sin(t))
        moving = {"horn": _rz(horn, (SERVO_OUT, 0), hd)}
        for sy, f, w, name in ((1, fl, wheel_L, "L"), (-1, fr, wheel_R, "R")):
            k = (FAX_X, sy * KING_Y)
            body = kn if sy > 0 else mirror(kn, about=Plane.XZ)
            moving[f"knuckle+wheel_{name}"] = _rz(body + w, k, f)
            x, y = ARM[0] - k[0], sy * ARM[1] - k[1]
            fr_ = math.radians(f)
            a = (k[0] + x * math.cos(fr_) - y * math.sin(fr_), k[1] + x * math.sin(fr_) + y * math.cos(fr_))
            d0 = math.atan2(sy * ARM[1] - PIN[1], ARM[0] - PIN[0])
            d1 = math.atan2(a[1] - pin[1], a[0] - pin[0])
            moving[f"rod_{name}"] = Pos(pin[0] - PIN[0], pin[1] - PIN[1], 0) * _rz(tie_rod(sy), PIN, math.degrees(d1 - d0))
        for mname, m in moving.items():
            for oname, o in (("nose", nose), ("servo+clamp", sv + bars + cscr)):
                v = sum(s_.volume for s_ in (m & o).solids())
                worst = max(worst, v)
                if v > 0.001:
                    print(f"  horn {hd:+5.1f}°  {mname} ∩ {oname}: {v:.3f} mm3")
        print(f"horn {hd:+5.1f}°  knuckle L {fl:+5.1f}°  R {fr:+5.1f}°")
    return worst


def mount_check(body):
    """Assembly path: the servo (without horn) goes straight down into the posts, then the horn straight down onto the
    shaft, and the M3 pin bolt and the four clamp screws must be reachable from above. body = chassis + nose.
    Returns the worst overlap (mm3) along the path."""
    sv, horn = servo()
    ov = lambda a, b: sum(s_.volume for s_ in (a & b).solids())
    worst = 0.0
    for dz in range(40, -1, -4):
        v = ov(Pos(0, 0, dz) * sv, body)
        worst = max(worst, v)
        if v > 0.001:
            print(f"  servo {dz:2d} mm above its seat ∩ body: {v:.3f} mm3")
    for dz in range(20, 0, -2):
        v = ov(Pos(0, 0, dz) * horn, body + sv)
        worst = max(worst, v)
        if v > 0.001:
            print(f"  horn {dz:2d} mm above the shaft ∩ body/servo: {v:.3f} mm3")
    # tool access from above: a Ø7 column (hex key + hand) over the servo screws (before the horn) and over the pin
    bars, _, _ = servo_clamp()
    v = ov(bars, body + sv)
    worst = max(worst, v)
    print(f"clamp bars ∩ body/servo: {v:.3f} mm3")
    cols = [(f"clamp screw {x:.1f}/{y:+.1f}", (x, y), TAB_Z1 + CLAMP["t"], body + sv) for x, y in clamp_bolts()]
    for name, (x, y), z0, others in cols + [("horn pin", PIN, HORN_Z1 + 2 * ROD["t"], body + sv + horn)]:
        v = ov(cz(x, y, z0 + 0.5, z0 + 60, 3.5), others)
        worst = max(worst, v)
        print(f"access from above, {name}: {v:.3f} mm3 in the way")
    print(f"servo base z = {SERVO_Z0:.1f} (ground clearance), tabs on the posts at z = {TAB_Z0:.1f}")
    return worst
