"""Genereert KiCad/DIY-Auto.kicad_sch — accu, ESP32 DevKit-headers, TB6612FNG-motordrivermodule (rev 4).

Draaien (vanuit de projectmap):
    KICAD_SYMBOL_DIR=/usr/share/kicad/symbols ~/.local/bin/uv run -p 3.12 --with kicad-sch-api python Scripts/gen_schematic.py
Controleren:
    kicad-cli sch erc KiCad/DIY-Auto.kicad_sch
"""
import math, re
from pathlib import Path
import kicad_sch_api as ksa

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "KiCad" / "DIY-Auto.kicad_sch"
G = 2.54

FP = {
    "TO220": "Package_TO_SOT_THT:TO-220-3_Vertical",
    "TO92": "Package_TO_SOT_THT:TO-92_Inline",
    "R": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "C": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "CP": "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
    "DO41": "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
    "TERM2": "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal",
    "HDR15": "Connector_PinSocket_2.54mm:PinSocket_1x15_P2.54mm_Vertical",
    "HDR3": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "HDR8": "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
    "BUCK_IN": "DIY-Auto:LM2596_IN",       # 2026-11-05: LM2596 module on the PCB (2x M3 + soldered pads), no cables
    "BUCK_OUT": "DIY-Auto:LM2596_OUT",
}

sch = ksa.create_schematic("DIY-Auto")
sch.set_paper_size("A3")
sch.set_title_block(title="DIY-Auto — voeding 2S, ESP32, TB6612FNG-motordriver", rev="4", company="Ruben")

_parts = {}      # ref -> (lib_id, x, y, rot, mirror)
_mirror = {}     # uuid -> 'x' | 'y'
_uuid2ref = {}   # uuid -> referentie
_n = {"pwr": 0}

def r2(v):
    return round(v, 2)

def place(lib, ref, value, x, y, fp=None, rot=0, mirror=None):
    c = sch.components.add(lib, reference=ref, value=value, position=(r2(x), r2(y)), footprint=fp, rotation=rot)
    _parts[ref] = (lib, x, y, rot, mirror)
    _uuid2ref[str(c.uuid)] = ref
    if mirror:
        _mirror[str(c.uuid)] = mirror
    return c

def pin(ref, num):
    """Pinpositie in schemacoördinaten (y naar beneden), met rotatie (CCW) en spiegeling."""
    lib, cx, cy, rot, mirror = _parts[ref]
    info = ksa.get_symbol_info(lib)
    p = next(p for p in info.pins if p.number == str(num))
    px, py = p.position.x, p.position.y          # symboolruimte, y omhoog
    if mirror == "y": px = -px
    if mirror == "x": py = -py
    sx, sy = px, -py                              # naar scherm (y omlaag)
    t = math.radians(rot)
    rx = sx * math.cos(t) + sy * math.sin(t)
    ry = -sx * math.sin(t) + sy * math.cos(t)
    return (r2(cx + rx), r2(cy + ry))

def W(*pts):
    for a, b in zip(pts, pts[1:]):
        sch.add_wire((r2(a[0]), r2(a[1])), (r2(b[0]), r2(b[1])))

def J(p):
    sch.junctions.add((r2(p[0]), r2(p[1])))

def PWR(name, p, rot=0):
    _n["pwr"] += 1
    sch.components.add(f"power:{name}", reference=f"#PWR{_n['pwr']:03d}", value=name, position=(r2(p[0]), r2(p[1])), rotation=rot)

def FLAG(p, rot=0):
    _n["pwr"] += 1
    sch.components.add("power:PWR_FLAG", reference=f"#FLG{_n['pwr']:03d}", value="PWR_FLAG", position=(r2(p[0]), r2(p[1])), rotation=rot)

def LBL(name, p, left=False):
    sch.add_label(name, position=(r2(p[0]), r2(p[1])), rotation=180 if left else 0)

def TXT(s, p, size=1.27, bold=False):
    sch.add_text(s, position=(r2(p[0]), r2(p[1])), size=size, bold=bold)

# ============================================================ VOEDING
yR = 20 * G
TXT("VOEDING", (25.4, 30.48), 2.5, True)
TXT("accu 2S Li-ion 7,4 V (6,0–8,4 V), rode JST BEC → J1 → +BATT (geen zekering, 2026-11-02).", (25.4, 35.56), 1.5)
TXT("Geen schakelaar: de stekker is aan/uit. Laden: witte stekker aan de USB-kabel.", (25.4, 39.37), 1.5)

