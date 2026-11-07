"""Breadboard-layout voor voeding + H-brug A, gecontroleerd tegen de KiCad-netlist.

Draaien:  .venv/bin/python Scripts/gen_breadboard.py [netlist] [uitvoer.png]
"""
import re, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Wedge

NETLIST = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/diy.net")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("breadboard.png")
BBRD = Path(sys.argv[3]) if len(sys.argv) > 3 else None      # optioneel: sessie voor de KiCad-plugin Breadboard Builder

# ------------------------------------------------------------------ geometrie
ROWY = {r: y for r, y in zip("abcde", [10, 9, 8, 7, 6])} | {r: y for r, y in zip("fghij", [4, 3, 2, 1, 0])}
RAILY = {"+11": 13.0, "GNDt": 12.0, "GNDb": -2.0}
NCOL = 63

def H(row, col):            # gat in het bord
    return ("h", row, col)
def RL(rail, col):          # gat in een voedingsrail
    return ("r", rail, col)
def OFF(name):              # aansluiting naast het bord (ESP32, accu)
    return ("o", name)

def xy(p):
    if p[0] == "h": return (p[2], ROWY[p[1]])
    if p[0] == "r": return (p[2], RAILY[p[1]])
    return OFFXY[p[1]]

def node(p):
    """Elektrische knoop van een gat: kolomstrip of rail."""
    if p[0] == "h": return ("T" if p[1] in "abcde" else "B") + str(p[2])
    if p[0] == "r": return p[1]
    return "OFF:" + p[1]

# ESP32 onder het bord, accu links boven
ESP_PINS = ["GND", "GPIO25", "GPIO26", "GPIO27", "GPIO13"]
OFFXY = {f"ESP.{n}": (8 + i * 7.5, -7.2) for i, n in enumerate(ESP_PINS)}
OFFXY |= {"BAT+": (-3.5, 13.0), "BAT-": (-3.5, 12.0)}
ESP_KICAD = {"GND": "J2.14", "GPIO25": "J2.8", "GPIO26": "J2.9", "GPIO27": "J2.10", "GPIO13": "J2.13"}

# ------------------------------------------------------------------ onderdelen
# pins: KiCad-pinnummer -> gat.  lab = (x, y, uitlijning) van het tekstlabel.
# TO-220 en TO-92 staan allemaal met de tekstkant/platte kant naar rij j (naar jou toe):
# pootjes van links naar rechts G D S; lijf richting rij a.
# 2N3904 staat omgekeerd: platte kant naar rij a (van je weg), zodat de pootjes C B E blijven.
P = []
def part(ref, kind, label, pins, lab, **kw):
    P.append(dict(ref=ref, kind=kind, label=label, pins=pins, lab=lab, **kw))

# --- voeding: alleen buffercondensatoren, de ESP32 krijgt stroom via USB
part("C1", "elco", "470µF", {"1": RL("+11", 12), "2": RL("GNDt", 12)}, (12, 14.0, "center"))
part("C2", "cap", "100nF", {"1": RL("+11", 15), "2": RL("GNDt", 15)}, (15, 14.0, "center"))

# --- H-brug A, links boven: 2N3904 + P-MOSFET
part("R102", "res", "10k", {"1": H("b", 17), "2": H("b", 21)}, (19, 9.65, "center"))
part("Q102", "to92", "2N3904", {"3": H("d", 20), "2": H("d", 21), "1": H("d", 22)}, (19.6, 6.0, "right"), legs=["C", "B", "E"], flat_away=True)
part("R103", "res", "10k", {"1": H("a", 21), "2": RL("GNDt", 21)}, (20.4, 11.1, "right"))
part("R101", "res", "10k", {"1": RL("+11", 27), "2": H("a", 27)}, (26.4, 11.5, "right"))
part("Q101", "to220", "IRF9540N", {"1": H("d", 27), "2": H("d", 28), "3": H("d", 29)}, (30.0, 7.5, "left"), legs=["G", "D", "S"])
# --- links onder: N-MOSFET
part("Q103", "to220", "IRLZ44N", {"1": H("h", 27), "2": H("h", 28), "3": H("h", 29)}, (26.4, 3.0, "right"), legs=["G", "D", "S"])
part("R104", "res", "1k", {"1": H("i", 23), "2": H("i", 27)}, (25, 0.45, "center"))
part("R105", "res", "10k", {"1": H("j", 23), "2": RL("GNDb", 23)}, (22.4, -1.0, "right"))

