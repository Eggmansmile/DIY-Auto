"""Fritzing-sketch rev 4 (voeding 2S 7,4 V + 5 V, TB6612FNG-motordrivermodule, ESP32, servo, 2 motoren) en breadboardtekeningen,
gecontroleerd tegen de KiCad-netlist. De leerversie met de eigen H-bruggen: gen_fritzing_hbrug.py.

Draaien:  python3 Scripts/gen_fritzing.py KiCad/DIY-Auto.net      (alleen standaardbibliotheek; Fritzing-Flatpak nodig)
Schrijft: Fritzing/DIY-Auto.fzz, ../../Assets/DIY-Auto_breadboard_v4.png (bouwstappen), ../../Assets/DIY-Auto_breadboard-overzicht_v4.png

Fritzing (Flatpak) exporteert zelf de SVG; dit script voegt daarna labels toe en vaagt per bouwstap weg wat al op het bord stond.
"""
import math, os, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
NETLIST = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "KiCad/DIY-Auto.net"
FZZ = HERE / "Fritzing/DIY-Auto.fzz"
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
DY2 = 0                                                       # rev 4: één bord (de hulpfuncties houden het b-achtervoegsel)
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
S_PWR, S_5V, S_TB, S_ESP, S_MOT, S_SERVO, S_BMOT = 1, 2, 3, 4, 5, 6, 7   # bouwstappen

# --- stap 1: voeding 7,4 V.  Accu 2S (JST BEC) -> Y3 (+) en Z3 (GND); geen zekering (ook niet op de print sinds rev 5).  Z en X rechts verbonden.
part("C2", "cap", {"1": "Y43", "2": "Z43"}, S_PWR, "100nF", rot=90)
part("C1", "elco", {"1": "Y47", "2": "Z47"}, S_PWR, "470µF 16V", rot=90)
wire(["Z61", G(65, "Z"), G(65, "X"), "X61"], BLK, S_PWR)
# --- stap 2: 5 V.  De onderste rode rail (W) wordt +5 V van de LM2596.
part("C7", "cap", {"1": "W52", "2": "X52"}, S_5V, "100nF", rot=90)

# --- stap 3: TB6612FNG-module over de gleuf, 90° gedraaid: VM-rij in H20–H27, logicarij in D20–D27.
# Het lijf bedekt rij I tot C, dus draden alleen in rij J (boven) en A/B (onder).
TBC = 20                                                     # eerste kolom
TB_TOP = ["GND", "B01", "B02", "A02", "A01", "GND", "VCC", "VM"]          # H20 .. H27
TB_BOT = ["GND", "PWMB", "BIN2", "BIN1", "STBY", "AIN1", "AIN2", "PWMA"]  # D20 .. D27
TB_CON = {"VM": 13, "VCC": 12, "GND1": 11, "A01": 10, "A02": 9, "B02": 8, "B01": 7, "GND0": 6,
          "PWMA": 14, "AIN2": 15, "AIN1": 16, "STBY": 17, "BIN1": 18, "BIN2": 19, "PWMB": 20, "GND2": 21}   # SparkFun-svg
TB_KICAD = {13: "J8.1", 12: "J8.2", 11: "J8.3", 10: "J8.4", 9: "J8.5", 8: "J8.6", 7: "J8.7", 6: "J8.8",
            14: "J9.1", 15: "J9.2", 16: "J9.3", 17: "J9.4", 18: "J9.5", 19: "J9.6", 20: "J9.7", 21: "J9.8"}
TB_PINS = {}                                                 # svg-connector -> gat
for i, nm in enumerate(TB_TOP):
    TB_PINS[{"GND": 6 if i == 0 else 11}.get(nm, TB_CON.get(nm))] = f"H{TBC + i}"
for i, nm in enumerate(TB_BOT):
    TB_PINS[21 if nm == "GND" else TB_CON[nm]] = f"D{TBC + i}"
