"""Technical drawing of the DIY-Auto, straight from the CAD model (A3, 1:1, third-angle projection).

Top, side and front view are hidden-line projections of every part (build123d HLR), so the drawing always matches the
model. Hidden lines are left out: with the gears and tyre treads they only add noise.

Run from Scripts/cad/:
    ~/.local/bin/uv run -p 3.12 --with build123d --with bd_warehouse --with matplotlib python gen_drawing.py
Writes Drawings/DIY-Auto_v4.pdf and .png, and Assets/DIYAuto_tekening_v4.png for the notes
(v1 and v2 stay in Drawings/ for comparison).
"""
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle as MplRect        # build123d (via lib) has its own Rectangle
from build123d import Compound
from lib import *
import frame, rear_drive, front_wheels, steering, electronics

VERSION = "v4"
OUT = Path(__file__).resolve().parents[2] / "Drawings"
OUT.mkdir(exist_ok=True)
SKIP = ("pcb_envelope", "insert_")            # envelope = clearance volume; inserts sit inside the plastic

P = {}
for m in (frame, rear_drive, front_wheels, steering, electronics):
    P.update({k: v.shape for k, v in m.build().items() if not k.startswith(SKIP)})
pcb = box(PCB_X0, PCB_X0 + 100, -35, 35, PCB_Z, PCB_Z + 1.6)      # the board itself, without the lead envelope
car = Compound(children=[*P.values(), pcb])
bb = car.bounding_box()

# --- sheet -------------------------------------------------------------------
fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect("equal"); ax.axis("off")
TXT = dict(fontsize=6.5, family="DejaVu Sans")
CEN = dict(lw=0.4, color="black", ls=(0, (10, 2, 2, 2)))
ax.add_patch(MplRect((10, 10), 400, 277, lw=1.4, ec="k", fc="none"))

# view origins on the sheet (car point (0, 0, 0) = rear axle on the centre line, on the ground)
TX, TY = 70.0, 196.0       # top view: (x, y)
SX, SY = 70.0, 34.0        # side view: (x, z), seen from the right side so the nose points right
FX, FY = 326.0, 34.0       # front view: (y, z), the car's left side is on the right


def project(origin, up, ox, oy):
    vis, _ = car.project_to_viewport(origin, up, (0, 0, 0))
    for e in vis:
        n = 2 if e.geom_type.name == "LINE" else max(6, int(e.length / 0.4))
        pts = [e.position_at(i / (n - 1)) for i in range(n)]
        ax.plot([ox + p.X for p in pts], [oy + p.Y for p in pts], lw=0.45, color="black", solid_capstyle="round", zorder=3)


project((0, 0, 1000), (0, 1, 0), TX, TY)
project((0, -1000, 0), (0, 0, 1), SX, SY)
project((1000, 0, 0), (0, 0, 1), FX, FY)


def dim(p, q, off, text, vertical=False):
    """Linear dimension between sheet points p and q, offset perpendicular by off (mm)."""
    (x0, y0), (x1, y1) = p, q
    sgn = 1 if off > 0 else -1
    box_ = dict(fc="white", ec="none", pad=0.3)
    arrow = dict(arrowstyle="<|-|>", lw=0.4, color="k", mutation_scale=5)
    if vertical:
        xd = max(x0, x1) + off if off > 0 else min(x0, x1) + off
        for y, x in ((y0, x0), (y1, x1)):
            ax.plot([x, xd + 1.5 * sgn], [y, y], lw=0.3, color="k", zorder=5)
        ax.annotate("", (xd, y0), (xd, y1), arrowprops=arrow, zorder=5)
        ax.text(xd - 1.2, (y0 + y1) / 2, text, rotation=90, ha="center", va="center", zorder=6, bbox=box_, **TXT)
    else:
        yd = max(y0, y1) + off if off > 0 else min(y0, y1) + off
        for x, y in ((x0, y0), (x1, y1)):
            ax.plot([x, x], [y, yd + 1.5 * sgn], lw=0.3, color="k", zorder=5)
        ax.annotate("", (x0, yd), (x1, yd), arrowprops=arrow, zorder=5)
        ax.text((x0 + x1) / 2, yd + 1.2, text, ha="center", va="bottom", zorder=6, bbox=box_, **TXT)


def title(x, y, s):
    ax.text(x, y, s, fontsize=8, weight="bold", family="DejaVu Sans", ha="left", va="bottom")


top = lambda x, y: (TX + x, TY + y)
side = lambda x, z: (SX + x, SY + z)
front = lambda y, z: (FX + y, FY + z)
L = (bb.min.X, bb.max.X)
W = bb.max.Y
H = bb.max.Z

# top view
title(TX + L[0], TY + W + 6, "BOVENAANZICHT")
ax.plot(*zip(top(L[0] - 4, 0), top(L[1] + 4, 0)), **CEN)
for x in (0, FAX_X):
    ax.plot(*zip(top(x, -W - 3), top(x, W + 3)), **CEN)
