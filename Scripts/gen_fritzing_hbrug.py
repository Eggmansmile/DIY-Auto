"""LEERVERSIE met de eigen H-bruggen (rev 3). De print (rev 4, TB6612) staat in gen_fritzing.py.

Fritzing-sketch (voeding 2S 7,4 V + 5 V, H-brug A, H-brug B op een tweede bord, ESP32, servo) en breadboardtekeningen,
gecontroleerd tegen de KiCad-netlist.

Draaien:  python3 Scripts/gen_fritzing_hbrug.py      (controleert tegen KiCad/DIY-Auto_rev3.net)      (alleen standaardbibliotheek; Fritzing-Flatpak nodig)
Schrijft: Fritzing/DIY-Auto_hbrug.fzz, ../../Assets/DIY-Auto_breadboard_v3b.png (bouwstappen), ../../Assets/DIY-Auto_breadboard-overzicht_v3b.png

Fritzing (Flatpak) exporteert zelf de SVG; dit script voegt daarna labels toe en vaagt per bouwstap weg wat al op het bord stond.
"""
import math, os, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
NETLIST = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "KiCad/DIY-Auto_rev3.net"
FZZ = HERE / "Fritzing/DIY-Auto_hbrug.fzz"
ASSETS = HERE.parent.parent / "Assets"
APP = "org.fritzing.Fritzing"                                 # Flatpak (flathub), 0.9.6
PARTS = Path(os.environ.get("FRITZING_PARTS") or
             Path(subprocess.run(["flatpak", "info", "--user", "--show-location", APP],
                                 capture_output=True, text=True).stdout.strip()) / "files/share/fritzing/parts")
BBSVG = PARTS / "svg/core/breadboard"

# ------------------------------------------------------------------ svg-hulp
def svg_info(text):
    root = re.search(r"<svg[^>]*>", text, re.S).group(0)
    g = lambda a: re.search(r"\b" + a + r'="([^"]*)"', root).group(1)
    vb = [float(x) for x in g("viewBox").split()]
    w = g("width")
    if w.endswith("in"): win = float(w[:-2])
    elif w.endswith("mm"): win = float(w[:-2]) / 25.4
    else: win = float(w.replace("px", "")) / (72 if "Illustrator" in text[:600] else 90)
    k = win * 90 / vb[2]                        # Fritzing-scène: 90 px per inch
    return k, vb[2] * k, vb[3] * k

def svg_legs(text):
    k, w, h = svg_info(text)
    out = {}
    for m in re.finditer(r'<line[^>]*id="(connector\d+)leg"[^>]*>', text):
        t = m.group(0); f = lambda a: float(re.search(r"\b" + a + r'="([^"]*)"', t).group(1)) * k
        p1, p2 = (f("x1"), f("y1")), (f("x2"), f("y2"))
        c = (w / 2, h / 2)                      # aanhechtpunt = het uiteinde dichtst bij het lijf
        out[m.group(1)] = p1 if math.dist(p1, c) < math.dist(p2, c) else p2
    return out, w, h

def svg_pins(text):
    k, w, h = svg_info(text)
    out = {}
    for m in re.finditer(r'<(rect|circle)[^>]*id="(connector\d+)pin"[^>]*>', text):
        t = m.group(0); f = lambda a: float(re.search(r"\b" + a + r'="([^"]*)"', t).group(1)) * k
        out[m.group(2)] = (f("cx"), f("cy")) if m.group(1) == "circle" else (f("x") + f("width") / 2, f("y") + f("height") / 2)
    return out, w, h

# ------------------------------------------------------------------ breadboard (RSR 03MB102, 63 kolommen)
bbtext = (BBSVG / "breadboard2.svg").read_text(errors="ignore")
K = svg_info(bbtext)[0]
HOLES = {}
for m in re.finditer(r'<g id="pin(\d+)([A-Z])">(.*?)</g>', bbtext, re.S):
    c = re.search(r'cx="([\d.]+)" cy="([\d.]+)"', m.group(3))
    HOLES[m.group(2) + m.group(1)] = (float(c.group(1)) * K, float(c.group(2)) * K)
# Rijen van boven naar onder: Z(GND) Y(+11V) | J I H G F | gleuf | E D C B A | X(GND) W(ongebruikt)
ROWY = {r: HOLES[r + "3"][1] for r in "ZYXW"} | {r: HOLES[r + "1"][1] for r in "JIHGFEDCBA"}
# bord 2 (H-brug B) ligt DY2 lager, onder de ESP32; zijn gaten krijgen het achtervoegsel b (J13b)
DY2 = 560
HOLES |= {n + "b": (x, y + DY2) for n, (x, y) in list(HOLES.items())}
def hsplit(h):
    m = re.fullmatch(r"([A-Z])(\d+)(b?)", h); return m.group(1), int(m.group(2)), m.group(3)
STREET = {"top": -16, "ZY": 13.5, "YJ": 31.5, "JI": 49.5, "IH": 58.5, "HG": 67.5, "GF": 76.5, "gap": 94.5,
          "ED": 112.5, "DC": 121.5, "CB": 130.5, "BA": 139.5, "AX": 157.5, "XW": 175.5}
def X(col): return HOLES["A1"][0] + 9 * (col - 1)
def Yv(y): return STREET[y] if isinstance(y, str) and y in STREET else (ROWY[y] if isinstance(y, str) else y)
def G(col, y, b=""): return (X(col), Yv(y) + (DY2 if b else 0))      # rasterpunt: kolom (mag x,5 zijn) + rij of straat
def pt(p): return HOLES[p] if isinstance(p, str) else p

# ------------------------------------------------------------------ onderdelen
CORE = {  # soort: (moduleId, fzp, breadboard-svg)
    "res":  ("ResistorModuleID", "resistor.fzp", "resistor_220.svg"),
    "cap":  ("100milCeramicCapacitorModuleID", "capacitor_ceramic_100mil.fzp", "ceramic_capacitor_blue_leg.svg"),
    "elco": ("MediumElectrolyticCapacitorModuleID", "capacitor_electrolytic_medium.fzp", "electrolytic_capacitor_220uF_35v_leg.svg"),
    "nfet": ("1001ABDC04", "basic_fet_n.fzp", "mosfet_n_channel.svg"),
    "pfet": ("1001ABDC27", "basic_fet_p.fzp", "mosfet_p_channel.svg"),
    "npn":  ("NPN-to92-ebc", "transistor_signal_NPN_TO92_EBC.fzp", "transistor_npn.svg"),
    "ledr": ("5mmColorLEDModuleID", "LED-generic-5mm.fzp", "LED-5mm-red-leg.svg"),
    "motor": ("1000FADF10011leg", "dc_motor.fzp", "dc_motor_leg.svg"),
    "diode": ("145554CBFC44diode", "diode_schottky_1N5817_300mil.fzp", "diode.svg"),   # 1N5817-beeld, label 1N5819
}
# KiCad-pinnummer -> Fritzing-connector
PINMAP = {"res": {"1": "connector0", "2": "connector1"}, "cap": {"1": "connector0", "2": "connector1"},
          "elco": {"1": "connector1", "2": "connector0"},          # KiCad 1 = +
          "nfet": {"1": "connector0", "2": "connector1", "3": "connector2"},
          "pfet": {"1": "connector0", "2": "connector1", "3": "connector2"},
          "npn": {"1": "connector0", "2": "connector1", "3": "connector2"},   # E B C
          "ledr": {"K": "connector0", "A": "connector1"},
          "motor": {"1": "connector0", "2": "connector1"},
          "diode": {"1": "connector0", "2": "connector1"}}                # KiCad 1 = K, 2 = A

PARTS_L = []     # dict(ref, kind, pins{kicadpin: gat}, rot, pos, step, label, props, test)
def part(ref, kind, pins, step, label, rot=0, body=None, props=None, test=False):
    PARTS_L.append(dict(ref=ref, kind=kind, pins=pins, step=step, label=label, rot=rot, body=body,
                        props=props or {}, test=test))

WIRES = []       # dict(pts, color, step, a, b)   a/b = gatnaam of ("ESP", pin) / ("BAT", pol)
def wire(pts, color, step, a=None, b=None):
    WIRES.append(dict(pts=[pt(p) for p in pts], color=color, step=step,
                      a=a if a is not None else pts[0], b=b if b is not None else pts[-1]))
def U(a, b, via, color, step):
    """Draad van gat a naar gat b via een straat (horizontaal tussen twee rijen)."""
    wire([a, G(hsplit(a)[1], via, hsplit(a)[2]), G(hsplit(b)[1], via, hsplit(b)[2]), b], color, step)

RED, BLK, BLU, GRY = "#d32f2f", "#1a1a1a", "#1565c0", "#8c8c8c"
ORA, TEAL = "#ef6c00", "#00897b"                             # +5 V, servosignaal
S_PWR, S_5V, S_HI, S_LO, S_ESP, S_MOT, S_SERVO, S_B, S_BMOT = 1, 2, 3, 4, 5, 6, 7, 8, 9   # bouwstappen