TBCOL = {nm: TBC + i for i, nm in enumerate(TB_TOP)} | {nm: TBC + i for i, nm in enumerate(TB_BOT) if nm != "GND"}
wire([f"J{TBC+7}", f"Y{TBC+7}"], RED, S_TB)                                                     # VM -> +7,4 V
wire([f"J{TBC}", G(TBC - 0.5, "YJ"), G(TBC - 0.5, "Z"), f"Z{TBC-1}"], BLK, S_TB)                # GND boven -> Z
wire([f"J{TBC+5}", G(TBC + 4.5, "YJ"), G(TBC + 4.5, "Z"), f"Z{TBC+4}"], BLK, S_TB)             # GND boven -> Z
wire([f"A{TBC}", G(TBC - 0.5, "AX"), G(TBC - 0.5, "X"), f"X{TBC-1}"], BLK, S_TB)   # GND onder -> X
part("R7", "res", {"1": f"B{TBC+4}", "2": f"B{TBC}"}, S_TB, "20k", props={"resistance": "20000"})  # STBY-pull-down

# ------------------------------------------------------------------ ESP32 (eigen onderdeel onder het bord)
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
ESP_KICAD = {"GPIO25": 8, "GPIO26": 9, "GPIO27": 10, "GPIO32": 6, "GPIO33": 7, "GND": 14, "VIN": 15,
             "GPIO19": 21, "GPIO18": 22, "GPIO4": 26, "3V3": 30}   # 16..30 = J3.1..15
def esp_ref(i): return f"J2.{i}" if i <= 15 else f"J3.{i - 15}"
def esp_xy(i): return esp_pin_xy(0, i) if i <= 15 else esp_pin_xy(1, i - 15)

# --- stap 4: ESP32 naar de logicarij (van onderen in rij A)
GP = {"GPIO25": ("AIN1", "#f9a825"), "GPIO26": ("AIN2", "#2e7d32"), "GPIO27": ("PWMA", BLU),
      "GPIO32": ("BIN1", "#c0ca33"), "GPIO33": ("BIN2", "#ec407a"), "GPIO4": ("PWMB", "#00acc1"), "GPIO18": ("STBY", "#8e24aa")}
def esp_sig(gpio, lane):
    i = ESP_KICAD[gpio]; p = esp_xy(i); nm, col = GP[gpio]; c = TBCOL[nm]
    wire([p, (p[0], lane), (X(c - 0.5), lane), G(c - 0.5, "AX"), G(c, "AX"), f"A{c}"], col, S_ESP, a=("ESP", i), b=f"A{c}")
for gpio, lane in (("GPIO27", 238), ("GPIO26", 230), ("GPIO25", 222), ("GPIO33", 208), ("GPIO32", 202)):
    esp_sig(gpio, lane)
for gpio, lane in (("GPIO4", 372), ("GPIO18", 379)):        # onderste rij: onder de DevKit door, links omhoog
    esp_sig(gpio, lane)
# 3V3 -> VCC (J26): onder de DevKit naar rechts, rechts langs het bord omhoog, bovenaan terug
p3 = esp_xy(30)
wire([p3, (p3[0], 386), (X(67.5), 386), (X(67.5), STREET["top"]), G(TBC + 6.5, "top"), G(TBC + 6.5, "YJ"),
      G(TBC + 6, "YJ"), f"J{TBC+6}"], "#ff7043", S_ESP, a=("ESP", 30), b=f"J{TBC+6}")
pg = esp_pin_xy(0, 14)
wire([pg, (pg[0], 244), (X(5.5), 244), (X(5.5), ROWY["X"]), HOLES["X5"]], BLK, S_ESP, a=("ESP", 14), b="X5")
# VIN: +5 V-rail -> D1 (anode kolom 8, kathode kolom 4) -> VIN
part("D1", "diode", {"1": "C4", "2": "C8"}, S_ESP, "1N5819")
wire(["A8", (X(8), ROWY["W"]), "W9"], ORA, S_ESP)
pv = esp_pin_xy(0, 15)
wire([pv, (pv[0], 251), (X(4.5), 251), (X(4.5), STREET["AX"]), G(4, "AX"), "A4"], ORA, S_ESP, a=("ESP", 15), b="A4")

# --- stap 5 en 7: motoren boven het bord, draden van bovenaf in rij J
_ma, _mw, _mh = svg_legs((BBSVG / CORE["motor"][2]).read_text(errors="ignore"))
MOTORS = [dict(ref="M1", step=S_MOT, label="MOTOR A (links)", pos=(X(30), -150), cols=(TBCOL["A01"], TBCOL["A02"])),
          dict(ref="M2", step=S_BMOT, label="MOTOR B (rechts)", pos=(X(2), -150), cols=(TBCOL["B01"], TBCOL["B02"]))]
