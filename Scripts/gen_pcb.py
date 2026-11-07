"""Genereert KiCad/DIY-Auto.kicad_pcb — bordrand, montagegaten en plaatsing van alle onderdelen, nog zonder sporen.

Draaien (vanuit de projectmap, met de systeem-Python want die heeft pcbnew):
    kicad-cli sch export netlist -o KiCad/DIY-Auto.net KiCad/DIY-Auto.kicad_sch
    python3 Scripts/gen_pcb.py
Controleren en exporteren:
    kicad-cli pcb drc KiCad/DIY-Auto.kicad_pcb
    kicad-cli pcb export step --subst-models -o KiCad/DIY-Auto.step KiCad/DIY-Auto.kicad_pcb

Het script overschrijft DIY-Auto.kicad_pcb. Sporen die je in KiCad trekt, gaan dan verloren.
Maten in mm, oorsprong linksboven op het bord, y naar beneden.
"""
import re
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "KiCad" / "DIY-Auto.net"
OUT = ROOT / "KiCad" / "DIY-Auto.kicad_pcb"
FPDIR = Path("/usr/share/kicad/footprints")

W, H = 100.0, 70.0          # bordmaat
O = (100.0, 100.0)          # plaats van het bord op het KiCad-blad
HOLE = 3.5                  # afstand van montagegat tot rand (M3)
ROW = 25.4                  # afstand tussen de twee headerrijen van de DevKit: METEN (22,86 of 25,4)
Y1 = H - 7 - 14 * 2.54      # pin 1 van J2/J3; pin 15 (USB-kant) ligt 7 mm van de onderrand
MOD_ROW = 15.24             # SparkFun ROB-14451 .brd (v11): JP1 x 2.54, JP2 x 17.78; pin order = J8/J9, VM tegenover PWMA


# --- netlist inlezen ---------------------------------------------------------
def sexp(s):
    st = [[]]
    for t in re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s):
        if t == "(":
            st.append([])
        elif t == ")":
            x = st.pop()
            st[-1].append(x)
        else:
            st[-1].append(t.strip('"'))
    return st[0][0]

def find(l, k):
    return [x for x in l if isinstance(x, list) and x and x[0] == k]

def val(l, k):
    r = find(l, k)
    return r[0][1] if r else None

d = sexp(NET.read_text())
comps = {val(c, "ref"): (val(c, "value"), val(c, "footprint"), val(c, "tstamps"))
         for c in find(find(d, "components")[0], "comp")}
nets = {val(n, "name"): [(val(x, "ref"), val(x, "pin")) for x in find(n, "node")]
        for n in find(find(d, "nets")[0], "net")}


# --- plaatsing ---------------------------------------------------------------
# ref -> (x, y, rotatie in graden). x, y = pad 1.
P = {
    # voeding, linksboven
    "J1": (15.5, 6, 180),   # 180°: draadopening naar de bovenrand (rev 3: geen SW1 meer; rev 5: geen zekering F1)
    "C1": (5.5, 19, 270), "C2": (3, 30, 270),
    # accumeting, links van de DevKit
    "R41": (3, 38, 270), "R42": (7, 38, 270), "C6": (3, 52, 270),
    # DevKit
    "J2": (14, Y1, 0), "J3": (14 + ROW, Y1, 0),    # 5 V + servo (added with the electronics subassembly): JST-XH to the LM2596, servo header at the front edge
    # LM2596 module on the PCB (2026-11-05), centre (63.6, 56.5): J7 = OUT side (pad 1 OUT+), J6 = IN side (pad 1 IN+), pads 39.497 x 17.145 (Handsontec drawing)
    "J7": (63.6 - 19.75, 56.5 + 8.57, 0), "J6": (63.6 + 19.75, 56.5 + 8.57, 0), "C7": (76, 34, 0),
    "J4": (9, 52, 0),
    "D1": (18, 56, 0), "R6": (18, 61, 0),   # lying flat under the DevKit (≈3 mm high, room ≈6 mm)
}

# TB6612-module: logicarij (J9) naar de DevKit, VM/motorrij (J8) naar de motorklemmen, pin 1 bovenaan
P["J9"] = (56, 6, 0)
P["J8"] = (56 + MOD_ROW, 6, 0)
P["R7"] = (44, 28, 0)                      # STBY-pull-down, onder de module
for n in (1, 2):
    fy = (lambda y: y) if n == 1 else (lambda y: H - y)
    P[f"C{n}50"] = (83.5, fy(22), 90) if n == 1 else (88, 56, 270)   # C250 beside the LM2596 module
    P[f"M{n}"] = (95, fy(22), 90)          # 90°: draadopening naar de rechterrand

missing = set(comps) - set(P)
assert not missing, f"geen plaats voor {sorted(missing)}"


# --- bord opbouwen -----------------------------------------------------------
def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(O[0] + x), pcbnew.FromMM(O[1] + y))

def load_fp(libfp):
    lib, name = libfp.split(":")
    d = ROOT / "KiCad" if lib == "DIY-Auto" else FPDIR          # project footprints (mini buck)
    fp = pcbnew.FootprintLoad(str(d / f"{lib}.pretty"), name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

b = pcbnew.NewBoard(str(OUT))

netobj = {}
for name in nets:
    ni = pcbnew.NETINFO_ITEM(b, name)
    b.Add(ni)
    netobj[name] = ni
pin2net = {(r, p): n for n, nodes in nets.items() for r, p in nodes}

for ref, (value, libfp, tstamp) in comps.items():
    fp = load_fp(libfp)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPath(pcbnew.KIID_PATH(f"/{tstamp}"))   # koppeling met het schema, zodat F8 geen dubbels maakt
    x, y, rot = P[ref]
    fp.SetPosition(mm(x, y))
    fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        n = pin2net.get((ref, pad.GetNumber()))
        if n:
            pad.SetNet(netobj[n])
    b.Add(fp)

for i, (x, y) in enumerate([(HOLE, HOLE), (W - HOLE, HOLE), (W - HOLE, H - HOLE), (HOLE, H - HOLE)], 1):
    fp = load_fp("MountingHole:MountingHole_3.2mm_M3")
    fp.SetReference(f"H{i}")
    fp.SetBoardOnly(True)                        # staat niet in het schema; F8 mag hem niet wissen
    fp.SetPosition(mm(x, y))
    b.Add(fp)

edge = pcbnew.PCB_SHAPE(b)
edge.SetShape(pcbnew.SHAPE_T_RECT)
edge.SetStart(mm(0, 0))
edge.SetEnd(mm(W, H))
edge.SetLayer(pcbnew.Edge_Cuts)
edge.SetWidth(pcbnew.FromMM(0.1))
b.Add(edge)

b.Save(str(OUT))
print(f"OK: {len(comps)} onderdelen + 4 montagegaten, bord {W:g} x {H:g} mm -> {OUT.name}")