place("Connector_Generic:Conn_01x02", "J1", "ACCU 7,4V", 12 * G, yR, FP["TERM2"], mirror="y")
j1p, j1n = (12 * G + 5.08, yR), (12 * G + 5.08, yR + G)
W(j1n, (15 * G, yR + G), (15 * G, yR + 2 * G)); PWR("GND", (15 * G, yR + 2 * G))

place("Device:C_Polarized", "C1", "470uF 16V", 28 * G, yR + 2 * G, FP["CP"])
place("Device:C", "C2", "100nF", 33 * G, yR + 2 * G, FP["C"])
taps = [26 * G, 28 * G, 33 * G, 36 * G]
W(j1p, *[(x, yR) for x in taps])
for x in taps[:-1]: J((x, yR))
PWR("+BATT", (26 * G, yR))                       # netnaam voor VM van de motordriver
FLAG((36 * G, yR))                               # +BATT wordt gevoed door de accu
for c in ("C1", "C2"):
    W((_parts[c][1], yR), pin(c, 1)); PWR("GND", pin(c, 2))

FLAG((20 * G, yR + 6 * G)); W((20 * G, yR + 6 * G), (20 * G, yR + 7 * G)); PWR("GND", (20 * G, yR + 7 * G))
TXT("ESP32: 5 V van de LM2596 via D1 op VIN.", (40 * G, yR - 1 * G), 1.5, True)
TXT("USB mag tegelijk: D1 houdt USB-stroom uit de buck.", (40 * G, yR + 1 * G), 1.5)
TXT("ESP32-GND naar accu-min.", (40 * G, yR + 3 * G), 1.5)

# accuspanning meten: 20k / 5k1 → 8,4 V wordt 1,71 V op GPIO34 (Ruben heeft geen 10k)
xs = 68 * G
PWR("+BATT", (xs, yR - 4 * G))
place("Device:R", "R41", "20k", xs, yR - 2 * G, FP["R"])
place("Device:R", "R42", "5.1k", xs, yR + 3 * G, FP["R"])
place("Device:C", "C6", "100nF", xs + 3 * G, yR + 3 * G, FP["C"])
W((xs, yR - 4 * G), pin("R41", 1))
node = (xs, yR + G)
W(pin("R41", 2), node, pin("R42", 1))
W(node, (xs + 3 * G, yR + G), (xs + 6 * G, yR + G)); J(node); J((xs + 3 * G, yR + G))
W((xs + 3 * G, yR + G), pin("C6", 1))
PWR("GND", pin("R42", 2)); PWR("GND", pin("C6", 2))
LBL("VBAT_SENSE", (xs + 6 * G, yR + G))
TXT("ACCUMETING", (xs + 3 * G, yR - 6 * G), 2.0, True)
TXT("8,4 V → 1,71 V op GPIO34 (×4,92)", (xs + 3 * G, yR - 4 * G), 1.27)

# ============================================================ ESP32
TXT("ESP32 DevKit v1 (30 pins)", (25.4, 100.33), 2.5, True)
TXT("op vrouwelijke headers, zodat je de DevKit kan uittrekken", (25.4, 105.41), 1.5)
LEFT = ["EN", "VP/36", "VN/39", "D34", "D35", "D32", "D33", "D25", "D26", "D27", "D14", "D12", "D13", "GND", "VIN"]
RIGHT = ["D23", "D22", "TX0", "RX0", "D21", "D19", "D18", "D5", "TX2", "RX2", "D4", "D2", "D15", "GND", "3V3"]
MAP_L = {4: "VBAT_SENSE", 6: "B_IN1", 7: "B_IN2", 8: "A_IN1", 9: "A_IN2", 10: "A_PWM", 14: "GND", 15: "VIN"}
MAP_R = {11: "B_PWM", 7: "STBY", 14: "GND", 15: "+3V3", 6: "SERVO_PWM"}
for ref, x0, names, mp in [("J2", 30 * G, LEFT, MAP_L), ("J3", 60 * G, RIGHT, MAP_R)]:
    place("Connector_Generic:Conn_01x15", ref, "DevKit " + ("LINKS" if ref == "J2" else "RECHTS"), x0, 55 * G, FP["HDR15"])
    for k, nm in enumerate(names, start=1):
        p = pin(ref, k)
        TXT(nm, (p[0] + 7.62, p[1]), 1.27)
        if k in mp:
            # GND kort, +5V lang: zo overlappen de twee zijwaartse powersymbolen niet
            n = {"GND": 2, "+5V": 6, "+3V3": 6}.get(mp[k], 3)
            end = (p[0] - n * G, p[1])
            W(p, end)
            if mp[k] in ("GND", "+5V", "+3V3"):
                PWR(mp[k], end, rot=270 if mp[k] == "GND" else 90)   # beide naar links
            else:
                LBL(mp[k], end, left=True)
        else:
            sch.no_connects.add(p)


