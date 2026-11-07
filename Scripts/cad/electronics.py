"""Subassembly 5 — electronics (v3, 2026-09-28): PCB on the 4 standoffs, ESP32 DevKit, LM2596 buck module on 2 floor
bosses between the motors (PCB rev 5, XH cables), 2S 7.4 V pack (AOLIKES 2S1P 18650, 66.3 x 37.1 x 18.5) under the PCB held by an elastic band, fasteners.
No switch, BMS or charger any more: the red JST plug is the switch, the pack charges on its own USB cable.

The printed features (buck bosses, battery stops + elastic hooks, lower axle tower) live in frame.py because they are
part of the body. The PCB goes to Blender as CAD/pcb.glb (KiCad export); here it is only an envelope for the checks.
"""
from build123d import *
from bd_warehouse.fastener import SocketHeadCapScrew, HeatSetNut, HexNut
from lib import *
import frame


def build():
    m3x6 = SocketHeadCapScrew("M3-0.5", 6, "iso4762", simple=True)

    # PCB rev 7: LM2596 on the PCB, 2x M3x10 through module + printed 3 mm spacer + PCB, nut under the PCB; pads soldered with wire stubs
    b = BUCK
    bz = PCB_Z + 1.6 + b["standoff"]
    x0, x1, y0, y1 = b["cx"] - b["L"] / 2, b["cx"] + b["L"] / 2, b["cy"] - b["W"] / 2, b["cy"] + b["W"] / 2
    buck = box(x0, x1, y0, y1, bz, bz + b["t"]) + box(x0 + 2, x1 - 2, y0 + 1, y1 - 1, bz + b["t"], bz + b["H"])   # parts (coil, cap)
    holes = [(b["cx"] - b["hole_dx"] / 2, b["cy"] + b["hole_dy"] / 2), (b["cx"] + b["hole_dx"] / 2, b["cy"] - b["hole_dy"] / 2)]   # KiCad J6/J7: IN hole next to IN+ (y +), OUT hole on the other diagonal (2026-11-07: was mirrored)
    spacer = Compound(children=[cz(x, y, PCB_Z + 1.6, bz, 3.0) - cz(x, y, PCB_Z, bz + 1, 1.75) for x, y in holes])
    m3x10 = SocketHeadCapScrew("M3-0.5", 10, "iso4762", simple=True)
    scr_buck = Compound(children=[Pos(x, y, bz + b["t"]) * m3x10 for x, y in holes])          # head on the module, 6.2 grip, 3.8 out under the PCB
    nut_buck = Compound(children=[Pos(x, y, PCB_Z - 2.4) * HexNut("M3-0.5", "iso4032", simple=True) for x, y in holes])

    bx0, bx1, hw, h = BATT
    battery = box(bx0, bx1, -hw, hw, FLOOR_Z1 - BATT_SEAT, FLOOR_Z1 - BATT_SEAT + h)
    d = DEVKIT
    zk = PCB_Z + 1.6 + 8.5
    devkit = box(d["cx"] - d["W"] / 2, d["cx"] + d["W"] / 2, d["cy"] - d["L"] / 2, d["cy"] + d["L"] / 2, zk, zk + 1.6)
    devkit += box(d["cx"] - 9, d["cx"] + 9, d["cy"] - 12, d["cy"] + 8, zk + 1.6, zk + 4.8)          # ESP-WROOM module

    pcb = box(PCB_X0, PCB_X0 + 100, -35, 35, PCB_Z, PCB_Z + 1.6)                              # envelope, the real board is CAD/pcb.glb
    pcb += box(PCB_X0 + 10, PCB_X0 + 92, -26, 26, PCB_Z - 2, PCB_Z)                                # THT leads, trimmed to 2 mm (inside the standoffs)
    scr_pcb = [Pos(x, y, PCB_Z + 1.6) * m3x6 for x, y in PCB_HOLES]

    return {
        "buck_LM2596": Part(buck, "#1a3a8a", "bought", 1, "LM2596 module 43x21 on the PCB (J6/J7): trimpot to 5.0 V first, then 2x M3x10 + nut, pads soldered with wire stubs"),
        "spacer_buck": Part(spacer, "#e0e0e0", "printed", 2, "ASA black spacer Ø6 x 3, M3 hole: between LM2596 and PCB (plastic, a metal nut would touch IN+)"),
        "screw_M3x10_buck": Part(scr_buck, "#303030", "fastener", 2, "BOLT M3x10 socket head: LM2596 hole -> printed spacer -> PCB"),
        "nut_M3_buck": Part(nut_buck, "#b8bcc2", "fastener", 2, "NUT M3 (ISO 4032) under the PCB, 2.5 mm above the battery"),
        "battery_2S": Part(battery, "#2f5fb3", "bought", 1, "ERYNK 7.4 V 1500 mAh 2S pack (80x41x18.72 measured), JST BEC, in a 3 mm floor pocket + elastic band"),
        "pcb_envelope": Part(pcb, "#1f6b3a", "reference", 1, "PCB 100x70 + 2 mm leads (collision check only)"),
        "devkit_ESP32": Part(devkit, "#202020", "bought", 1, "ESP32 DevKit v1 30-pin (Heemol, have)"),
        "screw_M3x6_pcb": Part(Compound(children=scr_pcb), "#303030", "fastener", 4, "BOLT M3x6 socket head: through the PCB corner hole into the standoff insert (max M3x10)"),
    }
