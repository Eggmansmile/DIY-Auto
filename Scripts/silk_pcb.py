"""Silkscreen for KiCad/DIY-Auto.kicad_pcb after route_pcb.py: resistor values, readable references, polarity marks.

Only touches F.Silkscreen, so it can run again without re-routing.
Run (from the project folder, system Python because it has pcbnew):
    python3 Scripts/silk_pcb.py
    kicad-cli pcb drc --schematic-parity KiCad/DIY-Auto.kicad_pcb
"""
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "KiCad" / "DIY-Auto.kicad_pcb"
O = (100.0, 100.0)
VALUE = {"5.1k": "5k1", "20k": "20k", "1k": "1k"}   # notation of the soldering note


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(O[0] + x), pcbnew.FromMM(O[1] + y))


def style(t, h=1.0, align=pcbnew.GR_TEXT_H_ALIGN_CENTER, angle=0):
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(h), pcbnew.FromMM(h)))
    t.SetTextThickness(pcbnew.FromMM(0.15))
    t.SetHorizJustify(align)
    t.SetTextAngleDegrees(angle)


def items(seq):
    """pcbnew's SWIG iterators break on Python 3.14; index instead."""
    return [seq[i] for i in range(len(seq))]


b = pcbnew.LoadBoard(str(PCB))
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
# FindPadByNumber() returns a bare SwigPyObject in this pcbnew build: read all pads once
PADS = {ref: {pd.GetNumber(): (pcbnew.ToMM(pd.GetPosition().x) - O[0], pcbnew.ToMM(pd.GetPosition().y) - O[1])
              for pd in fp.Pads()} for ref, fp in fps.items()}


def at(fp, pad):
    return PADS[fp.GetReference()][pad]


# texts from an earlier run of this script. Removed only just before saving:
# after Remove(), this pcbnew build returns bare SwigPyObjects for every later call.
OLD = [(b, d) for d in items(b.Drawings())
       if d.Type() == pcbnew.PCB_TEXT_T and d.GetLayer() == pcbnew.F_SilkS]
OLD += [(fp, t) for ref, fp in fps.items() if ref.startswith("R")
        for t in items(fp.GraphicalItems())
        if t.Type() == pcbnew.PCB_TEXT_T and t.GetLayer() == pcbnew.F_SilkS]

# resistors: value inside the body, reference next to pad 1.
# Rows are 3.5 mm apart, so between two bodies there is no room for text.
for ref, fp in fps.items():
    if not ref.startswith("R"):
        continue
    (x1, y1), (x2, y2) = at(fp, "1"), at(fp, "2")
    vertical = abs(x1 - x2) < 0.01
    v = pcbnew.PCB_TEXT(fp)
    v.SetText(VALUE[fp.GetValue()])
    style(v, angle=90 if vertical else 0)
    v.SetPosition(mm((x1 + x2) / 2, (y1 + y2) / 2))
    fp.Add(v)

    r = fp.Reference()
    if vertical:                                  # R41, R42: under pad 2, above J4 and C6
        style(r, h=0.9); r.SetPosition(mm(x2, y2 + 1.75))
    elif ref == "R6":                             # left is J2: keep above
        style(r); r.SetPosition(mm((x1 + x2) / 2, y1 - 2.37))
    else:
        style(r, align=pcbnew.GR_TEXT_H_ALIGN_RIGHT)
        r.SetPosition(mm(x1 - 1.1, y1))


def label(text, x, y, h=1.2):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text)
    style(t, h=h)
    t.SetPosition(mm(x, y))
    b.Add(t)


# polarity: J1 battery (pin 1 = +), J4 servo
(xp, yp), (xm, _) = at(fps["J1"], "1"), at(fps["J1"], "2")
label("+", xp, 12.4); label("-", xm, 12.4)
# LM2596 module on the PCB (J7 = OUT side left, J6 = IN side right)
for ref, sx, tag in (("J7", 1, "OUT"), ("J6", -1, "IN")):        # LM2596 on the PCB: pad names inside the outline
    for pad, sign in (("1", "+"), ("2", "-")):
        x, y = at(fps[ref], pad)
        t = pcbnew.PCB_TEXT(b); t.SetText(tag + sign)
        style(t, h=1.0, align=pcbnew.GR_TEXT_H_ALIGN_LEFT if sx > 0 else pcbnew.GR_TEXT_H_ALIGN_RIGHT)
        dy = {("J7", "2"): 3.6, ("J6", "1"): -3.6}.get((ref, pad), 0)   # beside the M3 hole: shift off it
        t.SetPosition(mm(x + sx * 2.0, y + dy)); b.Add(t)
(xo, yo), (xi, _) = at(fps["J7"], "1"), at(fps["J6"], "1")
label("LM2596: eerst 5,0 V instellen", (xo + xi) / 2, yo - 4.0, h=1.0)
x, y = at(fps["J4"], "3")
fps["J4"].Reference().SetPosition(mm(x, y + 2.7))   # above J4 sits the R42 label
for pad, text in (("1", "-"), ("2", "+"), ("3", "S")):
    x, y = at(fps["J4"], pad)
    label(text, x + 2.6, y, h=1.0)

# TB6612 module: pin names next to both rows, so the module goes in the right way round
ROW1 = ["VM", "VCC", "GND", "AO1", "AO2", "BO2", "BO1", "GND"]
ROW2 = ["PWMA", "AIN2", "AIN1", "STBY", "BIN1", "BIN2", "PWMB", "GND"]
for ref, names, dx, al in (("J8", ROW1, 2.0, pcbnew.GR_TEXT_H_ALIGN_LEFT), ("J9", ROW2, -2.0, pcbnew.GR_TEXT_H_ALIGN_RIGHT)):
    for k, nm in enumerate(names, start=1):
        x, y = at(fps[ref], str(k))
        t = pcbnew.PCB_TEXT(b); t.SetText(nm); style(t, h=1.0, align=al)
        t.SetPosition(mm(x + dx, y)); b.Add(t)
x8, y8 = at(fps["J8"], "8"); x9, _ = at(fps["J9"], "8")
label("TB6612", (x8 + x9) / 2, y8 + 3.0, h=1.2)

# ESP32 DevKit: orientation, rotated 180 deg puts VIN/GND on GPIOs
(xa, ya), (xb, yb) = at(fps["J2"], "1"), at(fps["J3"], "15")
label("ANTENNE", (xa + xb) / 2, ya - 2.6, h=1.2)
label("USB", (xa + xb) / 2, yb + 3.0, h=1.2)

# mounting-hole references sit 4.15 mm above the hole, outside the outline for the two top holes: hide all four
for ref in ("H1", "H2", "H3", "H4"):
    fps[ref].Reference().SetVisible(False)
# the pin-1 triangle of the motor terminals M1/M2 sticks 0.3 mm past the board edge (silk_edge_clearance): drop it.
# Collected here, removed last (after Remove() this pcbnew build returns bare SwigPyObjects).
TRI = []
for ref in ("M1", "M2"):
    for g in items(fps[ref].GraphicalItems()):
        if g.GetLayer() == pcbnew.F_SilkS and pcbnew.Cast_to_PCB_SHAPE(g).GetShape() == pcbnew.SHAPE_T_POLY:
            TRI.append((fps[ref], g))

for parent, t in OLD:
    parent.Remove(t)
for parent, g in TRI:
    parent.Remove(g)
b.Save(str(PCB))