def half_bridge(c, side, gp_hi, gp_lo, b="", s_hi=S_HI, s_lo=S_LO):
    """Halve H-brug: P-MOSFET boven (poten in rij J, lijf over de rails),
    2N3904 en N-MOSFET onder (180° gedraaid, poten in rij A, lijf over de onderste rails)."""
    k = "2" if b else "1"                                   # refs 1xx = brug A, 2xx = brug B
    s = [k + d for d in {"L": ("01", "02", "03", "04", "05"), "R": ("11", "12", "13", "14", "15")}[side]]
    qp, qn, qd = "Q" + s[0], "Q" + s[2], "Q" + s[1]
    rpu, rb, rbd, rg, rgd = "R" + s[0], "R" + s[1], "R" + s[2], "R" + s[3], "R" + s[4]
    n = c + 8
    # ---- hoge kant
    # TO-220-poten buig je niet: alle drie recht in rij J, S met een draadje naar de +rail (om het S-gat heen)
    part(qp, "pfet", {"1": f"J{c}{b}", "2": f"J{c+1}{b}", "3": f"J{c+2}{b}"}, s_hi, "IRF9540N")
    wire([f"I{c+2}{b}", G(c + 2.5, "I", b), G(c + 2.5, "Y", b), f"Y{c+3}{b}"], RED, s_hi)
    part(rpu, "res", {"1": f"I{c-4}{b}", "2": f"I{c}{b}"}, s_hi, "5k1", props={"resistance": "5100"})
    wire([f"Y{c-4}{b}", f"J{c-4}{b}"], RED, s_hi)                                                    # +7,4 V naar de pull-up
    part(qd, "npn", {"3": f"A{c}{b}", "2": f"A{c+1}{b}", "1": f"X{c+4}{b}"}, s_hi, "2N3904", rot=180)   # E-poot recht in de GND-rail
    wire([f"F{c}{b}", f"E{c}{b}"], GRY, s_hi)                                                        # collector -> gate P-MOSFET
    # basisweerstand + pull-down
    b_in = c + 5
    part(rb, "res", {("1" if side == "L" else "2"): f"C{b_in}{b}", ("2" if side == "L" else "1"): f"C{c+1}{b}"}, s_hi, "5k1",
         props={"resistance": "5100"})
    part(rbd, "res", {"1": f"B{c+1}{b}", "2": f"B{c-3}{b}"}, s_hi, "20k", props={"resistance": "20000"})
    wire([f"A{c-3}{b}", f"X{c-3}{b}"], BLK, s_hi)
    # ---- lage kant
    part(qn, "nfet", {"3": f"A{n}{b}", "2": f"A{n+1}{b}", "1": f"A{n+2}{b}"}, s_lo, "IRLZ44N", rot=180)   # recht, S = A{n}
    wire([f"B{n}{b}", G(n - 0.5, "B", b), G(n - 0.5, "X", b), f"X{n-2}{b}"], BLK, s_lo)                   # S -> GND-rail, naast het lijf
    g_in = n + 6
    part(rg, "res", {("1" if side == "L" else "2"): f"C{g_in}{b}", ("2" if side == "L" else "1"): f"C{n+2}{b}"}, s_lo, "1k",
         props={"resistance": "1000"})
    part(rgd, "res", {"1": f"B{g_in}{b}", "2": f"B{g_in+4}{b}"}, s_lo, "20k", props={"resistance": "20000"})
    wire([f"A{g_in+4}{b}", f"X{g_in+4}{b}"], BLK, s_lo)
    # motorknoop: drain boven (J{c+1}) -> bovenste strip m; strip m boven en onder verbonden; drain onder zit al in strip n+1
    m = n + 1
    U(f"G{c+1}{b}", f"G{m}{b}", "GF", GRY, s_lo)
    wire([f"F{m}{b}", f"E{m}{b}"], GRY, s_lo)
    return dict(hi=b_in, lo=g_in, m=m, gp_hi=gp_hi, gp_lo=gp_lo)

# --- stap 1: voeding 7,4 V.  Accu 2S (JST BEC) -> Y3 (+) en Z3 (GND); de zekering F1 komt pas op de print.  Z en X rechts verbonden.
part("C2", "cap", {"1": "Y43", "2": "Z43"}, S_PWR, "100nF", rot=90)
part("C1", "elco", {"1": "Y47", "2": "Z47"}, S_PWR, "470µF 16V", rot=90)
wire(["Z61", G(65, "Z"), G(65, "X"), "X61"], BLK, S_PWR)
# --- stap 2: 5 V.  De onderste rode rail (W) wordt +5 V van de LM2596.
part("C7", "cap", {"1": "W52", "2": "X52"}, S_5V, "100nF", rot=90)

LB = half_bridge(13, "L", "GPIO25", "GPIO27")
RB = half_bridge(37, "R", "GPIO26", "GPIO13")

# --- stap 4: testlast tussen M+ (strip 22) en M− (strip 46): 1 kΩ + rode en groene led antiparallel
N1, N2 = 30, 29
U("I22", "I26", "IH", GRY, S_ESP)
part("R_T", "res", {"1": "H26", "2": f"H{N1}"}, S_ESP, "1k", props={"resistance": "1000"}, test=True)
part("LED_R", "ledr", {"A": f"J{N1}", "K": f"J{N2}"}, S_ESP, "rood: vooruit", test=True)
part("LED_G", "ledr", {"A": f"F{N2}", "K": f"F{N1}"}, S_ESP, "groen: achteruit", rot=180,
     props={"color": "Green (570nm)"}, test=True)
U(f"I{N2}", "I46", "JI", GRY, S_ESP)

# --- stap 5: motor in plaats van de testlast (boven het bord); motor B idem boven bord 2
_ma, _mw, _mh = svg_legs((BBSVG / CORE["motor"][2]).read_text(errors="ignore"))
MOTORS = [dict(ref="M1", b="", step=S_MOT, label="MOTOR A · pas na de ledtest"),
          dict(ref="M2", b="b", step=S_BMOT, label="MOTOR B · eerst de testlast op D22 en D46")]
for M in MOTORS:
    dy = DY2 if M["b"] else 0
    M.update(pos=(X(31) - 75, -150 + dy), att=_ma, w=_mw, h=_mh)
    m0, m1 = [(M["pos"][0] + _ma[c][0], M["pos"][1] + _ma[c][1]) for c in ("connector0", "connector1")]
    wire([m0, (X(21.5), m0[1]), G(21.5, "YJ", M["b"]), G(22, "YJ", M["b"]), f"J22{M['b']}"], "#6d4c41", M["step"],
         a=("MOT", M["ref"], "1"))
    wire([m1, (m1[0] - 8, m1[1]), (m1[0] - 8, -22 + dy), (X(45.5), -22 + dy), G(45.5, "YJ", M["b"]), G(46, "YJ", M["b"]),
          f"J46{M['b']}"], "#6d4c41", M["step"], a=("MOT", M["ref"], "2"))

# --- stap 8: H-brug B op bord 2, zelfde layout.  Rails van bord 2 gevoed vanaf bord 1 (rechts langs de borden).
LB2 = half_bridge(13, "L", "GPIO32", "GPIO4", "b", S_B, S_B)
RB2 = half_bridge(37, "R", "GPIO33", "GPIO18", "b", S_B, S_B)
wire(["Y61", G(67, "Y"), G(67, "Y", "b"), "Y61b"], RED, S_B)
wire(["X59", G(59, "XW"), G(69, "XW"), G(69, "XW", "b"), G(61, "XW", "b"), "X61b"], BLK, S_B)

# ------------------------------------------------------------------ ESP32 en accu (eigen onderdelen)
ESP_POS = (250, 258)            # linkerbovenhoek van de DevKit (scène)
# bovenste rij, van links naar rechts (DevKit 90° gedraaid, USB links, antenne rechts): J2.15 .. J2.1
J2 = ["EN", "VP", "VN", "D34", "D35", "D32", "D33", "D25", "D26", "D27", "D14", "D12", "D13", "GND", "VIN"]
J3 = ["D23", "D22", "TX0", "RX0", "D21", "D19", "D18", "D5", "TX2", "RX2", "D4", "D2", "D15", "GND", "3V3"]
ESP_W, ESP_H, ESP_ROWGAP = 2.1 * 90, 1.12 * 90, 0.9 * 90
def esp_pin_xy(row, i):         # row 0 = J2 (boven), i = pinnummer 1..15
    x0 = (ESP_W - 14 * 9) / 2
    x = x0 + (15 - i) * 9
    y = (ESP_H - ESP_ROWGAP) / 2 + (ESP_ROWGAP if row else 0)
    return (ESP_POS[0] + x, ESP_POS[1] + y)
ESP_KICAD = {"GPIO25": 8, "GPIO26": 9, "GPIO27": 10, "GPIO13": 13, "GND": 14, "VIN": 15, "GPIO19": 21,
             "GPIO32": 6, "GPIO33": 7, "GPIO18": 22, "GPIO4": 26}   # 16..30 = J3.1..15
def esp_ref(i): return f"J2.{i}" if i <= 15 else f"J3.{i - 15}"

def esp_wire(gpio, col, lane, street_dx, color):
    p = esp_pin_xy(0, ESP_KICAD[gpio])
    xs = X(col + street_dx)
    wire([p, (p[0], lane), (xs, lane), (xs, STREET["gap"]), (X(col), STREET["gap"]), HOLES[f"E{col}"]],
         color, S_ESP, a=("ESP", ESP_KICAD[gpio]), b=f"E{col}")
esp_wire("GPIO25", LB["hi"], 238, -0.5, "#f9a825")
esp_wire("GPIO27", LB["lo"], 230, -0.5, BLU)
esp_wire("GPIO26", RB["hi"], 222, -0.5, "#2e7d32")
esp_wire("GPIO13", RB["lo"], 214, -0.5, "#8e24aa")
# stap 9: brug B.  Van de pin naar een laan, rechts langs de borden naar beneden, onder bord 2 terug naar links
# en van onderen in rij E (zelfde laatste stuk als bij bord 1).
B_COL = {"GPIO32": "#c0ca33", "GPIO4": "#00acc1", "GPIO33": "#ec407a", "GPIO18": "#a1887f"}
def esp_wire2(gpio, col, lane, xv, lane2):
    i = ESP_KICAD[gpio]; p = esp_pin_xy(0 if i <= 15 else 1, i if i <= 15 else i - 15)
    xs = X(col - 0.5)
    wire([p, (p[0], lane), (X(xv), lane), (X(xv), DY2 + lane2), (xs, DY2 + lane2), (xs, DY2 + STREET["gap"]),
          (X(col), DY2 + STREET["gap"]), HOLES[f"E{col}b"]], B_COL[gpio], S_BMOT, a=("ESP", i), b=f"E{col}b")
esp_wire2("GPIO32", LB2["hi"], 202, 74, 238)
esp_wire2("GPIO33", RB2["hi"], 208, 73, 222)
esp_wire2("GPIO4", LB2["lo"], 377, 71, 230)
esp_wire2("GPIO18", RB2["lo"], 370, 72, 214)
pg = esp_pin_xy(0, 14)
wire([pg, (pg[0], 244), (X(5.5), 244), (X(5.5), ROWY["X"]), HOLES["X5"]], BLK, S_ESP, a=("ESP", 14), b="X5")
# VIN: +5 V-rail -> D1 (anode kolom 8, kathode kolom 4) -> VIN.  Geen powerbank meer.
part("D1", "diode", {"1": "C4", "2": "C8"}, S_ESP, "1N5819")
wire(["A8", (X(8), ROWY["W"]), "W9"], ORA, S_ESP)
pv = esp_pin_xy(0, 15)
wire([pv, (pv[0], 251), (X(4.5), 251), (X(4.5), STREET["AX"]), G(4, "AX"), "A4"], ORA, S_ESP, a=("ESP", 15), b="A4")

