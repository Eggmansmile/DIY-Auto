"""Routes KiCad/DIY-Auto.kicad_pcb after gen_pcb.py: GND planes on both layers, Freerouting (autorouter), zone fill.

Run (from the project folder, system Python because it has pcbnew; Freerouting jar in ~/.local/share/freerouting):
    python3 Scripts/gen_pcb.py
    python3 Scripts/route_pcb.py
    kicad-cli pcb drc --schematic-parity KiCad/DIY-Auto.kicad_pcb
Net classes (Motor 1.2 mm, Voeding 1.0 mm, Default 0.3 mm, clearance 0.2) live in KiCad/DIY-Auto.kicad_pro.
"""
import subprocess, tempfile
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "KiCad" / "DIY-Auto.kicad_pcb"
JAR = Path.home() / ".local/share/freerouting/freerouting.jar"
O, W, H = (100.0, 100.0), 100.0, 70.0


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(O[0] + x), pcbnew.FromMM(O[1] + y))


b = pcbnew.LoadBoard(str(PCB))
b.SynchronizeNetsAndNetClasses(True)
gnd = b.FindNet("GND")
for z in list(b.Zones()):
    b.Remove(z)
for layer, name in ((pcbnew.B_Cu, "GND_B"), (pcbnew.F_Cu, "GND_F")):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNet(gnd); z.SetZoneName(name)
    z.SetLocalClearance(pcbnew.FromMM(0.35)); z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetThermalReliefGap(pcbnew.FromMM(0.35)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.7))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)):
        ol.Append(mm(x, y))
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())

with tempfile.TemporaryDirectory() as tmp:
    dsn, ses = Path(tmp) / "board.dsn", Path(tmp) / "board.ses"
    assert pcbnew.ExportSpecctraDSN(b, str(dsn))
    subprocess.run(["java", "-Djava.awt.headless=true", "-jar", str(JAR), "-de", str(dsn), "-do", str(ses),
                    "-mp", "80", "--gui.enabled=false"], check=True, capture_output=True)
    assert pcbnew.ImportSpecctraSES(b, str(ses))

# GND pads where tracks box in the copper (starved thermal spokes): solid instead. Signal GND only, <0.5 A
SOLID = {("J3", "14"), ("J8", "8"), ("J9", "8")}
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if (fp.GetReference(), pad.GetNumber()) in SOLID:
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(PCB))
print("OK: gerouteerd ->", PCB.name)
