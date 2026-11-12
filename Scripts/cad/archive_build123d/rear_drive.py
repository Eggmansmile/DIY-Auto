"""Subassembly 2 — rear drive: rim with 90T m0.5 gear (9:1, v3 2026-09-28), TPU tyre, 2x MR105 per wheel on an M5x40 bolt
(2026-10-01: head -> shim 5x7x0.5 on the inner race -> bearings -> race collar on the tower -> M5 nut in a slot in the tower),
3 keys rim <-> tyre against slipping, motor pinion 10T m0.5 (measured Ø6.0) as reference.

Approved geometry from the build123d-mcp session of 2026-09-26.
Rim prints with the outer face (y = 72) on the bed, gear on top: 45° cones replace support.
Checked (v3): pinion ↔ gear 0.125–0.141 mm gap at 5 rotation steps, 0 overlap.
"""
import math
from build123d import *
from lib import *


def build():
    gear = gear_y(MOD, Z_GEAR, 0, GY0, AXLE_Z, GEAR_W, BACKLASH)
    ring = rev_y([(26.5, RW_Y0), (RIM_R + RIM_LIP, RW_Y0), (RIM_R + RIM_LIP, RW_Y0 + 1), (RIM_R, RW_Y0 + 1),
                  (RIM_R, RW_Y1 - 1), (RIM_R + RIM_LIP, RW_Y1 - 1), (RIM_R + RIM_LIP, RW_Y1), (26.5, RW_Y1)], 0, AXLE_Z)
    cone_out = rev_y([(26.6, 61.9), (26.6, 58.4), (20.2, 52.0), (16.8, 52.0)], 0, AXLE_Z)     # ring → gear disc, 45°
    cone_in = rev_y([(7.4, 51.0), (19.9, 51.0), (19.9, 52.0), (7.4, 64.5)], 0, AXLE_Z)        # solid 45° fill under the disc
    hub = cy(0, GY0, RW_Y1, AXLE_Z, 7.5)
    rim = gear + ring + cone_out + cone_in + hub
    rim -= cy(0, GY0 - 1, RW_Y1 + 1, AXLE_Z, AXLE_FREE / 2)
    rim -= cy(0, GY0 - 1, GY0 + BEARING_W, AXLE_Z, SEAT_D / 2)
    rim -= cy(0, RW_Y1 - BEARING_W, RW_Y1 + 1, AXLE_Z, SEAT_D / 2)
    rim -= rev_y([(19.5, RW_Y0 - 0.01), (28.2, RW_Y0 - 0.01), (28.2, RW_Y0 + 0.6), (19.5, RW_Y0 + 0.6)], 0, AXLE_Z)  # pinion clearance
    rim += tyre_keys(0, AXLE_Z, RIM_R, RW_Y0 + 1, RW_Y1 - 1)

    ri, rl = RIM_R - TYRE_FIT, RIM_R + RIM_LIP - TYRE_FIT
    prof = Polygon(*[(ri, RW_Y0 + 1), (rl, RW_Y0 + 1), (rl, RW_Y0), (RW_R, RW_Y0), (RW_R, RW_Y1),
                     (rl, RW_Y1), (rl, RW_Y1 - 1), (ri, RW_Y1 - 1)], align=None)
    prof = fillet([v for v in prof.vertices() if abs(v.X - RW_R) < 1e-6], 3.0)
    tyre = Pos(0, 0, AXLE_Z) * revolve(prof, Axis.Y)
    for k in range(36):
        tyre -= Pos(0, 0, AXLE_Z) * Rot(0, 10 * k, 0) * Pos(RW_R, (RW_Y0 + RW_Y1) / 2, 0) * Box(2.4, RW_Y1 - RW_Y0 - 6, 1.6)
    tyre -= tyre_keys(0, AXLE_Z, RIM_R, RW_Y0 + 1, RW_Y1 - 1, grow=0.3)

    # axle = M5 bolt from the outside; the plain M5 nut sits in a slot in the tower (frame.py), tighten until the play is gone
    bolt = axle_bolt(0, RW_Y1 + SHIM[2], AXLE_Z, AXLE_BOLT_REAR)
    nut = axle_nut(0, REAR_NUT_Y0, AXLE_Z, NUT_M5["h"], NUT_M5["af"])   # v5: plain nut (no locknuts), tightened: the bolt does not turn
    sh = shim(0, RW_Y1, AXLE_Z)
    brg = Compound(children=[bearing(0, GY0, AXLE_Z), bearing(0, RW_Y1 - BEARING_W, AXLE_Z)])
    pinion = gear_y(MOD, Z_PIN, X_MOT, GY0, AXLE_Z, GEAR_W, phase=180 / Z_PIN)

    L = lambda s: s
    R = lambda s: mirror(s, about=Plane.XZ)
    parts = {}
    for side, f in (("L", L), ("R", R)):
        parts[f"rim_rear_{side}"] = Part(f(rim), "#f2f2f2", "printed", 1, "PLA (ASA later), 0.2 nozzle (m0.5 teeth)")
        parts[f"tyre_rear_{side}"] = Part(f(tyre), "#222222", "printed", 1, "TPU 90A")
    parts["bearing_MR105_rear"] = Part(Compound(children=[brg, R(brg)]), "#555a60", "bought", 4, "MR105-2RS 5x10x4")
    parts["axle_bolt_M5x40"] = Part(Compound(children=[bolt, R(bolt)]), "#303030", "fastener", 2, "BOLT M5x40 socket head: rear axle, from the wheel side (M5x30 is too short for the nylock)")
    parts["nut_M5_rear"] = Part(Compound(children=[nut, R(nut)]), "#b8bcc2", "fastener", 2, "PLAIN NUT M5 (no insert): dropped into the slot in the axle tower from the top, tighten fully (clamps the inner races, the bolt does not turn)")
    parts["shim_rear"] = Part(Compound(children=[sh, R(sh)]), "#b8bcc2", "bought", 2, "Shim washer 5x7x0.5 stainless (inner race only)")
    parts["pinion"] = Part(Compound(children=[pinion, R(pinion)]), "#c9a227", "reference", 2, "10T m0.5 brass on the motor (have)")
    return parts