BAT_POS = (-250, -95)
BAT_W, BAT_H = 150, 60
BAT_PLUS, BAT_MIN = (BAT_POS[0] + BAT_W, BAT_POS[1] + 20), (BAT_POS[0] + BAT_W, BAT_POS[1] + 40)

# ------------------------------------------------------------------ eigen modules buiten het bord (LM2596, servo)
MODS = {}
def module(key, title, pos, w, h, pins, step, label, fill):
    """pins: [(naam, (x, y) lokaal, kleur)]"""
    MODS[key] = dict(id=f"DIYAuto_{key}", title=title, pos=pos, w=w, h=h, pins=pins, step=step, label=label, fill=fill)
def mp(key, name):
    m = MODS[key]; lx, ly = next(q for n, q, _ in m["pins"] if n == name)
    return (m["pos"][0] + lx, m["pos"][1] + ly)
MODNET = {("BUCK", "IN+"): "J6.1", ("BUCK", "IN-"): "J6.2",
          ("BUCK", "OUT+"): "J7.1", ("BUCK", "OUT-"): "J7.2", ("SERVO", "GND"): "J4.1", ("SERVO", "+5V"): "J4.2",
          ("SERVO", "SIG"): "J4.3"}

# stap 2: LM2596 links onder het bord
module("BUCK", "LM2596", (-160, 140), 120, 50,
       [("IN+", (120, 10), RED), ("IN-", (120, 20), BLK), ("OUT-", (120, 31), BLK), ("OUT+", (120, 40), ORA)], S_5V,
       "LM2596 · eerst 5,0 V afstellen, dan OUT aansluiten", "#1f4e8c")
# stap 7: servo rechts onder het bord (bruin GND, rood +5 V, oranje signaal)
module("SERVO", "SERVO", (528, 215), 75, 40,
       [("GND", (X(59.5) - 528, 0), BLK), ("+5V", (X(61) - 528, 0), ORA), ("SIG", (X(62) - 528, 0), TEAL)], S_SERVO,
       "servo SM-S2309S", "#37474f")
MODS["SERVO"]["short"] = {"GND": "−", "+5V": "+", "SIG": "S"}

# accu rechtstreeks op de bovenste rails (JST BEC); op de print zit F1 ertussen
wire([BAT_PLUS, (-25, BAT_PLUS[1]), (-25, ROWY["Y"]), HOLES["Y3"]], RED, S_PWR, a=("BAT", "+"), b="Y3")
wire([BAT_MIN, (-35, BAT_MIN[1]), (-35, ROWY["Z"]), HOLES["Z3"]], BLK, S_PWR, a=("BAT", "-"), b="Z3")

_b = lambda n: mp("BUCK", n)
wire([_b("IN+"), (-15, _b("IN+")[1]), (-15, STREET["YJ"]), G(4, "YJ"), "Y4"], RED, S_5V, a=("MOD", "BUCK", "IN+"), b="Y4")
wire([_b("IN-"), (X(3.5), _b("IN-")[1]), (X(3.5), ROWY["X"]), "X4"], BLK, S_5V, a=("MOD", "BUCK", "IN-"), b="X4")
wire([_b("OUT-"), "X3"], BLK, S_5V, a=("MOD", "BUCK", "OUT-"), b="X3")
wire([_b("OUT+"), "W3"], ORA, S_5V, a=("MOD", "BUCK", "OUT+"), b="W3")

# stap 7: GPIO19 -> R6 (kolom 58 -> 62) -> servosignaal
part("R6", "res", {"1": "C58", "2": "C62"}, S_SERVO, "1k", props={"resistance": "1000"})
p19 = esp_pin_xy(1, 6)
wire([p19, (p19[0], p19[1] + 14), (X(57.5), p19[1] + 14), (X(57.5), STREET["AX"]), G(58, "AX"), "A58"], TEAL, S_SERVO,
     a=("ESP", 21), b="A58")
_s = lambda n: mp("SERVO", n)
wire([_s("GND"), (X(59.5), ROWY["X"]), "X60"], BLK, S_SERVO, a=("MOD", "SERVO", "GND"), b="X60")
wire([_s("+5V"), "W61"], ORA, S_SERVO, a=("MOD", "SERVO", "+5V"), b="W61")
wire([_s("SIG"), "A62"], TEAL, S_SERVO, a=("MOD", "SERVO", "SIG"), b="A62")

# ------------------------------------------------------------------ geometrie van de onderdelen
def rot_apply(rot, w, h, p):
    if rot == 0: return p
    if rot == 180: return (w - p[0], h - p[1])
    if rot == 90: return (h - p[1], p[0])            # 90° met de klok mee (y naar onder)
def rot_inv(rot, w, h, q):
    if rot == 0: return q
    if rot == 180: return (w - q[0], h - q[1])
    if rot == 90: return (q[1], h - q[0])
def rot_matrix(rot, w, h):
    if rot == 180: return dict(m11=-1, m12=0, m21=0, m22=-1, m31=w, m32=h)
    if rot == 90: return dict(m11=0, m12=1, m21=-1, m22=0, m31=h, m32=0)

LEGLEN = {"res": 0, "cap": 4.5, "elco": 4.5, "nfet": 9, "pfet": 9, "npn": 7, "ledr": 9, "motor": 0, "diode": 0}
for p in PARTS_L:
    mod, fzp, svgf = CORE[p["kind"]]
    text = (BBSVG / svgf).read_text(errors="ignore")
    att, w, h = svg_legs(text)
    p.update(mod=mod, fzp=fzp, w=w, h=h, att=att)
    cmap = dict(PINMAP[p["kind"]])
    if p["kind"] in ("res", "cap"):   # symmetrisch: linker (of bovenste) gat naar connector0
        k1, k2 = sorted(p["pins"])
        (x1, y1), (x2, y2) = pt(p["pins"][k1]), pt(p["pins"][k2])
        if (x1, y1) > (x2, y2) if p["rot"] == 0 else y1 > y2:
            cmap = {k1: "connector1", k2: "connector0"}
        else:
            cmap = {k1: "connector0", k2: "connector1"}
    p["cmap"] = cmap
    targets = {cmap[k]: pt(v) for k, v in p["pins"].items()}
    if p["kind"] in ("res", "diode"):   # lijf horizontaal midden tussen de twee gaten
        (x1, y1), (x2, y2) = targets["connector0"], targets["connector1"]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        a0, a1 = att["connector0"], att["connector1"]
        p["pos"] = (mx - (a0[0] + a1[0]) / 2, my - a0[1])
    elif p["kind"] == "motor":
        p["pos"] = (X(31) - w / 2, -150)
    else:                            # lijf zo zetten dat de 'rechte' poten op de gaten van rij J/A/rails vallen
        ref_c = sorted(targets)[0]
        tx, ty = targets[ref_c]
        # lokaal eindpunt van een rechte poot (naar onder, lengte LEGLEN)
        a = att[ref_c]; e = (a[0], a[1] + LEGLEN[p["kind"]])
        if p["kind"] in ("nfet", "pfet", "npn"):
            # de middelste poot bepaalt x (de buitenste kan naar de rail gebogen zijn)
            ref_c = "connector1"; a = att[ref_c]; e = (a[0], a[1] + LEGLEN[p["kind"]]); tx, ty = targets[ref_c]
        if p["kind"] in ("cap", "elco") and p["rot"] == 90:
            ref_c = "connector0" if p["kind"] == "cap" else "connector1"
            a = att[ref_c]; e = (a[0], a[1] + LEGLEN[p["kind"]]); tx, ty = targets[ref_c]
        se = rot_apply(p["rot"], w, h, e)
        p["pos"] = (tx - se[0], ty - se[1])
    p["targets"] = targets
    p["legs"] = {}
    for c, (tx, ty) in targets.items():
        local_t = rot_inv(p["rot"], w, h, (tx - p["pos"][0], ty - p["pos"][1]))
        a = att[c]
        p["legs"][c] = (a, (local_t[0] - a[0], local_t[1] - a[1]))

# ------------------------------------------------------------------ controle 1: netten gelijk aan KiCad
def strip(h):
    r, c, b = hsplit(h)
    if r in "WXYZ": return "rail" + r + b
    return ("T" if r in "JIHGF" else "B") + str(c) + b
par = {}
def f(a):
    par.setdefault(a, a)
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
def join(a, b): par[f(a)] = f(b)
def node(e):
    if isinstance(e, tuple): return ".".join(map(str, e))
    return strip(e)
for wd in WIRES: join(node(wd["a"]), node(wd["b"]))
kinds_kicad = {}
nets = {}
for p in PARTS_L:
    if p["test"]: continue
    for kpin, h in p["pins"].items():
        nets.setdefault(f(strip(h)), set()).add(f"{p['ref']}.{kpin}")
for gpio, i in ESP_KICAD.items():
    nets.setdefault(f(f"ESP.{i}"), set()).add(esp_ref(i))
for (k_, n_), ref in MODNET.items():
    nets.setdefault(f(f"MOD.{k_}.{n_}"), set()).add(ref)
nets.setdefault(f("BAT.+"), set()).add("+BATT")            # accu + via F1 = +BATT (F1 niet op het breadboard)
nets.setdefault(f("BAT.-"), set()).add("J1.2")
for M in MOTORS:
    for k_ in ("1", "2"): nets.setdefault(f(f"MOT.{M['ref']}.{k_}"), set()).add(f"{M['ref']}.{k_}")

