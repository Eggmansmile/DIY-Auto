"""Print plates per printer: P1S (bed 256 x 256, packed in 245 x 245), A1 mini (bed 180 x 180, packed in 175 x 175) or
H2D (bed 350 x 320, packed in 315 x 310 so each plate fits the area both nozzles reach).
A group that does not fit on one bed is split over several plates (a, b, c ...). Output: CAD/plates/<printer>/.
Parts come from CAD/parts/<subassembly>/print (already print-oriented, on z = 0). Each plate = one 3MF with separate objects, packed with
5 mm gaps. Open the 3MF in Bambu Studio; it keeps the layout (you can still press Arrange).

Run from Scripts/cad/:
    ~/.local/bin/uv run -p 3.12 --with trimesh --with rectpack --with networkx --with lxml python plates.py [p1s|p1s-alles|a1mini|h2d]
P1S = the PLA plates, A1 mini = the TPU plate (+ the TPU 90A filament profile in CAD/plates/a1mini/).
"""
import sys
from pathlib import Path
import trimesh, rectpack

CAD = Path(__file__).resolve().parents[2] / "CAD"
PRINTER = sys.argv[1] if len(sys.argv) > 1 else "p1s"
BED = {"p1s": (245.0, 245.0), "p1s-alles": (245.0, 245.0), "p1s-tpu": (245.0, 245.0), "h2d-herdruk": (315.0, 310.0), "p1s-asa": (245.0, 245.0), "a1mini": (175.0, 175.0), "h2d": (315.0, 310.0), "h2d-v6": (315.0, 310.0), "h2d-v7": (315.0, 310.0), "h2d-v8": (315.0, 310.0), "h2d-v9": (315.0, 310.0)}[PRINTER]
GAP = 5.0
PLATES = {
    "plaat0_PLA_testblok": ["test_fit"],         # print first in every new material: fits for params.py
    "plaat1_PLA_0.4": ["body", "clamp_L", "clamp_R", "knuckle_L", "knuckle_R", "tie_rod_L", "tie_rod_R", "servo_horn", "servo_clamp",
                        "rim_front_L", "rim_front_R"],
    "plaat2_PLA_0.2-nozzle": ["rim_rear_L", "rim_rear_R"],
    "plaat3_TPU": ["tyre_front_L", "tyre_front_R", "tyre_rear_L", "tyre_rear_R"],
}
# printer roles (Ruben 2026-10-01): PLA on the P1S, TPU 90A on the A1 mini (external spool, the P1S has the AMS in the path)
if PRINTER == "p1s":
    PLATES = {k: v for k, v in PLATES.items() if "PLA" in k}
elif PRINTER == "p1s-alles":         # all PLA on one P1S plate (rear rims included, so everything with the 0.2 nozzle)
    PLATES = {"plaat0_PLA_testblok": PLATES["plaat0_PLA_testblok"],
              "plaat1_PLA_alles": PLATES["plaat1_PLA_0.4"] + PLATES["plaat2_PLA_0.2-nozzle"]}
# h2d (2026-10-24): all plates, same split as the P1S (0.4 PLA / 0.2 rear rims / TPU) — no test block (Ruben: common fits)
elif PRINTER == "h2d":
    PLATES = {k: v for k, v in PLATES.items() if k != "plaat0_PLA_testblok"}
elif PRINTER == "h2d-herdruk":       # 2026-11-03: v5 redesign (sturdier parts, one-piece body), black ASA
    PLATES = {"plaat_herdruk_ASA": ["body", "clamp_L", "clamp_R", "knuckle_L", "knuckle_R", "tie_rod_L", "tie_rod_R",
                                     "servo_horn", "servo_clamp"]}   # v5: black ASA, only the redesigned parts (wheels stay)   # black ASA; rear rims stay (gear needs the 0.2 nozzle)
elif PRINTER == "h2d-v6":           # 2026-11-05: 8 mm floor, buck on the PCB, thicker walls: black ASA
    PLATES = {"DIYAuto_v6_ASA_H2D": ["body", "servo_clamp", "spacer_buck"]}
elif PRINTER == "h2d-v7":           # 2026-11-05: measured servo (towers, clamp notch, horn bore 4.78)
    PLATES = {"DIYAuto_v7_ASA_H2D": ["body", "servo_clamp", "servo_horn", "spacer_buck"]}
elif PRINTER == "h2d-v8":           # 2026-11-07: nose as thick as the floor (8 mm), same parts as v7
    PLATES = {"DIYAuto_v8_ASA_H2D": ["body", "clamp_L", "clamp_R", "servo_clamp", "servo_horn", "spacer_buck"]}
elif PRINTER == "h2d-v9":           # 2026-11-10: servo cable slot behind the rear tower, servo fit +0.2 mm
    PLATES = {"DIYAuto_v9_ASA_H2D": ["body", "clamp_L", "clamp_R", "servo_clamp", "servo_horn", "spacer_buck"]}
elif PRINTER == "p1s-asa":           # 2026-11-03: same ASA reprint on the P1S (H2D start failed)
    PLATES = {}
elif PRINTER == "p1s-tpu":           # 2026-11-03: tyres in TPU 95A on the P1S, external spool (not through the AMS)
    PLATES = {k: v for k, v in PLATES.items() if "TPU" in k}
elif PRINTER == "a1mini":            # filament profile next to it: "TPU 90A @BBL A1M (DIY-Auto).json"
    PLATES = {k: v for k, v in PLATES.items() if "TPU" in k}
OUT = CAD / "plates" / PRINTER
OUT.mkdir(parents=True, exist_ok=True)
for plate, names in PLATES.items():
    meshes = {n: trimesh.load(next(CAD.glob(f"parts/*/print/{n}.stl"))) for n in names}
    pk = rectpack.newPacker(rotation=True)
    for n, m in meshes.items():
        ext = m.bounds[1] - m.bounds[0]
        assert min(ext[0], ext[1]) + GAP <= min(BED) and max(ext[0], ext[1]) + GAP <= max(BED), f"{n} is te groot voor {PRINTER}"
        pk.add_rect(ext[0] + GAP, ext[1] + GAP, rid=n)
    for _ in names:
        pk.add_bin(*BED)
    pk.pack()
    placed = pk.rect_list()
    assert len(placed) == len(names), f"{plate}: niet alles geplaatst"
    bins = sorted({r[0] for r in placed})
    for k, bi in enumerate(bins):
        scene = trimesh.Scene()
        for bj, x, y, w, h, n in placed:
            if bj != bi: continue
            m = meshes[n].copy()
            ext = m.bounds[1] - m.bounds[0]
            if abs((ext[0] + GAP) - w) > 1e-6:                    # packer turned it 90°
                m.apply_transform(trimesh.transformations.rotation_matrix(1.5707963, [0, 0, 1]))
            lo = m.bounds[0]
            m.apply_translation([x + GAP / 2 - lo[0] - BED[0] / 2, y + GAP / 2 - lo[1] - BED[1] / 2, -lo[2]])
            scene.add_geometry(m, node_name=n, geom_name=n)
        suffix = "" if len(bins) == 1 else "abcdefgh"[k]
        name = plate.replace("plaat", "plaat" + "", 1).split("_", 1)
        out = OUT / f"{name[0]}{suffix}_{name[1]}.3mf"
        scene.export(out)
        b = scene.bounds
        print(f"{out.name}: {len(scene.geometry)} delen ({', '.join(sorted(scene.geometry))}), {b[1][0]-b[0][0]:.0f} x {b[1][1]-b[0][1]:.0f} mm")