# ============================================================ 5 V (LM2596-module naast de print) + SERVO
def tie(ref, num, name, pwr=False, n=3):
    """Korte draad van een pin naar buiten, met een powersymbool of label op het einde."""
    p = pin(ref, num)
    dx, dy = p[0] - _parts[ref][1], p[1] - _parts[ref][2]
    if abs(dx) >= abs(dy):
        sg = 1 if dx > 0 else -1
        end = (p[0] + sg * n * G, p[1])
        rot = {("GND", -1): 270, ("GND", 1): 90}.get((name, sg), 90 if sg < 0 else 270)
    else:
        sg = 1 if dy > 0 else -1
        end = (p[0], p[1] + sg * n * G)
        rot = 0 if (name == "GND") == (sg > 0) else 180
    W(p, end)
    if pwr:
        PWR(name, end, rot=rot)
    else:
        LBL(name, end, left=(end[0] < p[0]))

x5, y5 = 20 * G, 94 * G
TXT("5 V: LM2596-MODULE (ingesteld op 5,0 V) + SERVO", (x5 - 2 * G, y5 - 6 * G), 2.5, True)
TXT("J6 = IN+/IN-, J7 = OUT+/OUT- (LM2596-module op de print: 2x M3 + pads gesoldeerd); eerst 5,0 V instellen en meten, dan pas de ESP32 erin", (x5 - 2 * G, y5 - 4 * G), 1.5)
place("Connector_Generic:Conn_01x02", "J6", "BUCK IN", x5, y5, FP["BUCK_IN"])
tie("J6", 1, "+BATT", pwr=True, n=6); tie("J6", 2, "GND", pwr=True, n=2)
place("Connector_Generic:Conn_01x02", "J7", "BUCK 5V", x5 + 16 * G, y5, FP["BUCK_OUT"])
tie("J7", 1, "+5V", pwr=True, n=6); tie("J7", 2, "GND", pwr=True, n=2)
FLAG((x5 + 20 * G, y5 - 1 * G)); W((x5 + 20 * G, y5 - 1 * G), (x5 + 20 * G, y5)); PWR("+5V", (x5 + 20 * G, y5), rot=180)
place("Device:C", "C7", "100nF", x5 + 26 * G, y5 + 1 * G, FP["C"])
tie("C7", 1, "+5V", pwr=True, n=2); tie("C7", 2, "GND", pwr=True, n=2)
place("Diode:1N5819", "D1", "1N5819", x5 + 36 * G, y5 + 1 * G, FP["DO41"])
tie("D1", 2, "+5V", pwr=True); tie("D1", 1, "VIN")
place("Connector_Generic:Conn_01x03", "J4", "SERVO", x5 + 52 * G, y5, FP["HDR3"])
tie("J4", 1, "GND", pwr=True, n=2); tie("J4", 2, "+5V", pwr=True, n=6); tie("J4", 3, "SERVO_SIG")
place("Device:R", "R6", "1k", x5 + 64 * G, y5 + 1 * G, FP["R"], rot=90)
tie("R6", 1, "SERVO_PWM"); tie("R6", 2, "SERVO_SIG")
TXT("D1: Schottky, anode aan +5V, kathode naar VIN van de DevKit", (x5 + 30 * G, y5 + 5 * G), 1.27)
TXT("servo: 1 GND (bruin), 2 +5V (rood), 3 signaal (oranje) op GPIO19 via 1k", (x5 + 46 * G, y5 + 7 * G), 1.27)

# ============================================================ MOTORDRIVER (TB6612FNG-module)
# Breakoutmodule op 2 vrouwelijke 1x8-headers. Pinvolgorde van de gangbare module (SparkFun ROB-14450 en klonen):
# rij 1 VM VCC GND AO1 AO2 BO2 BO1 GND, rij 2 PWMA AIN2 AIN1 STBY BIN1 BIN2 PWMB GND. Controleer dit op jouw module.
xd, yd = 92 * G, 18 * G
TXT("MOTORDRIVER TB6612FNG (module)", (xd - 4 * G, yd - 6 * G), 2.5, True)
TXT("VM 2,5–13,5 V, 1,2 A continu / 3,2 A piek per kanaal, dead-time en thermische beveiliging zitten in de chip", (xd - 4 * G, yd - 4 * G), 1.5)
ROW1 = ["VM", "VCC", "GND", "AO1", "AO2", "BO2", "BO1", "GND"]
ROW2 = ["PWMA", "AIN2", "AIN1", "STBY", "BIN1", "BIN2", "PWMB", "GND"]
NET1 = {1: ("+BATT", True), 2: ("+3V3", True), 3: ("GND", True), 4: ("MA1", False), 5: ("MA2", False),
        6: ("MB2", False), 7: ("MB1", False), 8: ("GND", True)}