dim(top(0, -W), top(FAX_X, -W), -8, f"wielbasis {FAX_X:g}")
dim(top(L[0], -W), top(L[1], -W), -16, f"{L[1] - L[0]:.0f}")
dim(top(L[1], -W), top(L[1], W), 6, f"{2 * W:.0f}", vertical=True)
dim(top(FAX_X, -(FW_Y0 + FW_Y1) / 2), top(FAX_X, (FW_Y0 + FW_Y1) / 2), 3, f"spoor voor {FW_Y0 + FW_Y1:g}", vertical=True)
dim(top(0, -(RW_Y0 + RW_Y1) / 2), top(0, (RW_Y0 + RW_Y1) / 2), -54, f"spoor achter {RW_Y0 + RW_Y1:g}", vertical=True)

# side view
title(SX + L[0], SY + H + 6, "ZIJAANZICHT (RECHTS)")
ax.plot(*zip(side(L[0] - 6, 0), side(L[1] + 6, 0)), lw=0.8, color="k")
for x, z in ((0, AXLE_Z), (FAX_X, FAX_Z)):
    ax.plot(*zip(side(x - RW_R - 3, z), side(x + RW_R + 3, z)), **CEN)
    ax.plot(*zip(side(x, z - RW_R - 3), side(x, z + RW_R + 3)), **CEN)
dim(side(0, 0), side(0, 2 * RW_R), -RW_R - 8, f"Ø{2 * RW_R:g}", vertical=True)
dim(side(FAX_X, 0), side(FAX_X, 2 * FW_R), FW_R + 6, f"Ø{2 * FW_R:g}", vertical=True)
dim(side(L[1], 0), side(L[1], H), 14, f"{H:.0f}", vertical=True)
dim(side(L[0], 0), side(L[0], FLOOR_Z0), -6, f"{FLOOR_Z0:g}", vertical=True)

# front view
title(FX - W, FY + H + 6, "VOORAANZICHT")
ax.plot(*zip(front(-W - 6, 0), front(W + 6, 0)), lw=0.8, color="k")
ax.plot(*zip(front(0, -4), front(0, H + 4)), **CEN)
dim(front(-W, 0), front(W, 0), -10, f"{2 * W:.0f}")

# --- notes and title block ------------------------------------------------------
notes = [
    "ONTWERP v4 (2026-10-01)",
    f"1  Achterwielaandrijving, één motor per wiel, rondsel {Z_PIN}T → {Z_GEAR}T m{MOD} in de velg ({Z_GEAR // Z_PIN}:1).",
    "2  Assen: M5-bouten. Achter M5×35 + nylock in de toren, voor M5×20 + moer in de fusee.",
    "     Schijfje 5×7×0,5 en kraag Ø6,5 raken alleen de binnenring van de MR105.",
    "3  Sturing: fusees op M3×25 (kop onder, nylock boven), servo SM-S2309S rechtop,",
    f"     hoorn ±{steering.HORN_LOCK:g}° → binnenwiel 30°; stangen op M2 + nylock.",
    "4  Accu AOLIKES 2S 66,3 × 37,1 × 18,5 onder de print, elastiek over 4 haakjes.",
    "5  PLA voor de prototypes (later ASA), banden TPU 90A.",
    "",
    "Verborgen lijnen weggelaten. Lijnen = projectie van het CAD-model",
    "(Scripts/cad, build123d). Maten in mm.",
]
y = 270
for s in notes:
    bold = s.startswith("ONTWERP")
    ax.text(250, y, s, fontsize=7 if bold else 6.2, weight="bold" if bold else "normal", family="DejaVu Sans", va="top")
    y -= 4.0
tb = [("Titel", f"DIY-Auto — ontwerp {VERSION}"), ("Schaal", "1:1 op A3"), ("Eenheden", "mm"),
      ("Projectie", "derde hoek"), ("Datum", "2026-10-01"), ("Getekend / nagezien", "Claude / Ruben")]
bx, by = 250, 150
for i, (k, val) in enumerate(tb):
    ax.add_patch(MplRect((bx, by - (i + 1) * 5.5), 36, 5.5, lw=0.4, ec="k", fc="0.9"))
    ax.add_patch(MplRect((bx + 36, by - (i + 1) * 5.5), 120, 5.5, lw=0.4, ec="k", fc="none"))
    ax.text(bx + 1.5, by - (i + 0.5) * 5.5, k, fontsize=6, va="center", family="DejaVu Sans")
    ax.text(bx + 37.5, by - (i + 0.5) * 5.5, val, fontsize=7 if i else 8, va="center", family="DejaVu Sans",
            weight="bold" if i == 0 else "normal")

fig.savefig(OUT / f"DIY-Auto_{VERSION}.pdf")
fig.savefig(OUT / f"DIY-Auto_{VERSION}.png", dpi=200)
fig.savefig(OUT.parents[2] / "Assets" / f"DIYAuto_tekening_{VERSION}.png", dpi=150)   # for the notes (flat Assets folder)
print("OK:", OUT / f"DIY-Auto_{VERSION}.pdf", f"L {L[1] - L[0]:.0f}  B {2 * W:.0f}  H {H:.0f}")