for M in MOTORS:
    M.update(b="", att=_ma, w=_mw, h=_mh)
    for k, (k_, cn, c) in enumerate((("1", "connector0", M["cols"][0]), ("2", "connector1", M["cols"][1]))):
        m = (M["pos"][0] + _ma[cn][0], M["pos"][1] + _ma[cn][1])
        if X(c) > M["pos"][0] + _mw:                         # kolommen rechts van de motor: over de motor heen, niet over het lijf
            yo = M["pos"][1] - 14 - 7 * k
            pts = [m, (m[0] - 10 - 7 * k, m[1]), (m[0] - 10 - 7 * k, yo), (X(c - 0.5), yo)]
        else:
            pts = [m, (X(c - 0.5), m[1])]
        wire(pts + [G(c - 0.5, "YJ"), G(c, "YJ"), f"J{c}"], "#6d4c41", M["step"], a=("MOT", M["ref"], k_))

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

# accu rechtstreeks op de bovenste rails (JST BEC), net als op de print (geen F1 sinds rev 5)
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
for c, h in TB_PINS.items():
    nets.setdefault(f(strip(h)), set()).add(TB_KICAD[c])
nets.setdefault(f("BAT.+"), set()).add("+BATT")            # accu + = +BATT (geen zekering)
nets.setdefault(f("BAT.-"), set()).add("J1.2")
for M in MOTORS:
    for k_ in ("1", "2"): nets.setdefault(f(f"MOT.{M['ref']}.{k_}"), set()).add(f"{M['ref']}.{k_}")

s = NETLIST.read_text(); body = s[s.find("(nets"):]
keep = {p["ref"] for p in PARTS_L if not p["test"]} | {M["ref"] for M in MOTORS} | {"J8", "J9"} | {r.split(".")[0] for r in MODNET.values() if r[0] == "J" and r[:2] != "J1"}
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


# ------------------------------------------------------------------ controle 2: geen gat dubbel, geen draad over een gat
used = {}
for p in PARTS_L:
    for h in p["pins"].values(): used.setdefault(h, []).append(p["ref"])
for c, h in TB_PINS.items(): used.setdefault(h, []).append(f"TB6612.{c}")
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
# TB6612-module: zijn printje ligt van rij I tot rij C over kolom TBC-0,5 .. TBC+7,5
for hn in used:
    r_, c_, _ = hsplit(hn)
    if TBC - 0.5 < c_ < TBC + 7.5 and r_ in "IHGFEDC" and hn not in TB_PINS.values(): cover.append(("TB6612", hn))
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

# TB6612FNG: SparkFun-beeld uit de Fritzing-kern, maar met mannelijke pinnen zodat hij in het bord steekt
TB_ID = "DIYAuto_TB6612FNG_Breakout"
_tbsvg = (BBSVG / "TB6612FNG Breakout v11.svg").read_text(errors="ignore")
_tbsvg = re.sub(r'id="connector(\d+)pin"', lambda m: f'id="connector{int(m.group(1)) - 6}pin"', _tbsvg)
_tbsvg = re.sub(r"(<svg[^>]*>)", r'\1<g id="breadboard">', _tbsvg, count=1).replace("</svg>", "</g></svg>")
TB_K, TB_W, TB_H = svg_info(_tbsvg)
TB_NAMES = ["GND", "B01", "B02", "A02", "A01", "GND", "VCC", "VM", "PWMA", "AIN2", "AIN1", "STBY", "BIN1", "BIN2", "PWMB", "GND"]
TB_LOCAL = {}                                                # svg-connector (6..21) -> lokaal punt in de scène
for m in re.finditer(r'<circle id="connector(\d+)pin"[^>]*cx="([\d.]+)" cy="([\d.]+)"', _tbsvg):
    TB_LOCAL[int(m.group(1)) + 6] = (float(m.group(2)) * TB_K, float(m.group(3)) * TB_K)