NET2 = {1: ("A_PWM", False), 2: ("A_IN2", False), 3: ("A_IN1", False), 4: ("STBY", False), 5: ("B_IN1", False),
        6: ("B_IN2", False), 7: ("B_PWM", False), 8: ("GND", True)}
for ref, x0, names, mp, val in [("J8", xd, ROW1, NET1, "TB6612 VM/MOTOR"), ("J9", xd + 24 * G, ROW2, NET2, "TB6612 LOGICA")]:
    place("Connector_Generic:Conn_01x08", ref, val, x0, yd + 4 * G, FP["HDR8"])
    for k, nm in enumerate(names, start=1):
        p = pin(ref, k)
        TXT(nm, (p[0] + 7.62, p[1]), 1.27)
        name, pw = mp[k]
        end = (p[0] - (2 if name == "GND" else 4) * G, p[1])   # altijd naar links (tie() kiest verticaal bij de buitenste pinnen)
        W(p, end)
        if pw:
            PWR(name, end, rot=270 if name == "GND" else 90)
        else:
            LBL(name, end, left=True)
FLAG((xd + 10 * G, yd + 16 * G)); W((xd + 10 * G, yd + 16 * G), (xd + 10 * G, yd + 17 * G)); PWR("+3V3", (xd + 10 * G, yd + 17 * G), rot=180)

# STBY: 20k pull-down, zodat de driver uit staat tot de ESP32 opgestart is
place("Device:R", "R7", "20k", xd + 32 * G, yd + 20 * G, FP["R"])
tie("R7", 1, "STBY"); tie("R7", 2, "GND", pwr=True, n=2)

# motoren met een 100nF ontstoorcondensator over de klemmen
def motor(M, Cm, a, b, x, y, title):
    TXT(title, (x - 4 * G, y - 5 * G), 2.0, True)
    place("Motor:Motor_DC", M, title, x, y, FP["TERM2"], rot=90)
    tL, tR = (x - 5 * G, y), (x + 5 * G, y)
    W(pin(M, 1), tL); W(pin(M, 2), tR); J(tL); J(tR)
    LBL(a, tL, left=True); LBL(b, tR)
    place("Device:C", Cm, "100nF", x, y + 4 * G, FP["C"], rot=90)
    cl, cr = sorted([pin(Cm, 1), pin(Cm, 2)], key=lambda p: p[0])
    W(tL, (tL[0], cl[1]), cl); W(tR, (tR[0], cr[1]), cr)

motor("M1", "C150", "MA1", "MA2", xd + 6 * G, yd + 34 * G, "MOTOR A (links)")
motor("M2", "C250", "MB1", "MB2", xd + 26 * G, yd + 34 * G, "MOTOR B (rechts)")

TXT("REGELS VOOR DE CODE", (25.4, 190.5), 2.0, True)
TXT("1. STBY = 1 na het opstarten, anders draait er niets.", (25.4, 195.58), 1.5)
TXT("2. Vooruit A: A_IN1 = 1, A_IN2 = 0, A_PWM = snelheid.   Achteruit: A_IN1 = 0, A_IN2 = 1.   Idem voor B.", (25.4, 200.66), 1.5)
TXT("3. Remmen: IN1 = IN2 = 1.   Uitrollen: IN1 = IN2 = 0.   Kortsluiting kan niet: de chip regelt de dead-time.", (25.4, 205.74), 1.5)
TXT("4. PWM-frequentie 20 kHz (max 100 kHz): dan zoemt de motor niet.", (25.4, 210.82), 1.5)

OUT.parent.mkdir(parents=True, exist_ok=True)
sch.save(str(OUT))

# ---- nabewerking: spiegelingen en tekst links uitlijnen (kan kicad-sch-api niet zelf)
txt = OUT.read_text()
lines = txt.split("\n")
out, i = [], 0
while i < len(lines):
    ln = lines[i]
    out.append(ln)
    if ln == "\t(symbol" and i + 2 < len(lines) and lines[i + 2].lstrip().startswith("(at "):
        # zoek de uuid van dit symbool
        blk = "\n".join(lines[i:i + 12])
        m = re.search(r'\(uuid "([^"]+)"\)', blk)
        if m and m.group(1) in _mirror:
            out.append(lines[i + 1]); out.append(lines[i + 2])
            out.append(f"\t\t(mirror {_mirror[m.group(1)]})")
            i += 3
            continue
    i += 1