# --- rechts boven
part("R111", "res", "10k", {"1": RL("+11", 44), "2": H("a", 44)}, (43.4, 11.5, "right"))
part("Q111", "to220", "IRF9540N", {"1": H("d", 44), "2": H("d", 45), "3": H("d", 46)}, (43.0, 7.5, "right"), legs=["G", "D", "S"])
part("Q112", "to92", "2N3904", {"3": H("d", 49), "2": H("d", 50), "1": H("d", 51)}, (52.4, 6.0, "left"), legs=["C", "B", "E"], flat_away=True)
part("R113", "res", "10k", {"1": H("a", 50), "2": RL("GNDt", 50)}, (49.4, 11.1, "right"))
part("R112", "res", "10k", {"1": H("b", 50), "2": H("b", 54)}, (52, 9.65, "center"))
# --- rechts onder
part("Q113", "to220", "IRLZ44N", {"1": H("h", 44), "2": H("h", 45), "3": H("h", 46)}, (43.4, 3.0, "right"), legs=["G", "D", "S"])
part("R114", "res", "1k", {"1": H("i", 44), "2": H("i", 40)}, (42, 0.45, "center"))
part("R115", "res", "10k", {"1": H("j", 40), "2": RL("GNDb", 40)}, (39.4, -1.0, "right"))

# --- testlast in plaats van de motor: 1k + rode en groene led antiparallel
part("R_T", "res", "1k", {"1": H("j", 28), "2": H("j", 33)}, (30.5, -0.55, "center"), test=True)
part("LED_R", "led", "rood: vooruit", {"A": H("h", 33), "K": H("h", 36)}, (34.5, 2.75, "center"), color="#e53935", test=True)
part("LED_G", "led", "groen: achteruit", {"A": H("i", 36), "K": H("i", 33)}, (37.0, 1.0, "left"), color="#2e7d32", test=True)
# motoraansluiting (na de ledtest)
part("M1", "motor", "MOTOR A", {"1": H("i", 28), "2": H("i", 45)}, (0, 0, "left"))


# ------------------------------------------------------------------ bouwstappen
STEP_OF_REF = {}
for _refs, _n in [(["C1", "C2"], 1),
                  (["R101", "R102", "R103", "Q101", "Q102", "R111", "R112", "R113", "Q111", "Q112"], 2),
                  (["Q103", "R104", "R105", "Q113", "R114", "R115", "M1"], 3),
                  (["R_T", "LED_R", "LED_G"], 4)]:
    for _r in _refs:
        STEP_OF_REF[_r] = _n
for _pt in P:
    _pt["step"] = STEP_OF_REF.get(_pt["ref"], 4)

STEP_TITEL = {
    1: ("STAP 1 — VOEDING", "Rails en buffercondensatoren. Sluit de accu nog niet aan."),
    2: ("STAP 2 — HOGE KANT", "P-MOSFETs met hun 2N3904-driver, pull-up en basisweerstanden."),
    3: ("STAP 3 — LAGE KANT EN MOTOR", "N-MOSFETs, gateweerstanden en de twee motorgaten M+ en M−."),
    4: ("STAP 4 — ESP32 EN TESTLAST", "Vier dupontdraden naar de ESP32, 1 kΩ met twee leds. Accu pas nu aansluiten."),
}