TB_ROT = 90
_v = rot_apply(TB_ROT, TB_W, TB_H, TB_LOCAL[13])            # VM-pin op H{TBC+7}
TB_POS = (HOLES[TB_PINS[13]][0] - _v[0], HOLES[TB_PINS[13]][1] - _v[1])
for c, h in TB_PINS.items():                                 # controle: alle 16 pinnen vallen in hun gat
    q = rot_apply(TB_ROT, TB_W, TB_H, TB_LOCAL[c])
    assert math.dist((TB_POS[0] + q[0], TB_POS[1] + q[1]), HOLES[h]) < 0.5, f"TB6612-pin {c} mist gat {h}"
CUSTOM[f"part.{TB_ID}.fzp"] = fzp(TB_ID, "TB6612FNG-module", TB_NAMES, TB_ID)
CUSTOM[f"svg.breadboard.{TB_ID}.svg"] = _tbsvg
CUSTOM[f"svg.schematic.{TB_ID}.svg"] = box_svg(16, "schematic")
CUSTOM[f"svg.pcb.{TB_ID}.svg"] = box_svg(16, "copper0")

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
BB_MI, TB_MI = next(MI), next(MI)
BB2_MI = -1                                                  # geen tweede bord
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
for c, h in TB_PINS.items():
    link(TB_MI, f"connector{c - 6}", "breadboard", *endpoint(h))
