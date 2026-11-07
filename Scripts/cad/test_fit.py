"""Fit test block v4 (flat on the bed, ~45 min): which hole sizes suit Ruben's printer + filament. Print it again for every
new material (PLA now, ASA later). Every hole is a value from params.py, with one size smaller and one larger next to it
where the fit is critical. Instructions: "Testblok passingen.md".

Row A  M3 INSERT  M3_INSERT -0.2 / 0 / +0.2, blind 7   | M3 VRIJ  M3_FREE through (bolt slides through, kingpin)
Row B  M2 INSERT  M2_INSERT -0.2 / 0 / +0.2, blind 7   | M2 VRIJ  2.4 through (tie rods, arm boss, horn)
Row C  LAGER      SEAT_D -0.1 / 0 / +0.1, blind 4.5    | M5 PAS   AXLE_PRESS (bolt in tower/knuckle) | M5 VRIJ AXLE_FREE (rim)
Row D  M5 MOER    hex af + gap -0.2 / 0 / +0.2, 4.5 deep (knuckle pocket) | NYLOCK  slot af + gap x h_nyl + gap (tower)
Output: CAD/parts/test_fit/print/test_fit.stl

Run from Scripts/cad/:
    ~/.local/bin/uv run -p 3.12 --with build123d --with bd_warehouse python test_fit.py
"""
from pathlib import Path
from build123d import *
from params import M3_INSERT, M3_FREE, M2_INSERT, SEAT_D, AXLE_PRESS, AXLE_FREE, NUT_M5

T = 8.0
M2_FREE = 2.4                       # ROD["hole_d"] in steering.py
NUT = NUT_M5["af"] + NUT_M5["gap"]


def r2(v):
    return round(v, 2)


# (x, kind, size, depth, label); kind "o" = round hole, "hex" = nut pocket, "slot" = nylock slot; depth None = through
ROWS = [
    ("A  M3 INSERT", "M3 VRIJ", [(8, "o", M3_INSERT - 0.2, 7), (19, "o", M3_INSERT, 7), (30, "o", M3_INSERT + 0.2, 7),
                                 (55, "o", M3_FREE, None)]),
    ("B  M2 INSERT", "M2 VRIJ", [(8, "o", M2_INSERT - 0.2, 7), (19, "o", M2_INSERT, 7), (30, "o", M2_INSERT + 0.2, 7),
                                 (55, "o", M2_FREE, None)]),
    ("C  LAGER MR105", "M5 PAS | VRIJ", [(8, "o", SEAT_D - 0.1, 4.5), (21, "o", SEAT_D, 4.5), (34, "o", SEAT_D + 0.1, 4.5),
                                         (50, "o", AXLE_PRESS, None), (62, "o", AXLE_FREE, None)]),
    ("D  M5 MOER", "NYLOCK", [(9, "hex", NUT - 0.2, 4.5), (22, "hex", NUT, 4.5), (35, "hex", NUT + 0.2, 4.5),
                              (57, "slot", NUT, 7)]),
]
W, ROW_H = 70.0, 19.0
D = ROW_H * len(ROWS) + 2
block = Pos(W / 2, D / 2, T / 2) * Box(W, D, T)


def engrave(txt, x, y, size, align=Align.CENTER):
    return Pos(x, y, T - 0.5) * extrude(Text(txt, size, align=(align, Align.CENTER)), 0.6)


for j, (title_l, title_r, holes) in enumerate(ROWS):
    y0 = D - 1 - (j + 1) * ROW_H            # row A on top (far side on the bed)
    yc = y0 + 8.5
    block -= engrave(title_l, 3, y0 + ROW_H - 2.4, 2.6, Align.MIN)
    block -= engrave(title_r, 44, y0 + ROW_H - 2.4, 2.6, Align.MIN)
    for x, kind, d, depth in holes:
        dep = T + 0.02 if depth is None else depth
        if kind == "o":
            cut = Pos(x, yc, T - dep / 2 + 0.01) * Cylinder(d / 2, dep + 0.02)
            half = d / 2
        elif kind == "hex":                  # flats facing ±x, like the pocket in the knuckle
            cut = Pos(x, yc, T - dep + 0.01) * Rot(0, 0, 30) * extrude(RegularPolygon(d / 2, 6, major_radius=False), dep + 0.02)
            cut += Pos(x, yc, T - dep - 0.5) * Cylinder(AXLE_PRESS / 2, 1.1)          # bolt hole below, as in the knuckle
            half = d / 2 / 0.866
        else:                                # slot af x nylock height, like the tower
            sh = NUT_M5["h_nyl"] + 2 * NUT_M5["gap"]
            cut = Pos(x, yc, T - dep / 2 + 0.01) * Box(d, sh, dep + 0.02)
            half = sh / 2
        block -= cut
        block -= engrave(f"{r2(d):g}", x, yc - half - 2.6, 2.4)
    if j:                                    # divider groove between rows
        block -= Pos(W / 2, y0 + ROW_H, T - 0.2) * Box(W - 4, 0.6, 0.6)
out = Path(__file__).resolve().parents[2] / "CAD" / "parts" / "test_fit" / "print" / "test_fit.stl"
out.parent.mkdir(parents=True, exist_ok=True)
export_stl(block, str(out), tolerance=0.01, angular_tolerance=0.1)
print("OK", out, f"{W:.0f} x {D:.0f} x {T:.0f} mm")