# ------------------------------------------------------------------ draden en losse aansluitingen
WIRES = [
    (OFF("BAT+"), RL("+11", 1), "#c62828", 1), (OFF("BAT-"), RL("GNDt", 1), "#222", 1),
    (RL("GNDt", 62), RL("GNDb", 62), "#222", 1),               # beide GND-rails samen
    (H("a", 22), RL("GNDt", 22), "#222", 2),                   # emitter Q102
    (H("b", 20), H("b", 27), "#78909c", 2),                    # collector Q102 -> gate Q101
    (H("a", 29), RL("+11", 29), "#c62828", 2),                 # source Q101 -> +11 V
    (H("e", 28), H("f", 28), "#1e88e5", 3),                    # drain boven -> drain onder = M+
    (H("j", 29), RL("GNDb", 29), "#222", 3),                   # source Q103 -> GND
    (H("b", 49), H("b", 44), "#78909c", 2),                    # collector Q112 -> gate Q111
    (H("a", 46), RL("+11", 46), "#c62828", 2),
    (H("a", 51), RL("GNDt", 51), "#222", 2),
    (H("e", 45), H("f", 45), "#1e88e5", 3),                    # = M−
    (H("j", 46), RL("GNDb", 46), "#222", 3),
    (H("j", 36), H("j", 45), "#1e88e5", 4),                    # testlast naar M−
]
# dupontkabels naar de ESP32: (gat, ESP32-pin, kleur, tekst links/rechts)
TAGS = [
    (RL("GNDb", 3), "GND", "#222", "right"),
    (H("c", 17), "GPIO25", "#f9a825", "left"),
    (H("f", 23), "GPIO27", "#1565c0", "left"),
    (H("c", 54), "GPIO26", "#2e7d32", "right"),
    (H("f", 40), "GPIO13", "#8e24aa", "left"),
]
for h, pin, col, side in TAGS:
    OFFXY["ESP." + pin] = xy(h)
    WIRES.append((OFF("ESP." + pin), h, None, 4))

# ------------------------------------------------------------------ controle tegen KiCad
def union_find(pairs):
    par = {}
    def f(a):
        par.setdefault(a, a)
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for a, b in pairs:
        par[f(a)] = f(b)
    return f

find = union_find([(node(a), node(b)) for a, b, _, _ in WIRES])
bb_nets = {}
for pt in P:
    if pt.get("test"): continue
    for num, h in pt["pins"].items():
        bb_nets.setdefault(find(node(h)), set()).add(f"{pt['ref']}.{num}")
for name, kic in ESP_KICAD.items():
    bb_nets.setdefault(find(node(OFF("ESP." + name))), set()).add(kic)
bb_nets.setdefault(find("+11"), set()).add("BATT+")