STEP_OF = {BB_MI: 0, TB_MI: S_TB, ESP_MI: S_ESP, BAT_MI: S_PWR} | {M["mi"]: M["step"] for M in MOTORS} | {m["mi"]: m["step"] for m in MODS.values()}
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
# draden die alleen de testlast bedienen

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
for bmi, title, by in ((BB_MI, "Breadboard1", 0),):
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
        (TB_MI, TB_ID, f"{TB_ID}.fzp", "TB6612FNG", TB_POS, [f"connector{i}" for i in range(16)], None),
        *[(M["mi"], CORE["motor"][0], ":/resources/parts/core/dc_motor.fzp", M["ref"], M["pos"], ["connector0", "connector1"], mlegs)
          for M in MOTORS],
        *[(m["mi"], m["id"], f"{m['id']}.fzp", m["title"], m["pos"], [f"connector{i}" for i in range(len(m["pins"]))], None)
          for m in MODS.values()]):
    z += 0.01
    cids = [c for c in cids if (mi, c) in CONN]
    trf = tf(TB_ROT, TB_W, TB_H) if mi == TB_MI else ""
    inst.append(f'<instance moduleIdRef="{mod}" modelIndex="{mi}" path="{path}"><title>{title}</title><views>'
                f'<breadboardView layer="breadboard"><geometry z="{z:.4f}" x="{pos[0]:.4f}" y="{pos[1]:.4f}">{trf}</geometry>'
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
for M in MOTORS: lab(M["mi"], M["pos"][0] + M["w"] / 2, M["pos"][1] + M["h"] + 9, M["label"], size=62)
lab(BB_MI, X(63) + 12, ROWY["Y"] + 2, "+7,4 V", "start", "#c62828", 60)
lab(BB_MI, X(63) + 12, ROWY["Z"] + 2, "GND", "start", "#1a1a1a", 60)
lab(BB_MI, X(63) + 12, ROWY["X"] + 2, "GND", "start", "#1a1a1a", 60)
lab(BB_MI, X(63) + 12, ROWY["W"] + 5, "+5 V", "start", ORA, 60)
lab(TB_MI, X(TBC + 8) + 4, ROWY["H"] + 2, "VM-kant: motoren en voeding", "start", "#37474f", 50)
lab(TB_MI, X(TBC + 8) + 4, ROWY["D"] + 2, "logicakant: naar de ESP32", "start", "#37474f", 50)
lab(TB_MI, X(TBC - 1) - 4, STREET["gap"] + 2, "TB6612FNG", "end", "#b71c1c", 62)

def step_svg(step, overview=False):
    out = [head]
    for pid, g in groups.items():
        st = STEP_OF.get(pid, 0)
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
        if overview and test: continue
        if not overview and (st > step or (test and step != S_ESP)): continue
        op = 1 if overview or st in (0, step) else 0.25
        ex, ey = E(x, y)
        out.append(f"<text x='{ex:.1f}' y='{ey:.1f}' font-family='DejaVu Sans' font-size='{size}' fill='{col}' "
                   f"text-anchor='{anc}' opacity='{op}' stroke='#fff' stroke-width='14' paint-order='stroke'>{t}</text>")
    out.append("</svg>")
    return "".join(out)

TITLES = {S_PWR: ("STAP 1 — VOEDING 7,4 V", "Accu via de rode JST-stekker (of labvoeding 7,4 V, 0,5 A) op de bovenste rails. C1 en C2 over + en GND. Draad Z61 → X61 (GND boven ↔ onder)."),
          S_5V: ("STAP 2 — 5 V", "LM2596 op +7,4 V en GND. Eerst OUT op 5,0 V afstellen, dan OUT+ in de onderste rode rail. C7 over +5 V en GND."),
          S_TB: ("STAP 3 — TB6612FNG-MODULE", f"Module over de gleuf: VM-rij in H{TBC}–H{TBC+7} (VM rechts), logicarij in D{TBC}–D{TBC+7}. VM → +7,4 V, drie keer GND, R7 20k van STBY naar GND."),
          S_ESP: ("STAP 4 — ESP32", f"Zeven signaaldraden in rij A, 3V3 naar VCC (J{TBC+6}), GND naar de X-rail, D1 van +5 V naar VIN."),
          S_MOT: ("STAP 5 — MOTOR A", f"Motordraden in J{TBCOL['A01']} (A01) en J{TBCOL['A02']} (A02). Eerst kort en met lage PWM (test_tb6612)."),
          S_SERVO: ("STAP 6 — SERVO", "GPIO19 via R6 (1 kΩ) naar het signaal, servo op +5 V en GND van de onderste rails."),
          S_BMOT: ("STAP 7 — MOTOR B", f"Motordraden in J{TBCOL['B01']} (B01) en J{TBCOL['B02']} (B02). Draait hij verkeerd om: MOTOR_B_INVERT in test_drive.")}
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
    rows = [("#d32f2f", "+7,4 V van de accu"), (ORA, "+5 V van de LM2596"), ("#ff7043", "3V3 van de ESP32 → VCC"), ("#1a1a1a", "GND (accu −)"),
            ("#6d4c41", "motordraden")] + [(col, f"{g} → {nm}") for g, (nm, col) in GP.items()] + [(TEAL, "GPIO19 → servosignaal (via R6)")]
    for i, (c, t) in enumerate(rows):
        yy = y0 + 300 + i * 140
        L.append(f"<line x1='{x0+40}' y1='{yy}' x2='{x0+300}' y2='{yy}' stroke='{c}' stroke-width='40' stroke-linecap='round'/>")
        L.append(f"<text x='{x0+360}' y='{yy+35}' font-family='DejaVu Sans' font-size='90' fill='#263238'>{t}</text>")
    txt = ["Rails: bovenaan rood = +7,4 V, blauw = GND. Onderaan blauw = GND, rood = +5 V.",
           "Rijen J–F en E–A: elke kolom van 5 gaten is onderling verbonden. De gleuf in het midden scheidt ze.",
           "TB6612-module: pinrijen 15,24 mm uit elkaar, over de gleuf. VM-rij boven (rij H), logicarij onder (rij D).",
           "Het printje bedekt rij I tot C: draden alleen in rij J (boven) en A/B (onder).",
           "Controleer de opdruk van JOUW module: staat VM boven rechts en PWMA onder rechts, dan klopt het.",
           "Remmen = IN1 en IN2 hoog. Kortsluiting via de code kan niet: de chip regelt de dode tijd.",
           "Grijs weggevaagd = werk uit een vorige stap. Het bord is op ware grootte getekend (1 gat = 2,54 mm)."]
    for i, t in enumerate(txt):
        L.append(f"<text x='{VB[2]/2-200}' y='{y0+330+i*140}' font-family='DejaVu Sans' font-size='82' fill='#37474f'>{t}</text>")
    return "".join(L)

ASSETS.mkdir(exist_ok=True)
CROP1 = E(0, 420)[1] - VB[1]
compose([(TITLES[s_][0], TITLES[s_][1], step_svg(s_), CROP1) for s_ in range(1, S_BMOT + 1)],
        legend_svg(), ASSETS / "DIY-Auto_breadboard_v4.png")
compose([("", "", step_svg(S_BMOT, overview=True), CROP1)], legend_svg(), ASSETS / "DIY-Auto_breadboard-overzicht_v4.png")
shutil.rmtree(work)