txt = "\n".join(out)
# tekstblokken: justify left
txt = re.sub(r'(\(text "(?:[^"\\]|\\.)*"\n(?:\t\t.*\n)*?\t\t\(effects\n\t\t\t\(font\n(?:\t\t\t\t.*\n)*?\t\t\t\))', r'\1\n\t\t\t(justify left)', txt)

# ---- veldplaatsing: Reference en Value leesbaar naast elk onderdeel
def field_layout(ref):
    """(x, y, justify) voor Reference en Value, plus hoek.
    KiCad draait/spiegelt veldhoek en uitlijning mee met het symbool, dus:
    - bij rotatie 90 schrijf je hoek 90 om horizontale tekst te krijgen;
    - bij spiegeling y of rotatie 180 wisselt links/rechts om."""
    lib, cx, cy, rot, mirror = _parts[ref]
    name = lib.split(":")[1]
    flipped = (rot == 180) or (mirror == "y")
    def j(side):
        if side is None: return None
        return {"left": "right", "right": "left"}[side] if flipped else side
    ang = 90 if rot in (90, 270) else 0
    if ref == "C1":   # waarde links, anders loopt "470uF 25V" over C2
        return (cx - 2.54, cy - 1.27, "right"), (cx - 2.54, cy + 1.27, "right"), ang
    if name in ("R", "C", "C_Polarized", "Fuse"):
        if rot in (90, 270):
            return (cx, cy - 2.54, None), (cx, cy + 2.54, None), ang
        return (cx + 2.54, cy - 1.27, j("left")), (cx + 2.54, cy + 1.27, j("left")), ang
    if ref.startswith("Q"):
        if flipped:
            return (cx - 5.08, cy - 1.27, j("right")), (cx - 5.08, cy + 1.27, j("right")), ang
        return (cx + 5.08, cy - 1.27, j("left")), (cx + 5.08, cy + 1.27, j("left")), ang
    if name == "Motor_DC":
        return (cx + 1.27, cy - 7.62, None), (cx + 1.27, cy - 5.08, None), ang
    if name == "L7805":
        return (cx, cy - 7.62, None), (cx, cy - 5.08, None), ang
    if ref == "J1":
        return (cx, cy + 6.35, None), (cx, cy - 3.81, None), ang
    if name == "1N5819":
        return (cx, cy - 2.54, None), (cx, cy + 2.54, None), ang
    return None

def rewrite_fields(text):
    L = text.split("\n"); out = []; i = 0; ref = None
    while i < len(L):
        ln = L[i]
        if ln == "\t(symbol":
            ref = None
        m = re.match(r'\t\t\(uuid "([^"]+)"\)$', ln)
        if m and m.group(1) in _uuid2ref:
            ref = _uuid2ref[m.group(1)]
        m = re.match(r'\t\t\(property "(Reference|Value)" ', ln)
        if m and ref and field_layout(ref):
            (rx, ry, rj), (vx, vy, vj), ang = field_layout(ref)
            x, y, j = (rx, ry, rj) if m.group(1) == "Reference" else (vx, vy, vj)
            # blok tot de sluitende "\t\t)" overslaan en opnieuw schrijven
            k = i + 1
            while L[k] != "\t\t)":
                k += 1
            hidden = any("(hide yes)" in l for l in L[i:k])
            out += [ln, f"\t\t\t(at {r2(x)} {r2(y)} {ang})", "\t\t\t(effects", "\t\t\t\t(font", "\t\t\t\t\t(size 1.27 1.27)", "\t\t\t\t)"]
            if j: out.append(f"\t\t\t\t(justify {j})")
            if hidden: out.append("\t\t\t\t(hide yes)")
            out += ["\t\t\t)", "\t\t)"]
            i = k + 1
            continue
        out.append(ln); i += 1
    return "\n".join(out)

txt = rewrite_fields(txt)
# labels met hoek 180: tekst links van het ankerpunt (zoals KiCad het zelf schrijft)
txt = re.sub(r'(\t\(label "[^"]*"\n\t\t\(at [-\d.]+ [-\d.]+ 180\)\n\t\t\(effects\n\t\t\t\(font\n\t\t\t\t\(size [^)]*\)\n\t\t\t\)\n\t\t\t\(justify )left bottom\)',
             r'\1right bottom)', txt)
OUT.write_text(txt)
print("geschreven:", OUT, "| gespiegeld:", len(_mirror))