s = NETLIST.read_text(); body = s[s.find("(nets"):]
keep = {p["ref"] for p in PARTS_L if not p["test"]} | {M["ref"] for M in MOTORS} | {r.split(".")[0] for r in MODNET.values() if r[0] == "J" and r[:2] != "J1"}
kc = []
for m in re.finditer(r'\(net\s+\(code "?\d+"?\)\s+\(name "([^"]*)"\)(.*?)(?=\n\t\t\(net\s|\Z)', body, re.S):
    pins = {f"{r}.{n}" for r, n in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', m.group(2))}
    pins = {x for x in pins if x.split(".")[0] in keep or x in {esp_ref(i) for i in ESP_KICAD.values()} or x == "J1.2"}
    if m.group(1) == "+BATT": pins.add("+BATT")
    if len(pins) > 1: kc.append(frozenset(pins))
bb = [frozenset(v) for v in nets.values() if len(v) > 1]
missing, extra = set(kc) - set(bb), set(bb) - set(kc)
if missing or extra:
    print("FOUT: breadboard wijkt af van KiCad")
    for n_ in missing: print("  KiCad :", sorted(n_))
    for n_ in extra: print("  bord  :", sorted(n_))
    sys.exit(1)
print(f"OK: {len(bb)} netten identiek aan KiCad")

# testlast apart: M+ -> R_T -> N1 -> leds -> N2 -> M−
tl = {strip(h) for p in PARTS_L if p["test"] for h in p["pins"].values()}
assert f(strip("H22")) == f(strip("A22")) and f(strip("H46")) == f(strip("A46")), "testlast hangt niet aan M+/M−"

# ------------------------------------------------------------------ controle 2: geen gat dubbel, geen draad over een gat
used = {}
for p in PARTS_L:
    for h in p["pins"].values(): used.setdefault(h, []).append(p["ref"])
for i, wd in enumerate(WIRES):
    for e in (wd["a"], wd["b"]):
        if isinstance(e, str): used.setdefault(e, []).append(f"draad{i}")
dups = {k: v for k, v in used.items() if len(v) > 1}
def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)
cross = []
for i, wd in enumerate(WIRES):
    ends = {wd["a"], wd["b"]}
    for a, b in zip(wd["pts"], wd["pts"][1:]):
        for hn, hp in HOLES.items():
            if hn not in ends and seg_dist(hp, a, b) < 3.2: cross.append((f"draad{i} {wd['a']}->{wd['b']}", hn))
for p in PARTS_L:
    for c, (a, e) in p["legs"].items():
        A = (p["pos"][0], p["pos"][1]); pa = rot_apply(p["rot"], p["w"], p["h"], a); pe = rot_apply(p["rot"], p["w"], p["h"], (a[0] + e[0], a[1] + e[1]))
        A1, A2 = (A[0] + pa[0], A[1] + pa[1]), (A[0] + pe[0], A[1] + pe[1])
        tgt = [h for h in p["pins"] if p["cmap"][h] == c][0]
        for hn, hp in HOLES.items():
            if hn != p["pins"][tgt] and seg_dist(hp, A1, A2) < 3.2: cross.append((f"poot {p['ref']}.{tgt}", hn))
# lijven die een gebruikt gat bedekken
cover = []
for p in PARTS_L:
    x0, y0 = p["pos"]; w, h = (p["h"], p["w"]) if p["rot"] == 90 else (p["w"], p["h"])
    own = set(p["pins"].values())
    for hn in used:
        hx, hy = HOLES[hn]
        if hn not in own and x0 + 1 < hx < x0 + w - 1 and y0 + 1 < hy < y0 + h - 1: cover.append((p["ref"], hn))
if dups or cross or cover:
    for k_, v in dups.items(): print("FOUT: gat dubbel gebruikt:", k_, v)
    for c_ in cross: print("FOUT: loopt over gat:", c_)
    for c_ in cover: print("FOUT: lijf bedekt gebruikt gat:", c_)
    sys.exit(1)
print("OK: geen dubbele gaten, geen draad of poot over een gat, geen lijf over een gebruikt gat")

# ------------------------------------------------------------------ eigen onderdelen: ESP32 DevKit v1 (30 pins) en accu 2S
def u(px): return px / 0.9                          # scène-px -> 0,01 inch
ESP_ID, BAT_ID = "DIYAuto_ESP32_DevKitV1_30", "DIYAuto_Accu_2S"
def esp_svg():
    W, H = u(ESP_W), u(ESP_H)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W/100}in" height="{H/100}in" viewBox="0 0 {W} {H}"><g id="breadboard">',
         f'<rect x="0" y="0" width="{W}" height="{H}" rx="6" fill="#1b1f24"/>',
         f'<rect x="{W-72}" y="{H/2-34}" width="66" height="68" rx="2" fill="#b8bec4" stroke="#8a9096"/>',      # WROOM-schild
         f'<rect x="{W-24}" y="{H/2-34}" width="18" height="68" fill="#1b1f24"/>',
         f'<path d="M{W-20},{H/2-28} h10 v8 h-10 v8 h10 v8 h-10 v8 h10 v8 h-10 v8 h10" stroke="#d4af37" stroke-width="1.6" fill="none"/>',
         f'<text x="{W-45}" y="{H/2+3}" font-family="Droid Sans" font-size="5.5" fill="#333" text-anchor="middle">ESP-WROOM-32</text>',
         f'<rect x="-6" y="{H/2-12}" width="22" height="24" rx="2" fill="#c7c7c7" stroke="#888"/>',              # USB
         f'<rect x="40" y="{H/2-10}" width="14" height="10" fill="#444"/><circle cx="47" cy="{H/2-5}" r="3" fill="#222"/>',
         f'<rect x="40" y="{H/2+4}" width="14" height="10" fill="#444"/><circle cx="47" cy="{H/2+9}" r="3" fill="#222"/>',
         f'<text x="57" y="{H/2-3}" font-family="Droid Sans" font-size="5" fill="#fff">EN</text>',
         f'<text x="57" y="{H/2+11}" font-family="Droid Sans" font-size="5" fill="#fff">BOOT</text>',
         f'<text x="{W/2-8}" y="{H/2+3}" font-family="Droid Sans" font-size="9" fill="#fff" text-anchor="middle">ESP32 DevKit v1</text>']
    for row, names in ((0, J2), (1, J3)):
        for i, nm in enumerate(names, 1):
            x, y = esp_pin_xy(row, i); x, y = u(x - ESP_POS[0]), u(y - ESP_POS[1])
            cid = f"connector{(i - 1) + 15 * row}"
            o.append(f'<rect x="{x-4}" y="{y-4}" width="8" height="8" fill="#222" stroke="#d4af37" stroke-width="1.2"/>')
            o.append(f'<rect id="{cid}pin" x="{x-2}" y="{y-2}" width="4" height="4" fill="#d4af37"/>')
            ty = y + 7 if row == 0 else y - 7
            anc = "end" if row == 0 else "start"
            o.append(f'<text x="{x}" y="{y + 11 if row == 0 else y - 7}" font-family="Droid Sans" font-size="3.8" fill="#fff" '
                     f'text-anchor="middle">{nm}</text>')
    o.append("</g></svg>")
    return "".join(o)
def bat_svg():
    W, H = u(BAT_W), u(BAT_H)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W/100}in" height="{H/100}in" viewBox="0 0 {W} {H}"><g id="breadboard">',
         f'<rect x="0" y="0" width="{W-6}" height="{H}" rx="6" fill="#222"/>']
    # one shrink-wrapped pack (ERYNK 7,4 V 1500 mAh), not loose cells
    o.append(f'<rect x="8" y="6" width="{W-34}" height="{H-12}" rx="10" fill="#1e63c6"/>')
    o.append(f'<text x="{(W-26)/2+4}" y="{H/2-4}" font-family="Droid Sans" font-size="15" fill="#fff" text-anchor="middle">ACCU 7,4 V</text>')
    o.append(f'<text x="{(W-26)/2+4}" y="{H/2+14}" font-family="Droid Sans" font-size="10" fill="#dfe8f5" text-anchor="middle">1500 mAh · 2S Li-ion</text>')
    o.append(f'<rect x="{W-26}" y="{H/2-13}" width="14" height="26" rx="2" fill="#d32f2f"/>')       # red JST BEC plug
    o.append(f'<text x="{W-19}" y="{H/2+3}" font-family="Droid Sans" font-size="7" fill="#fff" text-anchor="middle">JST</text>')
    for cid, yy, col, lab in (("connector0", u(BAT_PLUS[1] - BAT_POS[1]), "#d32f2f", "+"), ("connector1", u(BAT_MIN[1] - BAT_POS[1]), "#1a1a1a", "−")):
        o.append(f'<rect x="{W-8}" y="{yy-5}" width="8" height="10" fill="{col}"/>')
        o.append(f'<rect id="{cid}pin" x="{W-2}" y="{yy-2}" width="2" height="4" fill="{col}"/>')
    o.append("</g></svg>")
    return "".join(o)
def box_svg(n, layer):               # eenvoudig schema-/pcb-beeld met n aansluitingen
    H = 30 + n * 10
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="0.6in" height="{H/100}in" viewBox="0 0 60 {H}"><g id="{layer}">',
         f'<rect x="10" y="5" width="40" height="{H-10}" fill="none" stroke="#000"/>']
    for i in range(n):
        o.append(f'<rect id="connector{i}pin" x="0" y="{15+i*10}" width="10" height="2" fill="#000"/>')
    o.append("</g></svg>")
    return "".join(o)
def fzp(mid, title, names, img):
    con = "".join(
        f'<connector id="connector{i}" name="{nm}" type="male"><description>{nm}</description><views>'
        f'<breadboardView><p layer="breadboard" svgId="connector{i}pin"/></breadboardView>'
        f'<schematicView><p layer="schematic" svgId="connector{i}pin"/></schematicView>'
        f'<pcbView><p layer="copper0" svgId="connector{i}pin"/></pcbView></views></connector>' for i, nm in enumerate(names))
    return (f'<?xml version="1.0" encoding="UTF-8"?><module fritzingVersion="0.9.6" moduleId="{mid}"><version>1</version>'
            f'<title>{title}</title><label>U</label><properties><property name="family">{title}</property></properties>'
            f'<views><iconView><layers image="breadboard/{img}.svg"><layer layerId="icon"/></layers></iconView>'
            f'<breadboardView><layers image="breadboard/{img}.svg"><layer layerId="breadboard"/></layers></breadboardView>'
            f'<schematicView><layers image="schematic/{img}.svg"><layer layerId="schematic"/></layers></schematicView>'
            f'<pcbView><layers image="pcb/{img}.svg"><layer layerId="copper0"/></layers></pcbView></views>'
            f'<connectors>{con}</connectors></module>')