s = NETLIST.read_text(); body = s[s.find("(nets"):]
keep_refs = {p["ref"] for p in P if not p.get("test")}
keep_pins = set(ESP_KICAD.values())
kc = []
for m in re.finditer(r'\(net\s+\(code "?\d+"?\)\s+\(name "([^"]*)"\)(.*?)(?=\n\t\t\(net\s|\Z)', body, re.S):
    pins = {f"{r}.{n}" for r, n in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', m.group(2))}
    pins = {x for x in pins if x.split(".")[0] in keep_refs or x in keep_pins}
    if m.group(1) == "+BATT": pins.add("BATT+")
    if len(pins) > 1: kc.append(frozenset(pins))
bb = [frozenset(v) for v in bb_nets.values() if len(v) > 1]
missing = set(kc) - set(bb); extra = set(bb) - set(kc)
if missing or extra:
    print("FOUT: breadboard wijkt af van KiCad")
    for n in missing: print("  KiCad :", sorted(n))
    for n in extra: print("  bord  :", sorted(n))
    sys.exit(1)
print(f"OK: {len(bb)} netten identiek aan KiCad")

# dubbel gebruikte gaten?
used = {}
for pt in P:
    for h in pt["pins"].values():
        if h[0] == "h": used.setdefault(h, []).append(pt["ref"])
for a, b, _, _ in WIRES:
    for h in (a, b):
        if h[0] == "h": used.setdefault(h, []).append("draad")
dups = {k: v for k, v in used.items() if len(v) > 1}
if dups:
    print("FOUT: gat dubbel gebruikt:", dups); sys.exit(1)

# ------------------------------------------------------------------ tekenen
import numpy as np

FADE = 0.16                      # doorzichtigheid van wat in een vorige stap al stond

def board(ax):
    """Lege breadboardplaat met rails, rijletters en kolomnummers."""
    ax.set_xlim(-6.8, NCOL + 2.4); ax.set_ylim(-5.6, 16.6); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(FancyBboxPatch((-0.5, -3.0), NCOL + 1.5, 17.0, boxstyle="round,pad=0.2",
                                fc="#f5f3ee", ec="#c9c4b8", lw=1.5))
    ax.add_patch(Rectangle((-0.3, 4.6), NCOL + 1.1, 0.8, fc="#e3dfd5", ec="none"))
    for rail, col in [("+11", "#c62828"), ("GNDt", "#1a1a1a"), ("GNDb", "#1a1a1a")]:
        y = RAILY[rail]
        ax.plot([0.2, NCOL + 0.3], [y + 0.45, y + 0.45], color=col, lw=1.2)
        ax.text(-0.4, y, {"+11": "+11V", "GNDt": "GND", "GNDb": "GND"}[rail], ha="right", va="center",
                fontsize=10, color=col, weight="bold")
        for c_ in range(1, NCOL + 1):
            ax.add_patch(Rectangle((c_ - 0.15, y - 0.15), 0.3, 0.3, fc="#bdb7aa", ec="none"))
    for r, y in ROWY.items():
        ax.text(-0.1, y, r, ha="right", va="center", fontsize=8, color="#8a8478")
        ax.text(NCOL + 0.6, y, r, ha="left", va="center", fontsize=8, color="#8a8478")
        for c_ in range(1, NCOL + 1):
            ax.add_patch(Rectangle((c_ - 0.15, y - 0.15), 0.3, 0.3, fc="#bdb7aa", ec="none"))
    for c_ in [1] + list(range(5, NCOL + 1, 5)):
        ax.text(c_, 5.0, str(c_), ha="center", va="center", fontsize=7.5, color="#8a8478")

def dot(ax, p, color="#333", r=0.17, al=1.0):
    x, y = xy(p); ax.add_patch(Circle((x, y), r, fc=color, ec="none", alpha=al, zorder=6))

def lbl(ax, x, y, s, ha="center", al=1.0, **kw):
    ax.text(x, y, s, ha=ha, va="center", fontsize=kw.pop("fs", 8.5), alpha=al, zorder=9, **kw)

def draw_wire(ax, a, b, color, al):
    (x1, y1), (x2, y2) = xy(a), xy(b)
    if abs(x1 - x2) < 0.01 or a[0] == "o" or b[0] == "o":
        ax.plot([x1, x2], [y1, y2], color=color, lw=3.2, alpha=al, solid_capstyle="round", zorder=4)
    else:
        t = np.linspace(0, 1, 30); bump = 0.45 * np.sin(np.pi * t) * (1 if y1 >= 5 else -1)
        ax.plot(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t + bump, color=color, lw=3.2, alpha=al,
                solid_capstyle="round", zorder=4)
    for q in (a, b):
        if q[0] != "o": dot(ax, q, color, al=al)

def draw_part(ax, pt, al=1.0, labels=True):
    pins = list(pt["pins"].values()); k = pt["kind"]; lx, ly, lha = pt["lab"]
    text = f"{pt['ref']}\n{pt['label']}" if k in ("to220", "to92") else f"{pt['ref']} {pt['label']}"
    if k in ("to220", "to92"):
        xs = [xy(q)[0] for q in pins]; y = xy(pins[0])[1]; xc = sum(xs) / 3
        if k == "to220":                                  # 10 x 15 mm, tab naar rij a
            for q in pins:
                ax.plot([xy(q)[0]] * 2, [y, y + 0.6], color="#9e9e9e", lw=1.6, alpha=al, zorder=6)
            ax.add_patch(Rectangle((xc - 1.2, y + 0.6), 2.4, 2.6, fc="#263238", ec="black", alpha=0.5 * al, zorder=7))
            ax.add_patch(Rectangle((xc - 1.2, y + 3.2), 2.4, 0.9, fc="#b0bec5", ec="#78909c", alpha=0.7 * al, zorder=7))
        elif pt.get("flat_away"):                         # platte kant van je weg
            ax.add_patch(Rectangle((xc - 0.62, y + 0.92), 1.24, 0.08, fc="#263238", alpha=0.9 * al, zorder=7))
            ax.add_patch(Wedge((xc, y + 0.94), 0.62, 180, 360, fc="#263238", ec="black", alpha=0.9 * al, zorder=7))
        else:
            ax.add_patch(Rectangle((xc - 0.62, y + 0.22), 1.24, 0.08, fc="#263238", alpha=0.9 * al, zorder=7))
            ax.add_patch(Wedge((xc, y + 0.3), 0.62, 0, 180, fc="#263238", ec="black", alpha=0.9 * al, zorder=7))
        for q, leg in zip(pins, pt["legs"]):
            dot(ax, q, "#9e9e9e", al=al)
            if labels: lbl(ax, xy(q)[0], y - 0.45, leg, fs=7.5, color="#b71c1c", weight="bold")
        if labels: lbl(ax, lx, ly, text, ha=lha, fs=8.5, weight="bold")
        return
    (x1, y1), (x2, y2) = xy(pins[0]), xy(pins[1])
    if k == "motor":
        for q, s_ in zip(pins, ["M+", "M−"]):
            x, y = xy(q)
            ax.add_patch(Circle((x, y), 0.34, fc="none", ec="#6d4c41", lw=2, ls="--", alpha=al, zorder=8))
            if labels: lbl(ax, x + 0.5, y, s_, ha="left", fs=8.5, color="#6d4c41", weight="bold")
        return
    ax.plot([x1, x2], [y1, y2], color="#9e9e9e", lw=1.4, alpha=al, zorder=5)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if k == "res":
        vert = abs(x1 - x2) < 0.01
        w, h = (0.7, 1.8) if vert else (1.8, 0.7)          # verkleind getekend
        ax.add_patch(FancyBboxPatch((mx - w / 2, my - h / 2), w, h, boxstyle="round,pad=0.05",
                                    fc="#e8d3a9", ec="#a1887f", alpha=al, zorder=6))
    elif k in ("cap", "elco"):
        r = 0.65 if k == "cap" else 1.25                   # keramisch 5 mm, elco 10 mm, verkleind
        ax.add_patch(Circle((mx, my), r, fc="#ffb74d" if k == "cap" else "#1565c0", ec="black",
                            alpha=0.85 * al, zorder=6))
        if k == "elco":
            ax.plot([mx - 0.5, mx + 0.5], [my - 0.7] * 2, color="white", lw=2.5, alpha=al, zorder=7)
    elif k == "led":
        ax.add_patch(Circle((mx, my), 0.65, fc=pt["color"], ec="black", alpha=0.85 * al, zorder=6))
    for q in pins: dot(ax, q, "#9e9e9e", al=al)
    if labels:
        lbl(ax, lx, ly, text if k != "led" else pt["label"], ha=lha, fs=7.8 if k != "led" else 8,
            color=pt.get("color", "black"), weight="bold" if k == "led" else "normal", al=al)

def draw_tags(ax, al=1.0):
    for h, pin, col, side in TAGS:
        x, y = xy(h)
        ax.add_patch(Circle((x, y), 0.3, fc=col, ec="black", lw=0.8, alpha=al, zorder=8))
        dx = 0.55 if side == "right" else -0.55
        ax.text(x + dx, y, f"ESP32 {pin}", ha="left" if side == "right" else "right", va="center",
                fontsize=8.5, color="white", weight="bold", alpha=al, zorder=9,
                bbox=dict(boxstyle="round,pad=0.25", fc=col, ec="none", alpha=al))

def draw_accu(ax, al=1.0):
    for n, t, y in [("BAT+", "accu +\n(via zekering 5 A\n+ schakelaar)", 14.6), ("BAT-", "accu −", 10.9)]:
        x, yy = OFFXY[n]
        ax.add_patch(Circle((x, yy), 0.28, fc="#ffd54f", ec="black", alpha=al, zorder=8))
        lbl(ax, x, y, t, fs=8, color="#c62828" if "+" in n else "#222", al=al)

def draw_board(ax, step=None):
    """step=None tekent alles; anders krijgt de huidige stap volle kleur en het vorige werk een waas."""
    board(ax)
    for x, s_ in [(9, "VOEDING"), (24.5, "H-BRUG A — LINKS"), (47.5, "H-BRUG A — RECHTS")]:
        lbl(ax, x, 14.9, s_, fs=10.5, weight="bold", color="#90a4ae")
    for a, b, color, st in WIRES:
        if color is None: continue
        if step is not None and st > step: continue
        draw_wire(ax, a, b, color, 1.0 if step is None or st == step else FADE)
    if step is None or step >= 4:
        draw_tags(ax, 1.0 if step is None or step == 4 else FADE)
    for pt in P:
        st = pt["step"]
        if step is not None and st > step: continue
        al = 1.0 if step is None or st == step else FADE
        draw_part(ax, pt, al, labels=(al == 1.0))
    draw_accu(ax, 1.0 if step in (None, 1) else FADE)
    if step is not None:
        titel, uitleg = STEP_TITEL[step]
        lbl(ax, -6.5, 18.6, titel, ha="left", fs=15, weight="bold", color="#37474f")
        lbl(ax, -6.5, 17.1, uitleg, ha="left", fs=10.5, color="#546e7a")
        ax.set_ylim(-5.6, 19.6)

def draw_legend(ax):
    ax.set_xlim(-6.8, NCOL + 2.4); ax.set_ylim(-11.6, 1.2); ax.set_aspect("equal"); ax.axis("off")
    LY = 0.0
    ax.add_patch(FancyBboxPatch((-5.8, LY - 11.0), NCOL + 7.0, 11.4, boxstyle="round,pad=0.2",
                                fc="#fafafa", ec="#b0bec5", lw=1.2, zorder=2))
    lbl(ax, -5.2, LY - 0.5, "LEGENDE", ha="left", fs=12, weight="bold", color="#37474f")
    lbl(ax, -5.2, LY - 1.5, "Het bord staat op ware grootte: 1 gat = 2,54 mm.  De onderdelen zijn kleiner getekend; hun echte maat staat erbij.", ha="left", fs=9, color="#607d8b")
    def L(x, y, t, fs=8.5, **kw): lbl(ax, x, y, t, ha="left", fs=fs, **kw)

    C1X = -5.2
    L(C1X, LY - 2.9, "DRADEN", fs=10, weight="bold", color="#37474f")
    for i, (col, t) in enumerate([("#c62828", "+11,1 V van de accu"), ("#222", "GND (accu −)"),
                                  ("#1e88e5", "signaal van de ESP32"), ("#90a4ae", "verbinding tussen twee gaten")]):
        yy = LY - 4.0 - i * 1.1
        ax.plot([C1X, C1X + 1.8], [yy, yy], color=col, lw=3.2, solid_capstyle="round", zorder=5)
        L(C1X + 2.3, yy, t)
    L(C1X, LY - 9.0, "Grijs weggevaagd = werk uit een vorige stap.", fs=8.5, color="#607d8b")

    C2X = 14.0
    L(C2X, LY - 2.9, "ONDERDELEN", fs=10, weight="bold", color="#37474f")
    yy = LY - 4.2
    ax.add_patch(FancyBboxPatch((C2X, yy - 0.35), 1.8, 0.7, boxstyle="round,pad=0.05", fc="#e8d3a9", ec="#a1887f", zorder=6))
    L(C2X + 3.4, yy, "weerstand, 6,3 x 2,5 mm")
    yy = LY - 6.2
    ax.add_patch(Circle((C2X + 0.9, yy), 0.65, fc="#ffb74d", ec="black", alpha=0.85, zorder=6))
    L(C2X + 3.4, yy, "keramische condensator 100 nF, 5 mm")
    yy = LY - 9.0
    ax.add_patch(Circle((C2X + 0.9, yy), 1.25, fc="#1565c0", ec="black", alpha=0.85, zorder=6))
    ax.plot([C2X + 0.4, C2X + 1.4], [yy - 0.7] * 2, color="white", lw=2.5, zorder=7)
    L(C2X + 3.4, yy + 0.4, "elco 470 µF, 10 mm")
    L(C2X + 3.4, yy - 0.6, "witte streep = min, naar GND", fs=8)

    C3X = 33.0
    L(C3X, LY - 2.9, "HALFGELEIDERS", fs=10, weight="bold", color="#37474f")
    yy = LY - 5.8
    ax.add_patch(Rectangle((C3X, yy - 1.1), 2.0, 2.2, fc="#263238", ec="black", alpha=0.45, zorder=6))
    ax.add_patch(Rectangle((C3X, yy + 1.1), 2.0, 0.75, fc="#b0bec5", ec="#78909c", alpha=0.6, zorder=6))
    L(C3X + 3.0, yy + 1.3, "TO-220: vermogen, 10 x 15 mm.  Q101, Q103, Q111, Q113")
    L(C3X + 3.0, yy + 0.3, "grijze strip = metalen tab (koeling), naar rij a", fs=8)
    L(C3X + 3.0, yy - 0.7, "tekstkant naar jou, pootjes G  D  S", fs=8)
    L(C3X + 3.0, yy - 1.7, "half doorzichtig: je ziet de gaten eronder", fs=8, color="#607d8b")
    yy = LY - 9.2
    ax.add_patch(Rectangle((C3X + 0.3, yy + 0.5), 1.4, 0.1, fc="#263238", alpha=0.9, zorder=6))
    ax.add_patch(Wedge((C3X + 1.0, yy + 0.5), 0.7, 180, 360, fc="#263238", ec="black", alpha=0.9, zorder=6))
    L(C3X + 3.0, yy + 0.4, "TO-92: klein signaal, 5 mm.  Q102, Q112")
    L(C3X + 3.0, yy - 0.6, "platte kant van je weg, pootjes C  B  E", fs=8)

    C4X = 48.0
    L(C4X, LY - 2.9, "TEKENS", fs=10, weight="bold", color="#37474f")
    ax.add_patch(Circle((C4X + 0.5, LY - 4.1), 0.3, fc="#1e88e5", ec="black", lw=0.8, zorder=8))
    L(C4X + 1.5, LY - 4.1, "gat waar een draad van de ESP32 in komt")
    ax.add_patch(Circle((C4X + 0.5, LY - 5.2), 0.34, fc="none", ec="#6d4c41", lw=2, ls="--", zorder=8))
    L(C4X + 1.5, LY - 5.2, "M+ / M− : hier komen de motordraden")
    ax.add_patch(Circle((C4X + 0.5, LY - 6.3), 0.28, fc="#ffd54f", ec="black", zorder=8))
    L(C4X + 1.5, LY - 6.3, "accudraad, via zekering en schakelaar")
    ax.add_patch(Circle((C4X + 0.5, LY - 7.7), 0.65, fc="#e53935", ec="black", alpha=0.85, zorder=8))
    L(C4X + 1.9, LY - 7.7, "led van de testlast, 5 mm")
    L(C4X, LY - 9.2, "Rijen a–e en f–j: elke rij van 5 gaten is onderling verbonden.", fs=8)
    L(C4X, LY - 10.0, "De + en − rails zijn halverwege onderbroken.", fs=8)
    L(C4X, LY - 10.8, "Leg daar een draadje over, anders staat de rechterhelft dood.", fs=8)

    SX = 19.0; SY = LY - 10.6
    ax.plot([SX, SX + 10], [SY] * 2, color="#37474f", lw=2.5, zorder=6)
    for xx in (SX, SX + 10):
        ax.plot([xx] * 2, [SY - 0.25, SY + 0.25], color="#37474f", lw=2.5, zorder=6)
    lbl(ax, SX + 5, SY + 0.7, "10 gaten = 25,4 mm", fs=8.5, color="#37474f")

VOET = ("Gezien van boven.  MOSFETs: tekstkant naar rij j (naar jou), metalen tab naar rij a.  "
        "Pootjes van links naar rechts: G  D  S.   2N3904: platte kant van je weg (naar rij a), dan C  B  E.")

# --- bouwplaat in vier stappen
fig = plt.figure(figsize=(26, 34))
gs = fig.add_gridspec(5, 1, height_ratios=[1, 1, 1, 1, 0.62], hspace=0.04)
for i in range(4):
    draw_board(fig.add_subplot(gs[i]), step=i + 1)
draw_legend(fig.add_subplot(gs[4]))
fig.text(0.5, 0.075, VOET, ha="center", fontsize=11, color="#37474f")
fig.savefig(OUT, dpi=110, bbox_inches="tight", facecolor="white")
print("geschreven:", OUT)

# --- alles-in-één overzicht
fig2 = plt.figure(figsize=(26, 15))
gs2 = fig2.add_gridspec(2, 1, height_ratios=[1, 0.62], hspace=0.02)
draw_board(fig2.add_subplot(gs2[0]))
draw_legend(fig2.add_subplot(gs2[1]))
OUT2 = OUT.with_name(OUT.stem + "-overzicht" + OUT.suffix)
fig2.savefig(OUT2, dpi=110, bbox_inches="tight", facecolor="white")
print("geschreven:", OUT2)

# ------------------------------------------------------------------ export naar Breadboard Builder (.kicad_bbrd)
def rail_col(i):                      # plugin: railgat i (1..50) staat boven kolom ...
    return ((i - 1) // 5) * 6 + (i - 1) % 5 + 2

def export_bbrd(path, netlist_path):
    import json
    RAIL = {"+11": "top_plus", "GNDt": "top_minus", "GNDb": "bot_minus"}
    used = {r: {25, 26} for r in RAIL.values()}            # 25/26 gereserveerd voor de brug over de railsplitsing
    memo = {}
    def conv(h):
        if h[0] == "h":
            return ["tie", h[2], h[1]]
        if h[0] == "r":
            key = (h[1], h[2])
            if key not in memo:
                rail = RAIL[h[1]]
                idx = min((i for i in range(1, 51) if i not in used[rail]), key=lambda i: abs(rail_col(i) - h[2]))
                used[rail].add(idx); memo[key] = ["rail", rail, idx]
            return memo[key]
        return {"BAT+": ["terminal", "V1"], "BAT-": ["terminal", "GND"]}.get(h[1])
    placements = []
    for pt in P:
        if pt.get("test") or pt["kind"] == "motor":
            continue          # testlast en motor kent de plugin niet
        tid = {"res": "R", "cap": "C", "elco": "C_POL", "diode": "D"}.get(pt["kind"])
        if pt["kind"] == "to220": tid = "PMOS" if pt["label"] == "IRF9540N" else "NMOS"
        if pt["kind"] == "to92": tid = "NPN"
        placements.append({"ref": pt["ref"], "type_id": tid, "flipped": 0,
                           "pins": [[int(n), conv(h)] for n, h in pt["pins"].items()]})
    wires = []
    for a, b, col, _st in WIRES:
        if col is None: continue                            # dupont naar de ESP32: niet op het bord
        wires.append({"h1": conv(a), "h2": conv(b), "color": col if col != "#222" else "#303030"})
    for rail in RAIL.values():                              # brug over de gesplitste rail
        wires.append({"h1": ["rail", rail, 25], "h2": ["rail", rail, 26], "color": "#303030" if "minus" in rail else "#c62828"})
    doc = {"version": 1, "netlist": str(Path(netlist_path).resolve()),
           "board": {"layout": "full"},
           "terminals": {"V1": "+BATT", "GND": "GND"},
           "placements": placements, "wires": wires}
    Path(path).write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print("geschreven:", path)

if BBRD:
    export_bbrd(BBRD, NETLIST)
