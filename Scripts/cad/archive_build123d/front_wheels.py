"""Subassembly 3 — front wheels: rim (web on the outer face, prints flat without support), TPU tyre,
2x MR105 per wheel, 3 keys rim <-> tyre. The axle (M5x20 bolt + shim + nut) and the inner spacer belong to the
knuckle (subassembly 4, steering).

Approved geometry from the build123d-mcp session of 2026-09-26.
"""
from build123d import *
from lib import *

WEB_T, HUB_R, RING_T = 2.5, 7.0, 2.5


def build():
    x, zc, y0, y1 = FAX_X, FAX_Z, FW_Y0, FW_Y1
    ring = rev_y([(FRIM_R - RING_T, y0), (FRIM_R + RIM_LIP, y0), (FRIM_R + RIM_LIP, y0 + 1), (FRIM_R, y0 + 1),
                  (FRIM_R, y1 - 1), (FRIM_R + RIM_LIP, y1 - 1), (FRIM_R + RIM_LIP, y1), (FRIM_R - RING_T, y1)], x, zc)
    rim = ring + cy(x, y1 - WEB_T, y1, zc, FRIM_R - 1) + cy(x, y0, y1, zc, HUB_R)
    rim -= cy(x, y0 - 1, y1 + 1, zc, AXLE_FREE / 2)
    rim -= cy(x, y0 - 1, y0 + BEARING_W, zc, SEAT_D / 2)
    rim -= cy(x, y1 - BEARING_W, y1 + 1, zc, SEAT_D / 2)
    rim += tyre_keys(x, zc, FRIM_R, y0 + 1, y1 - 1)

    ri, rl = FRIM_R - TYRE_FIT, FRIM_R + RIM_LIP - TYRE_FIT
    prof = Polygon(*[(ri, y0 + 1), (rl, y0 + 1), (rl, y0), (FW_R, y0), (FW_R, y1),
                     (rl, y1), (rl, y1 - 1), (ri, y1 - 1)], align=None)
    prof = fillet([v for v in prof.vertices() if abs(v.X - FW_R) < 1e-6], 2.0)
    tyre = Pos(x, 0, zc) * revolve(prof, Axis.Y)
    for k in range(24):
        tyre -= Pos(x, 0, zc) * Rot(0, 15 * k, 0) * Pos(FW_R, (y0 + y1) / 2, 0) * Box(2.0, y1 - y0 - 4, 1.4)
    tyre -= tyre_keys(x, zc, FRIM_R, y0 + 1, y1 - 1, grow=0.3)

    brg = Compound(children=[bearing(x, y0, zc), bearing(x, y1 - BEARING_W, zc)])

    R = lambda s: mirror(s, about=Plane.XZ)
    parts = {}
    for side, f in (("L", lambda s: s), ("R", R)):
        parts[f"rim_front_{side}"] = Part(f(rim), "#f2f2f2", "printed", 1, "PLA (ASA later)")
        parts[f"tyre_front_{side}"] = Part(f(tyre), "#222222", "printed", 1, "TPU 90A")
    parts["bearing_MR105_front"] = Part(Compound(children=[brg, R(brg)]), "#555a60", "bought", 4, "MR105-2RS 5x10x4")
    return parts