ESP_NAMES = [f"J2.{i} {n}" for i, n in enumerate(J2, 1)] + [f"J3.{i} {n}" for i, n in enumerate(J3, 1)]
CUSTOM = {f"part.{ESP_ID}.fzp": fzp(ESP_ID, "ESP32 DevKit v1 (30 pins)", ESP_NAMES, ESP_ID),
          f"svg.breadboard.{ESP_ID}.svg": esp_svg(), f"svg.schematic.{ESP_ID}.svg": box_svg(30, "schematic"),
          f"svg.pcb.{ESP_ID}.svg": box_svg(30, "copper0"),
          f"part.{BAT_ID}.fzp": fzp(BAT_ID, "Accu 7,4 V 1500 mAh (ERYNK)", ["+", "-"], BAT_ID),
          f"svg.breadboard.{BAT_ID}.svg": bat_svg(), f"svg.schematic.{BAT_ID}.svg": box_svg(2, "schematic"),
          f"svg.pcb.{BAT_ID}.svg": box_svg(2, "copper0")}

def mod_svg(m):
    W, H = u(m["w"]), u(m["h"])
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W/100}in" height="{H/100}in" viewBox="0 0 {W} {H}"><g id="breadboard">',
         f'<rect x="0" y="0" width="{W}" height="{H}" rx="6" fill="{m["fill"]}"/>',
         f'<text x="{W/2 - (18 if any(q[0] >= m["w"] for _, q, _ in m["pins"]) else 0)}" y="{H/2+5 + (8 if any(q[1] <= 0 for _, q, _ in m["pins"]) else 0)}" '
         f'font-family="Droid Sans" font-size="13" fill="#fff" text-anchor="middle">{m["title"]}</text>']
    for i, (nm, (lx, ly), col) in enumerate(m["pins"]):
        x, y = u(lx), u(ly)
        o.append(f'<rect x="{x-5}" y="{y-5}" width="10" height="10" fill="{col}" stroke="#ddd"/>')
        o.append(f'<rect id="connector{i}pin" x="{x-2}" y="{y-2}" width="4" height="4" fill="{col}"/>')
        tx, ty, anc = (x - 9, y + 3.5, "end") if lx >= m["w"] else (x + 9, y + 3.5, "start") if lx <= 0 else (x, y + 14, "middle")
        o.append(f'<text x="{tx}" y="{ty}" font-family="Droid Sans" font-size="8" fill="#fff" text-anchor="{anc}">{m.get("short", {}).get(nm, nm).replace("-", "−")}</text>')
    o.append("</g></svg>")
    return "".join(o)
for m in MODS.values():
    CUSTOM[f"part.{m['id']}.fzp"] = fzp(m["id"], m["title"], [n for n, _, _ in m["pins"]], m["id"])
    CUSTOM[f"svg.breadboard.{m['id']}.svg"] = mod_svg(m)
    CUSTOM[f"svg.schematic.{m['id']}.svg"] = box_svg(len(m["pins"]), "schematic")
    CUSTOM[f"svg.pcb.{m['id']}.svg"] = box_svg(len(m["pins"]), "copper0")

# ------------------------------------------------------------------ .fz schrijven
MI = iter(range(100, 100000))
BB_MI, BB2_MI = next(MI), next(MI)
for p in PARTS_L: p["mi"] = next(MI)
ESP_MI, BAT_MI = next(MI), next(MI)
for M in MOTORS: M["mi"] = next(MI)
for m in MODS.values(): m["mi"] = next(MI)
CONN = {}
def link(a, ac, al, b, bc, bl):
    CONN.setdefault((a, ac), []).append((b, bc, bl)); CONN.setdefault((b, bc), []).append((a, ac, al))
def endpoint(e):
    if isinstance(e, str):
        r, c, b = hsplit(e); return (BB2_MI if b else BB_MI), f"pin{c}{r}", "breadboardbreadboard"
    if e[0] == "ESP": return ESP_MI, f"connector{e[1]-1}", "breadboard"
    if e[0] == "BAT": return BAT_MI, "connector0" if e[1] == "+" else "connector1", "breadboard"
    if e[0] == "MOT": return next(M["mi"] for M in MOTORS if M["ref"] == e[1]), "connector0" if e[2] == "1" else "connector1", "breadboard"
    if e[0] == "MOD":
        m = MODS[e[1]]; return m["mi"], f"connector{[n for n, _, _ in m['pins']].index(e[2])}", "breadboard"
for p in PARTS_L:
    for kpin, h in p["pins"].items():
        link(p["mi"], p["cmap"][kpin], "breadboard", *endpoint(h))
STEP_OF = {BB_MI: 0, BB2_MI: 0, ESP_MI: S_ESP, BAT_MI: S_PWR} | {M["mi"]: M["step"] for M in MOTORS} | {m["mi"]: m["step"] for m in MODS.values()}
TEST_MI = set()
for p in PARTS_L:
    STEP_OF[p["mi"]] = p["step"]
    if p["test"]: TEST_MI.add(p["mi"])
for wd in WIRES:
    wd["mis"] = [next(MI) for _ in wd["pts"][1:]]
    for i, mi in enumerate(wd["mis"]):
        STEP_OF[mi] = wd["step"]
        if i: link(wd["mis"][i - 1], "connector1", "breadboardWire", mi, "connector0", "breadboardWire")
    for e, mi, c in ((wd["a"], wd["mis"][0], "connector0"), (wd["b"], wd["mis"][-1], "connector1")):
        tm, tc, tl_ = endpoint(e); link(mi, c, "breadboardWire", tm, tc, tl_)
    if any(p["mi"] in TEST_MI for p in PARTS_L if False): pass
# draden die alleen de testlast bedienen
for wd in WIRES:
    if wd["step"] == S_ESP and (wd["a"] in ("I22", "I29") or wd["b"] in ("I26", "I46")): TEST_MI.update(wd["mis"])

def connects(mi, c):
    return "".join(f'<connect connectorId="{bc}" modelIndex="{b}" layer="{bl}"/>' for b, bc, bl in CONN.get((mi, c), []))
def conxml(mi, cids, layer, legs=None):
    out = []
    for c in cids:
        leg = ""
        g = '<geometry x="0" y="0"/>'
        if legs and c in legs:
            a, e = legs[c]
            g = f'<geometry x="{a[0]:.4f}" y="{a[1]:.4f}"/>'
            leg = f'<leg><point x="0" y="0"/><bezier/><point x="{e[0]:.4f}" y="{e[1]:.4f}"/><bezier/></leg>'
        out.append(f'<connector connectorId="{c}" layer="{layer}">{g}{leg}<connects>{connects(mi, c)}</connects></connector>')
    return "".join(out)
def tf(rot, w, h):
    if not rot: return ""
    m = rot_matrix(rot, w, h)
    return (f'<transform m11="{m["m11"]}" m12="{m["m12"]}" m13="0" m21="{m["m21"]}" m22="{m["m22"]}" m23="0" '
            f'm31="{m["m31"]:.4f}" m32="{m["m32"]:.4f}" m33="1"/>')

inst = []
for bmi, title, by in ((BB_MI, "Breadboard1", 0), (BB2_MI, "Breadboard2", DY2)):
    bbc = sorted({c for (m, c) in CONN if m == bmi})
    inst.append(f'<instance moduleIdRef="Breadboard-RSR03MB102-ModuleID" modelIndex="{bmi}" path=":/resources/parts/core/breadboard2.fzp">'
                f'<title>{title}</title><views><breadboardView layer="breadboardbreadboard"><geometry z="1.5" x="0" y="{by}"/>'
                f'<connectors>{conxml(bmi, bbc, "breadboardbreadboard")}</connectors></breadboardView></views></instance>')
z = 2.5
def other_views(i, z):
    sx, sy = (i % 8) * 110, (i // 8) * 110
    return (f'<schematicView layer="schematic"><geometry z="{z:.4f}" x="{sx}" y="{sy}"/></schematicView>'
            f'<pcbView layer="copper0"><geometry z="{z:.4f}" x="{sx*0.7:.1f}" y="{sy*0.7:.1f}"/></pcbView>')
for i, p in enumerate(PARTS_L):
    z += 0.01
    props = dict(p["props"])
    if p["kind"] == "res": props.setdefault("pin spacing", "400 mil")
    if p["ref"] == "C1": props["capacitance"] = "470µF"; props["voltage"] = "16V"
    pr = "".join(f'<property name="{k}" value="{v}"/>' for k, v in props.items())
    cids = sorted(p["legs"])
    inst.append(f'<instance moduleIdRef="{p["mod"]}" modelIndex="{p["mi"]}" path=":/resources/parts/core/{p["fzp"]}">{pr}'
                f'<title>{p["ref"]}</title><views><breadboardView layer="breadboard">'
                f'<geometry z="{z:.4f}" x="{p["pos"][0]:.4f}" y="{p["pos"][1]:.4f}">{tf(p["rot"], p["w"], p["h"])}</geometry>'
                f'<connectors>{conxml(p["mi"], cids, "breadboard", p["legs"])}</connectors></breadboardView>'
                f'{other_views(i, z)}</views></instance>')
mlegs = {c: (_ma[c], (0.01, 0)) for c in ("connector0", "connector1")}
for mi, mod, path, title, pos, cids, legs_ in (
        (ESP_MI, ESP_ID, f"{ESP_ID}.fzp", "ESP32", ESP_POS, [f"connector{i}" for i in range(30)], None),
        (BAT_MI, BAT_ID, f"{BAT_ID}.fzp", "Accu", BAT_POS, ["connector0", "connector1"], None),
        *[(M["mi"], CORE["motor"][0], ":/resources/parts/core/dc_motor.fzp", M["ref"], M["pos"], ["connector0", "connector1"], mlegs)
          for M in MOTORS],
        *[(m["mi"], m["id"], f"{m['id']}.fzp", m["title"], m["pos"], [f"connector{i}" for i in range(len(m["pins"]))], None)
          for m in MODS.values()]):
    z += 0.01
    cids = [c for c in cids if (mi, c) in CONN]
    inst.append(f'<instance moduleIdRef="{mod}" modelIndex="{mi}" path="{path}"><title>{title}</title><views>'
                f'<breadboardView layer="breadboard"><geometry z="{z:.4f}" x="{pos[0]:.4f}" y="{pos[1]:.4f}"/>'
                f'<connectors>{conxml(mi, cids, "breadboard", legs_)}</connectors></breadboardView>'
                f'{other_views(len(PARTS_L) + mi % 3, z)}</views></instance>')
wz = 3.5
for wd in WIRES:
    for i, (a, b) in enumerate(zip(wd["pts"], wd["pts"][1:])):
        mi = wd["mis"][i]; wz += 0.001
        inst.append(f'<instance moduleIdRef="WireModuleID" modelIndex="{mi}" path=":/resources/parts/core/wire.fzp"><title>Wire{mi}</title><views>'
                    f'<breadboardView layer="breadboardWire"><geometry z="{wz:.4f}" x="{a[0]:.4f}" y="{a[1]:.4f}" x1="0" y1="0" '
                    f'x2="{b[0]-a[0]:.4f}" y2="{b[1]-a[1]:.4f}" wireFlags="64"/>'
                    f'<wireExtras mils="22.2222" color="{wd["color"]}" opacity="1" banded="0"/>'
                    f'<connectors>{conxml(mi, ["connector0", "connector1"], "breadboardWire")}</connectors></breadboardView></views></instance>')
FZ = ('<?xml version="1.0" encoding="UTF-8"?>\n<module fritzingVersion="0.9.6">'
      '<views><view name="breadboardView" backgroundColor="#ffffff" gridSize="0.1in" showGrid="1" alignToGrid="0" viewFromBelow="0"/>'
      '<view name="schematicView" backgroundColor="#ffffff" gridSize="0.1in" showGrid="1" alignToGrid="1" viewFromBelow="0"/>'
      '<view name="pcbView" backgroundColor="#333333" gridSize="0.05in" showGrid="1" alignToGrid="1" viewFromBelow="0"/></views>'
      '<instances>' + "\n".join(inst) + '</instances></module>')
FZZ.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(FZZ, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("DIY-Auto.fz", FZ)
    for k_, v in CUSTOM.items(): zf.writestr(k_, v)
print("geschreven:", FZZ)

# ------------------------------------------------------------------ Fritzing laat de SVG exporteren
work = Path(tempfile.mkdtemp(prefix=".export_", dir=FZZ.parent))   # de Flatpak-sandbox ziet /tmp en ~/.cache niet; wordt op het einde gewist
(work / "DIY-Auto.fzz").write_bytes(FZZ.read_bytes())
subprocess.run(["flatpak", "run", "--user", f"--filesystem={work}", "--env=QT_QPA_PLATFORM=offscreen", APP, "-svg", str(work)],
               capture_output=True, timeout=180)
if not (work / "DIY-Auto_breadboard.svg").exists():
    shutil.rmtree(work)
    sys.exit(f"FOUT: Fritzing exporteerde niets. Is de Flatpak er? flatpak install --user flathub {APP}")
EXP = (work / "DIY-Auto_breadboard.svg").read_text()
tx, ty = map(float, re.search(rf"<g partID='{BB_MI*10}'><g transform='translate\(([-\d.]+),([-\d.]+)\)'", EXP).groups())
S = 1000 / 90
def E(x, y): return (x * S + tx, y * S + ty)          # scène -> exportcoördinaten
VB = [float(v) for v in re.search(r"viewBox='([^']*)'", EXP).group(1).split()]

# top-level groepen per partID
head = EXP[:EXP.find("<g partID=")]
groups, stack = {}, []
for m in re.finditer(r"<g\b[^>]*>|</g>", EXP):           # één doorloop met een stapel
    if m.group(0).endswith("/>"): continue               # <g .../> sluit zichzelf
    if m.group(0) == "</g>":
        start, pid = stack.pop()
        if pid is not None and not any(q is not None for _, q in stack):
            groups[pid] = EXP[start:m.end()]
    else:
        pm = re.match(r"<g partID='(\d+)'", m.group(0))
        stack.append((m.start(), int(pm.group(1)) // 10 if pm else None))

# ------------------------------------------------------------------ labels
LBL = []      # (mi, x, y, tekst, anchor, kleur)
def lab(mi, x, y, t, anchor="middle", color="#263238", size=62):
    LBL.append((mi, x, y, t, anchor, color, size))
for p in PARTS_L:
    x0, y0 = p["pos"]; w, h = (p["h"], p["w"]) if p["rot"] == 90 else (p["w"], p["h"])
    cx = x0 + w / 2
    if p["kind"] == "pfet":  lab(p["mi"], cx, y0 - 4, f'{p["ref"]} {p["label"]}  ·  G D S')
    elif p["kind"] == "nfet": lab(p["mi"], cx, y0 + h + 9, f'{p["ref"]} {p["label"]}  ·  S D G')
    elif p["kind"] == "npn":  lab(p["mi"], cx, y0 + h + 9, f'{p["ref"]} {p["label"]}  ·  C B E')
    elif p["kind"] in ("res", "diode"):  lab(p["mi"], cx, y0 - 1.5, f'{p["ref"]} {p["label"]}', size=50)
    elif p["kind"] in ("cap", "elco"): lab(p["mi"], cx, y0 - 3, f'{p["ref"]} {p["label"]}', size=55)
    elif p["kind"] == "ledr":
        yy = y0 + h / 2
        lab(p["mi"], x0 + w + 3, yy, p["label"], "start", "#c62828" if "rood" in p["label"] else "#2e7d32", 55)
lab(BAT_MI, BAT_POS[0] + BAT_W / 2, BAT_POS[1] - 5, "ERYNK-accu 7,4 V · rode JST-stekker", size=62)
lab(BAT_MI, BAT_POS[0] + BAT_W / 2, BAT_POS[1] + BAT_H + 9, "of: labvoeding 7,4 V, begrensd op 0,5 A", size=55)
for m in MODS.values():
    lab(m["mi"], m["pos"][0] + m["w"] / 2, m["pos"][1] + m["h"] + 9 if m["pos"][1] > 0 else m["pos"][1] - 5, m["label"], size=55)
lab(ESP_MI, ESP_POS[0] - 8, ESP_POS[1] + ESP_H / 2 - 4, "ESP32 DevKit v1", "end", size=62)
lab(ESP_MI, ESP_POS[0] - 8, ESP_POS[1] + ESP_H / 2 + 5, "5 V op VIN via D1 · USB mag erbij", "end", size=55)
for M in MOTORS: lab(M["mi"], M["pos"][0] + M["w"] + 8, M["pos"][1] + M["h"] / 2 + 2, M["label"], "start", size=62)
lab(BB_MI, X(63) + 12, ROWY["Y"] + 2, "+7,4 V", "start", "#c62828", 60)
lab(BB_MI, X(63) + 12, ROWY["Z"] + 2, "GND", "start", "#1a1a1a", 60)
lab(BB_MI, X(63) + 12, ROWY["X"] + 2, "GND", "start", "#1a1a1a", 60)
lab(BB_MI, X(63) + 12, ROWY["W"] + 5, "+5 V", "start", ORA, 60)
lab(BB2_MI, X(1) - 16, DY2 + ROWY["Y"] + 2, "+7,4 V (van bord 1)", "end", "#c62828", 60)
lab(BB2_MI, X(1) - 16, DY2 + ROWY["X"] + 2, "GND (van bord 1)", "end", "#1a1a1a", 60)
lab(BB2_MI, X(1), DY2 - 175, "BORD 2 · H-BRUG B", "start", "#37474f", 80)
for bmi, dy, pair in ((BB_MI, 0, (LB, RB)), (BB2_MI, DY2, (LB2, RB2))):
    for col, t in ((pair[0]["m"], "M+"), (pair[1]["m"], "M−")):
        lab(bmi, X(col) + 3, dy + STREET["gap"] + 2.5, t, "start", "#6d4c41", 60)

def step_svg(step, overview=False):
    out = [head]
    for pid, g in groups.items():
        st = STEP_OF.get(pid, 0)
        if pid == BB2_MI and not overview and step < S_B: continue
        test = pid in TEST_MI
        if overview:
            if test: continue
            out.append(g); continue
        if st > step or (test and step != S_ESP): continue
        if st == 0 or st == step: out.append(g)
        else: out.append(f"<g opacity='0.16'>{g}</g>")
    # transistor legs drawn by hand: the TO-220/TO-92 images only have short straight stubs, so draw each leg
    # from its root on the body to the hole it really goes into (S/E legs bent to the rail)
    for p in PARTS_L:
        if p["kind"] not in ("nfet", "pfet", "npn"): continue
        st = STEP_OF.get(p["mi"], 0)
        if p["mi"] == BB2_MI or (not overview and st > step): continue
        op = 1 if overview or st == step else 0.25
        for c, (a, e) in p["legs"].items():
            ra = rot_apply(p["rot"], p["w"], p["h"], a)
            x0, y0 = E(p["pos"][0] + ra[0], p["pos"][1] + ra[1])
            x1, y1 = E(*p["targets"][c])
            out.append(f"<g opacity='{op}'><line x1='{x0:.1f}' y1='{y0:.1f}' x2='{x1:.1f}' y2='{y1:.1f}' stroke='#555' stroke-width='26' stroke-linecap='round'/>"
                       f"<line x1='{x0:.1f}' y1='{y0:.1f}' x2='{x1:.1f}' y2='{y1:.1f}' stroke='#d9d9d9' stroke-width='14' stroke-linecap='round'/>"
                       f"<circle cx='{x1:.1f}' cy='{y1:.1f}' r='20' fill='#555'/></g>")
    for mi, x, y, t, anc, col, size in LBL:
        st = STEP_OF.get(mi, 0); test = mi in TEST_MI
        if mi == BB2_MI and not overview and step < S_B: continue
        if overview and test: continue
        if not overview and (st > step or (test and step != S_ESP)): continue
        op = 1 if overview or st in (0, step) else 0.25
        ex, ey = E(x, y)
        out.append(f"<text x='{ex:.1f}' y='{ey:.1f}' font-family='DejaVu Sans' font-size='{size}' fill='{col}' "
                   f"text-anchor='{anc}' opacity='{op}' stroke='#fff' stroke-width='14' paint-order='stroke'>{t}</text>")
    out.append("</svg>")
    return "".join(out)

TITLES = {S_PWR: ("STAP 1 — VOEDING 7,4 V", "Accu via de rode JST-stekker (of labvoeding 7,4 V, 0,5 A) op de bovenste rails. C1 en C2 over + en GND."),
          S_5V: ("STAP 2 — 5 V", "LM2596 op +7,4 V en GND. Eerst OUT op 5,0 V afstellen, dan OUT+ in de onderste rode rail. C7 over +5 V en GND."),
          S_HI: ("STAP 3 — HOGE KANT", "IRF9540N recht in J13–J15 en J37–J39, rood draadje I15 → Y16 en I39 → Y40. 2N3904 onderaan, E-poot schuin in de GND-rail. Weerstanden."),
          S_LO: ("STAP 4 — LAGE KANT", "IRLZ44N recht in A21–A23 en A45–A47, zwart draadje B21 → X19 en B45 → X43. Gateweerstanden, drains naar M+ (22) en M− (46)."),
          S_ESP: ("STAP 5 — ESP32 EN TESTLAST", "D1 van +5 V naar VIN, vijf dupontdraden naar de ESP32, 1 kΩ met een rode en een groene led tussen M+ en M−."),
          S_MOT: ("STAP 6 — MOTOR", "Testlast weg, motordraden in J22 (M+) en J46 (M−). Eerst kort en met lage PWM."),
          S_SERVO: ("STAP 7 — SERVO", "GPIO19 via R6 (1 kΩ) naar het signaal, servo op +5 V en GND van de onderste rails."),
          S_B: ("STAP 8 — H-BRUG B (BORD 2)", "Tweede bord, exact dezelfde layout als stap 3 en 4. Y61 → Y61 (+7,4 V) en X59 → X61 (GND) verbinden de rails."),
          S_BMOT: ("STAP 9 — ESP32 NAAR BRUG B + MOTOR B", "GPIO32, 33, 4 en 18 naar rij E. Eerst de testlast van stap 5 op D22 en D46, dan motor B in J22 en J46.")}
CROP1 = E(0, 395)[1] - VB[1]               # stappen 1-7: alleen bord 1 + ESP32
def compose(items, legend, out_png, width_px=2600):
    W = VB[2]; blocks = []; y = 0
    for title, sub, svg, *hh in items:
        Hc = hh[0] if hh else VB[3]
        inner = re.sub(r"^.*?<svg[^>]*>", "", svg, count=1, flags=re.S).rsplit("</svg>", 1)[0]
        blk = ""
        if title:
            blk += (f"<text x='80' y='{y+170}' font-family='DejaVu Sans' font-weight='bold' font-size='150' fill='#37474f'>{title}</text>"
                    f"<text x='80' y='{y+330}' font-family='DejaVu Sans' font-size='100' fill='#546e7a'>{sub}</text>")
            y += 400
        blk += f"<svg x='0' y='{y}' width='{W}' height='{Hc}' viewBox='{VB[0]} {VB[1]} {VB[2]} {Hc}'>{inner}</svg>"
        y += Hc + 250
        blocks.append(blk)
    if legend:
        blocks.append(f"<g transform='translate(0,{y})'>{legend}</g>"); y += 2440
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{y}' viewBox='0 0 {W} {y}'>"
           f"<rect width='{W}' height='{y}' fill='white'/>" + "".join(blocks) + "</svg>")
    tmp = work / (out_png.stem + ".svg"); tmp.write_text(svg)
    subprocess.run(["rsvg-convert", "-w", str(width_px), "-b", "white", str(tmp), "-o", str(out_png)], check=True)
    print("geschreven:", out_png)

def legend_svg():
    L = []; x0, y0 = 80, 0
    L.append(f"<rect x='40' y='0' width='{VB[2]-80}' height='2360' rx='30' fill='#f7f8f9' stroke='#b0bec5' stroke-width='6'/>")
    L.append(f"<text x='{x0+40}' y='{y0+150}' font-family='DejaVu Sans' font-weight='bold' font-size='110' fill='#37474f'>LEGENDE</text>")
    rows = [("#d32f2f", "+7,4 V van de accu"), (ORA, "+5 V van de LM2596"), ("#1a1a1a", "GND (accu −)"), ("#8c8c8c", "verbinding op het bord"), ("#6d4c41", "motordraden"),
            ("#f9a825", "GPIO25 → A_HL (hoge kant links)"), ("#1565c0", "GPIO27 → A_LL (lage kant links, PWM)"),
            ("#2e7d32", "GPIO26 → A_HR (hoge kant rechts)"), ("#8e24aa", "GPIO13 → A_LR (lage kant rechts, PWM)"), (TEAL, "GPIO19 → servosignaal (via R6)"),
            (B_COL["GPIO32"], "GPIO32 → B_HL (bord 2, hoge kant links)"), (B_COL["GPIO4"], "GPIO4 → B_LL (bord 2, lage kant links, PWM)"),
            (B_COL["GPIO33"], "GPIO33 → B_HR (bord 2, hoge kant rechts)"), (B_COL["GPIO18"], "GPIO18 → B_LR (bord 2, lage kant rechts, PWM)")]
    for i, (c, t) in enumerate(rows):
        yy = y0 + 300 + i * 140
        L.append(f"<line x1='{x0+40}' y1='{yy}' x2='{x0+300}' y2='{yy}' stroke='{c}' stroke-width='40' stroke-linecap='round'/>")
        L.append(f"<text x='{x0+360}' y='{yy+35}' font-family='DejaVu Sans' font-size='90' fill='#263238'>{t}</text>")
    txt = ["Rails: bovenaan rood = +7,4 V, blauw = GND. Onderaan blauw = GND, rood = +5 V.",
           "Rijen J–F en E–A: elke kolom van 5 gaten is onderling verbonden. De gleuf in het midden scheidt ze.",
           "IRF9540N bovenaan: tekstkant naar jou, pootjes G D S recht in rij J. Een rood draadje brengt S naar de +rail.",
           "IRLZ44N onderaan: metalen tab NAAR JOU, pootjes S D G recht in rij A. Een zwart draadje brengt S naar de GND-rail.",
           "2N3904 onderaan: platte kant VAN JE WEG (naar de gleuf), C B E. Alleen de E-poot buig je schuin naar de GND-rail.",
           "Het lijf van elke transistor ligt in de tekening over de rails. Echt staat hij rechtop in rij J of A.",
           "Grijs weggevaagd = werk uit een vorige stap. Het bord is op ware grootte getekend (1 gat = 2,54 mm)."]
    for i, t in enumerate(txt):
        L.append(f"<text x='{VB[2]/2-200}' y='{y0+330+i*140}' font-family='DejaVu Sans' font-size='82' fill='#37474f'>{t}</text>")
    return "".join(L)

ASSETS.mkdir(exist_ok=True)
compose([(TITLES[s_][0], TITLES[s_][1], step_svg(s_), *([CROP1] if s_ < S_B else [])) for s_ in range(1, S_BMOT + 1)],
        legend_svg(), ASSETS / "DIY-Auto_breadboard_v3g.png")
compose([("", "", step_svg(S_BMOT, overview=True))], legend_svg(), ASSETS / "DIY-Auto_breadboard-overzicht_v3g.png")

# ------------------------------------------------------------------ meetpunten (brug A, met test_hbridge.ino)
# (nr, gat in de tekening, wat, altijd, VOORUIT (rode led), ACHTERUIT (groene led))
TP = [(1, "Y3", "+7,4 V-rail", "7,4 V", "7,4 V", "7,4 V"),
      (2, "X5", "GND onderste rail ↔ Z3 en GND van de ESP32", "0 V, piept", "", ""),
      (3, "E18", "GPIO25 (HL)", "", "3,3 V", "0 V"),
      (4, "J13", "gate IRF9540N links", "7,4 V = uit", "± 0 V = aan", "7,4 V"),
      (5, "A22", "M+ (drain links)", "", "± 7 V", "± 0 V"),
      (6, "E51", "GPIO13 (LR, PWM)", "", "± 2,3 V*", "0 V"),
      (7, "A47", "gate IRLZ44N rechts", "", "± 2,3 V*", "0 V"),
      (8, "A46", "M− (drain rechts)", "", "± 0 V", "± 7 V"),
      (9, "E42", "GPIO26 (HR)", "", "0 V", "3,3 V"),
      (10, "J37", "gate IRF9540N rechts", "7,4 V = uit", "7,4 V", "± 0 V = aan"),
      (11, "E27", "GPIO27 (LL, PWM)", "", "0 V", "± 2,3 V*"),
      (12, "A23", "gate IRLZ44N links", "", "0 V", "± 2,3 V*")]
def tp_svg(TP=TP, below={7, 12}):
    svg = step_svg(S_ESP).rsplit("</svg>", 1)[0]                                   # neighbours of 8 and 5: badge under the hole
    for n, h, *_ in TP:
        x, y = E(*HOLES[h])
        bx, by = (x + 95, y + 115) if n in below else (x + 95, y - 95)
        svg += (f"<circle cx='{x:.1f}' cy='{y:.1f}' r='55' fill='none' stroke='#d81b60' stroke-width='16'/>"
                f"<circle cx='{bx:.1f}' cy='{by:.1f}' r='62' fill='#d81b60'/>"
                f"<text x='{bx:.1f}' y='{by+23:.1f}' font-family='DejaVu Sans' font-weight='bold' font-size='70' fill='white' text-anchor='middle'>{n}</text>")
    return svg + "</svg>"
def tp_table(TP=TP, hdr=None):
    L, y0 = [], 0
    xs = [int(VB[2] * f) for f in (0.015, 0.05, 0.11, 0.45, 0.61, 0.78)]
    hdr = hdr or ("#", "gat", "meetpunt (zwarte probe op GND)", "altijd", "VOORUIT (rood)", "ACHTERUIT (groen)")
    for i, t in enumerate(hdr):
        L.append(f"<text x='{xs[i]}' y='{y0+120}' font-family='DejaVu Sans' font-weight='bold' font-size='120' fill='#37474f'>{t}</text>")
    for r, row in enumerate(TP):
        yy = y0 + 300 + r * 175
        if r % 2 == 0: L.append(f"<rect x='40' y='{yy-125}' width='{VB[2]-80}' height='175' fill='#f3f5f7'/>")
        for i, t in enumerate(row):
            col = "#d81b60" if i == 0 else "#263238"
            L.append(f"<text x='{xs[i]}' y='{yy}' font-family='DejaVu Sans' font-size='112' fill='{col}'{' font-weight=\'bold\'' if i == 0 else ''}>{t}</text>")
    yy = y0 + 300 + len(TP) * 175 + 80
    L.append(f"<text x='80' y='{yy}' font-family='DejaVu Sans' font-size='100' fill='#546e7a'>* PWM 70 %: een gewone multimeter toont het gemiddelde, ± 0,7 × 3,3 V. "
             f"Klopt een waarde niet, dan zit de fout tussen dat punt en het vorige.</text>")
    return "".join(L), yy + 150
tab, tab_h = tp_table()
W_ = VB[2]
inner = re.sub(r"^.*?<svg[^>]*>", "", tp_svg(), count=1, flags=re.S).rsplit("</svg>", 1)[0]
Y0 = 420
full = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{W_}' height='{Y0 + CROP1 + 200 + tab_h}' viewBox='0 0 {W_} {Y0 + CROP1 + 200 + tab_h}'>"
        f"<rect width='100%' height='100%' fill='white'/>"
        f"<text x='80' y='170' font-family='DejaVu Sans' font-weight='bold' font-size='150' fill='#37474f'>MEETPUNTEN — H-BRUG A</text>"
        f"<text x='80' y='330' font-family='DejaVu Sans' font-size='100' fill='#546e7a'>test_hbridge.ino draait: 2 s vooruit (rood), 1 s uit, 2 s achteruit (groen). Zwarte probe op GND (Z- of X-rail).</text>"
        f"<svg x='0' y='{Y0}' width='{W_}' height='{CROP1}' viewBox='{VB[0]} {VB[1]} {VB[2]} {CROP1}'>{inner}</svg>"
        f"<g transform='translate(0,{Y0 + CROP1 + 200})'>{tab}</g></svg>")
tmp = work / "meetpunten.svg"; tmp.write_text(full)
subprocess.run(["rsvg-convert", "-w", "2600", "-b", "white", str(tmp), "-o", str(ASSETS / "DIY-Auto_meetpunten_v1.png")], check=True)
print("geschreven:", ASSETS / "DIY-Auto_meetpunten_v1.png")

# ------------------------------------------------------------------ pad M+ -> testlast -> M− (brug vast op vooruit, debug_hold.ino)
TP2 = [(1, "J14", "drain IRF9540N links (middelste poot)", "± 7 V", "", ""),
       (2, "G14", "grijs draadje: begin (kolom van die drain)", "± 7 V", "", ""),
       (3, "G22", "grijs draadje: eind (kolom M+)", "± 7 V", "", ""),
       (4, "F22", "draadje bovenste ↔ onderste helft, boven", "± 7 V", "", ""),
       (5, "E22", "zelfde draadje, onder", "± 7 V", "", ""),
       (6, "A22", "drain IRLZ44N links (middelste poot)", "± 7 V", "", ""),
       (7, "I22", "testlast: grijs draadje begin", "± 7 V", "", ""),
       (8, "I26", "testlast: grijs draadje eind", "± 7 V", "", ""),
       (9, "H26", "1 kΩ, eerste poot", "± 7 V", "", ""),
       (10, "H30", "1 kΩ, tweede poot = lange poot rode led", "± 2 V", "", ""),
       (11, "J29", "korte poot rode led", "± 0 V", "", ""),
       (12, "I46", "grijs draadje eind = M−", "± 0 V", "", "")]
hdr2 = ("#", "gat", "meetpunt (zwarte probe op GND)", "VOORUIT", "", "")
tab2, tab2_h = tp_table(TP2, hdr2)
inner2 = re.sub(r"^.*?<svg[^>]*>", "", tp_svg(TP2, below={3, 5, 8, 12}), count=1, flags=re.S).rsplit("</svg>", 1)[0]
full2 = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{W_}' height='{Y0 + CROP1 + 200 + tab2_h}' viewBox='0 0 {W_} {Y0 + CROP1 + 200 + tab2_h}'>"
         f"<rect width='100%' height='100%' fill='white'/>"
         f"<text x='80' y='170' font-family='DejaVu Sans' font-weight='bold' font-size='150' fill='#37474f'>MEETPUNTEN — PAD M+ → RODE LED → M−</text>"
         f"<text x='80' y='330' font-family='DejaVu Sans' font-size='100' fill='#546e7a'>Brug vast op vooruit (debug_hold.ino). Volg de punten: de eerste ± 0 V na een ± 7 V is de onderbreking.</text>"
         f"<svg x='0' y='{Y0}' width='{W_}' height='{CROP1}' viewBox='{VB[0]} {VB[1]} {VB[2]} {CROP1}'>{inner2}</svg>"
         f"<g transform='translate(0,{Y0 + CROP1 + 200})'>{tab2}</g></svg>")
tmp = work / "pad.svg"; tmp.write_text(full2)
subprocess.run(["rsvg-convert", "-w", "2600", "-b", "white", str(tmp), "-o", str(ASSETS / "DIY-Auto_meetpunten_pad_v1.png")], check=True)
print("geschreven:", ASSETS / "DIY-Auto_meetpunten_pad_v1.png")

# ------------------------------------------------------------------ fixes na de foto van 2026-09-30 (GND ESP ↔ bord = −0,5 V: geen gemeenschappelijke massa)
def fix_svg():
    svg = step_svg(S_ESP).rsplit("</svg>", 1)[0]
    M = "#d81b60"
    def ring(h, r=70): x, y = E(*HOLES[h]); return f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='none' stroke='{M}' stroke-width='18'/>"
    def tag(x, y, n, t, anchor="start"):
        return (f"<circle cx='{x:.1f}' cy='{y:.1f}' r='75' fill='{M}'/><text x='{x:.1f}' y='{y+27:.1f}' font-family='DejaVu Sans' font-weight='bold' "
                f"font-size='80' fill='white' text-anchor='middle'>{n}</text>"
                f"<text x='{x + (110 if anchor == 'start' else -110):.1f}' y='{y+25:.1f}' font-family='DejaVu Sans' font-weight='bold' font-size='72' "
                f"fill='{M}' text-anchor='{anchor}' stroke='#fff' stroke-width='14' paint-order='stroke'>{t}</text>")
    # 1: GND bridge top rail (Z61) -> bottom rail (X61)
    pts = [E(*HOLES["Z61"]), E(*G(65, "Z")), E(*G(65, "X")), E(*HOLES["X61"])]
    svg += f"<polyline points='{' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)}' fill='none' stroke='{M}' stroke-width='30' stroke-dasharray='60,30' opacity='0.85'/>"
    svg += ring("Z61") + ring("X61")
    x, y = E(*G(65, "gap")); svg += tag(x - 140, y, 1, "draad Z61 → X61: GND boven ↔ GND onder", "end")
    # 2: ESP32 GND on the blue (GND) row of the bottom rail
    svg += ring("X5", 80)
    x, y = E(*HOLES["X5"]); svg += tag(x - 160, y + 330, 2, "GND van de ESP32 hier: rij met de BLAUWE lijn", "start")
    # 3: VIN stays free
    return svg + "</svg>"
inner = re.sub(r"^.*?<svg[^>]*>", "", fix_svg(), count=1, flags=re.S).rsplit("</svg>", 1)[0]
lines = ["Gemeten: GND van de ESP32 ↔ GND van het bord = −0,5 V. Dat moet 0 V zijn en piepen: de massa's zijn niet verbonden.",
         "1  Draad van de bovenste GND-rail (Z, blauwe lijn) naar de onderste GND-rail (X, blauwe lijn). In de tekening rechts: Z61 → X61.",
         "    Zonder die draad krijgen de sources van de IRLZ44N en de emitters van de 2N3904 geen massa van de labvoeding.",
         "2  De GND-draad van de ESP32 in de onderste rail op de rij met de BLAUWE lijn (X), niet op de rij met de rode lijn (W = +5 V).",
         "3  VIN blijft los zolang de ESP32 op USB hangt. De labvoeding: rood → Y (rode lijn boven), zwart → Z (blauwe lijn boven).",
         "Controle: doorgangsstand tussen GND van de ESP32, X-rail en Z-rail: alle drie piepen. Daarna de meetpunten 1–12."]
H2 = 420 + CROP1 + 200 + len(lines) * 150 + 100
full = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{W_}' height='{H2}' viewBox='0 0 {W_} {H2}'><rect width='100%' height='100%' fill='white'/>"
        f"<text x='80' y='170' font-family='DejaVu Sans' font-weight='bold' font-size='150' fill='#37474f'>AAN TE PASSEN — MASSA VERBINDEN</text>"
        f"<text x='80' y='330' font-family='DejaVu Sans' font-size='100' fill='#546e7a'>Twee draadjes, daarna de test opnieuw.</text>"
        f"<svg x='0' y='420' width='{W_}' height='{CROP1}' viewBox='{VB[0]} {VB[1]} {VB[2]} {CROP1}'>{inner}</svg>"
        + "".join(f"<text x='80' y='{420 + CROP1 + 250 + i*150}' font-family='DejaVu Sans' font-size='105' fill='{'#d81b60' if i == 0 else '#263238'}'"
                  f"{' font-weight=\'bold\'' if i in (0, 5) else ''}>{t}</text>" for i, t in enumerate(lines)) + "</svg>")
tmp = work / "fixes.svg"; tmp.write_text(full)
subprocess.run(["rsvg-convert", "-w", "2600", "-b", "white", str(tmp), "-o", str(ASSETS / "DIY-Auto_fixes_massa_v1.png")], check=True)
print("geschreven:", ASSETS / "DIY-Auto_fixes_massa_v1.png")
shutil.rmtree(work)
