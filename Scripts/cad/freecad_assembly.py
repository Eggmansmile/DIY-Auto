"""FreeCAD 1.1 assembly with joints, built from the STEP files of assemble.py (+ freecad_export.py for the motors).

Every part sits in world position already, so each joint gets its two connectors (JCS) at the same world
placement on the axis: Detach = True with an explicit Placement, no picking of edges/faces needed.

Rigid groups (App::Part) move as one:  Frame (grounded) · Wheel_rear_L/R · Pinion_L/R · Knuckle_L/R ·
Wheel_front_L/R · Horn · TieRod_L/R.  Joints: revolute wheels/pinions/knuckles/horn, gears pinion↔rim (10:90),
tie rods revolute on the horn and cylindrical on the steering arm (a planar loop with 4 revolutes is redundant).

Run (from the project folder):   freecad Scripts/cad/freecad_assembly.py      (GUI: colours + opens the result)
                          or:    freecadcmd Scripts/cad/freecad_assembly.py   (headless, no colours)
Output: CAD/DIY-Auto.FCStd
"""
import math, sys
from pathlib import Path
import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from params import *                                              # noqa: E402  (plain constants, no build123d)
for _d in (App.getResourceDir(), App.getHomePath(), "/usr/lib/freecad/"):      # Linux package, AppImage and Windows install all differ
    _m = Path(_d) / "Mod" / "Assembly"
    if _m.is_dir():
        sys.path.insert(0, str(_m))
        break
import JointObject                                                # noqa: E402

CAD = HERE.parents[1] / "CAD"
_d = math.hypot(FAX_X, KING_Y)
ARM = (FAX_X - ARM_L * FAX_X / _d, KING_Y - ARM_L * KING_Y / _d)   # same as steering.py

# ---------------------------------------------------------------- parts → groups
SIDED = {  # name: group per side ("{s}" = L/R); everything not listed goes to Frame
    "rim_rear_{s}": "Wheel_rear_{s}", "tyre_rear_{s}": "Wheel_rear_{s}",
    "rim_front_{s}": "Wheel_front_{s}", "tyre_front_{s}": "Wheel_front_{s}",
    "knuckle_{s}": "Knuckle_{s}",
    "tie_rod_{s}": "TieRod_{s}",
}
SPLIT = {  # compound of left + right solids: name → group per side (solid centre y > 0 = L)
    "pinion": "Pinion_{s}", "bearing_MR105_front": "Knuckle_{s}", "axle_bolt_M5x20": "Knuckle_{s}",
    "nut_M5_front": "Knuckle_{s}", "shim_front": "Knuckle_{s}",
}


def group_of(name):
    for s in "LR":
        for pat, g in SIDED.items():
            if name == pat.format(s=s):
                return g.format(s=s)
    return {"servo_horn": "Horn"}.get(name, "Frame")


def hexcol(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


import json                                                       # noqa: E402
manifest = {m["name"]: m for m in json.loads((CAD / "manifest.json").read_text())}
SKIP = {"pcb_envelope"}                                           # clearance volume, not a part

doc = App.newDocument("DIY_Auto")
asm = doc.addObject("Assembly::AssemblyObject", "Assembly")
joints = asm.newObject("Assembly::JointGroup", "Joints")
groups = {}


def grp(name):
    if name not in groups:
        g = doc.addObject("App::Part", name)
        asm.addObject(g)
        groups[name] = g
    return groups[name]


# fasteners become Fasteners Workbench objects (editable ISO/DIN parts), placed on the solids from build123d
sys.path.insert(0, App.getUserAppDataDir() + "Mod/FreeCAD_FastenersWB")
import FastenersCmd                                               # noqa: E402


def fs_type(name):
    if name.startswith(("screw_", "kingpin_", "axle_bolt_")):
        return "ISO4762"
    if name.startswith("nut_"):
        return "ISO4032"                                          # v5: plain nuts only (no locknuts)
    return "IUTHeatInsert" if name.startswith("insert_") else None    # shims (5x7x0.5) are not in the library


def axis_and_end(shape, longest):
    """Axis index (0..2) of an axis-aligned fastener and +1/-1 for the end with the larger cross-section (head, hex)."""
    b = shape.BoundBox
    lo, hi = (b.XMin, b.YMin, b.ZMin), (b.XMax, b.YMax, b.ZMax)
    size = [h - l for l, h in zip(lo, hi)]
    i = size.index(max(size) if longest else min(size))

    def slab(at):
        p0, p1 = list(lo), list(hi)
        p0 = [v - 1 for v in p0]; p1 = [v + 1 for v in p1]
        p0[i], p1[i] = at - 0.15, at + 0.15
        box = Part.makeBox(*(p1[k] - p0[k] for k in range(3)), App.Vector(*p0))
        return shape.common(box).Volume
    return i, (1 if slab(hi[i] - 0.4) >= slab(lo[i] + 0.4) else -1), size[i]


def add_fastener(name, so, typ, gname, colour, how):
    nut = typ in ("DIN985", "ISO4032")                            # nuts: axis = thinnest direction; bolts, inserts: longest
    i, end, length = axis_and_end(so, longest=not nut)
    d = next(m for m in ("M5", "M4", "M3") if m in name)
    f = doc.addObject("Part::FeaturePython", name)
    FastenersCmd.FSScrewObject(f, typ, None)
    f.Diameter = d
    if typ == "ISO4762":
        L = str(round(length - int(d[1])))                        # ISO 4762 head height k = d
        if L in f.getEnumerationsOfProperty("Length"):
            f.Length = L
        else:                                                     # e.g. M5x35 is not in the library table
            f.Length = "Custom"
            f.LengthCustom = float(L)
    doc.recompute()
    _, end_fs, _ = axis_and_end(f.Shape, longest=not nut)          # library parts are built along z
    world = App.Vector(*[end if k == i else 0 for k in range(3)])
    rot = App.Rotation(App.Vector(0, 0, end_fs), world)
    f.Placement = App.Placement(so.BoundBox.Center - rot.multVec(f.Shape.BoundBox.Center), rot)
    f.Label = f"{name} — {how}"
    grp(gname).addObject(f)
    if App.GuiUp:
        FastenersCmd.FSViewProviderTree(f.ViewObject)
        f.ViewObject.ShapeColor = hexcol(colour)
    bb, bt = f.Shape.BoundBox, so.BoundBox                        # check: library part covers the modelled one
    if max(abs(bb.XLength - bt.XLength), abs(bb.YLength - bt.YLength), abs(bb.ZLength - bt.ZLength)) > 1.0:
        print(f"CHECK {name}: library {bb.XLength:.1f}x{bb.YLength:.1f}x{bb.ZLength:.1f} "
              f"vs model {bt.XLength:.1f}x{bt.YLength:.1f}x{bt.ZLength:.1f}")


def add(name, shape, gname, colour, how=""):
    typ = fs_type(name)
    if typ:
        for k, so in enumerate(shape.Solids):
            add_fastener(f"{name}_{k + 1}" if len(shape.Solids) > 1 else name, so, typ, gname, colour, how)
        return
    f = doc.addObject("Part::Feature", name)
    f.Shape = shape
    if how:                                                       # fasteners: the tree says what goes where
        f.Label = f"{name} — {how}"
    grp(gname).addObject(f)
    if App.GuiUp:
        f.ViewObject.ShapeColor = hexcol(colour)


for name, m in manifest.items():
    path = next(CAD.glob(f"parts/*/{name}.step"), None)
    if name in SKIP or path is None:
        print("skip", name)
        continue
    shape = Part.read(str(path))
    how = m["material"] if m["kind"] == "fastener" else ""
    if name in SPLIT:
        for s, keep in (("L", lambda c: c.y > 0), ("R", lambda c: c.y < 0)):
            solids = [so for so in shape.Solids if keep(so.BoundBox.Center)]
            add(f"{name}_{s}", Part.makeCompound(solids), SPLIT[name].format(s=s), m["colour"], how)
    elif name in ("screw_M4_steering", "nut_M4_steering"):      # 3 pivot screws + 2 jam nuts each: 1 in the horn pin, 1 per steering arm
        for so in shape.Solids:
            c = so.BoundBox.Center
            g = "Horn" if abs(c.y) < 3 else ("Knuckle_L" if c.y > 0 else "Knuckle_R")
            add(f"{name[:-9]}_{g}", so, g, m["colour"], how)
    else:
        add(name, shape, group_of(name), m["colour"], how)

# ---------------------------------------------------------------- real motor + real PCB (instead of the stand-ins)
MOTOR_STL = CAD / "ref" / "dc_motor.stl"                          # Ruben's motor model, in metres
MOTOR_Y = CAN_FACE - 15.15                                        # same placement as blender_assembly.py
if MOTOR_STL.exists():
    import Mesh
    for s, sy in (("L", 1), ("R", -1)):
        doc.removeObject(f"motor_{s}") if doc.getObject(f"motor_{s}") else None
        mesh = Mesh.read(str(MOTOR_STL))
        mesh.transform(App.Matrix(1000, 0, 0, 0, 0, 1000, 0, 0, 0, 0, 1000, 0))
        mesh.transform(App.Placement(App.Vector(X_MOT, sy * MOTOR_Y, AXLE_Z),
                                     App.Rotation(App.Vector(0, 0, 1), 180 if sy > 0 else 0)).toMatrix())
        sh = Part.Shape()
        sh.makeShapeFromMesh(mesh.Topology, 0.05)
        add(f"motor_{s}", Part.makeSolid(sh), "Frame", "#c0c4c8")

PCB_STEP = CAD / "parts" / "5 electronics" / "pcb_kicad.step"                                # kicad-cli pcb export step (see note)
if PCB_STEP.exists():
    raw = Part.read(str(PCB_STEP))
    board = max(raw.Solids, key=lambda so: so.BoundBox.XLength * so.BoundBox.YLength)   # the FR4 plate
    rot = App.Placement(App.Vector(), App.Rotation(App.Vector(0, 0, 1), 180))            # motor terminals to the rear
    b = board.transformGeometry(rot.toMatrix()).BoundBox
    plc = App.Placement(App.Vector(PCB_X0 - b.XMin, -(b.YMin + b.YMax) / 2, PCB_Z - b.ZMin), App.Rotation()) * rot
    if App.GuiUp:                                                 # keeps the component colours
        import ImportGui
        before = set(doc.Objects)
        ImportGui.insert(str(PCB_STEP), doc.Name)
        new = [o for o in doc.Objects if o not in before]
        pcb = doc.addObject("App::Part", "PCB")
        for o in new:
            if not [p for p in o.InList if p in new]:
                pcb.addObject(o)
        pcb.Placement = plc
        grp("Frame").addObject(pcb)
    else:
        f = doc.addObject("Part::Feature", "PCB")
        f.Shape = raw
        f.Placement = plc
        grp("Frame").addObject(f)

# ---------------------------------------------------------------- joints
Y = App.Rotation(App.Vector(0, 0, 1), App.Vector(0, 1, 0))       # JCS z-axis along world y
Z = App.Rotation()


def joint(label, jtype, a, b, point, rot, **props):
    j = joints.newObject("App::FeaturePython", label)
    JointObject.Joint(j, JointObject.JointTypes.index(jtype))
    j.Detach1 = j.Detach2 = True
    plc = App.Placement(App.Vector(*point), rot)
    j.Reference1 = [groups[a], ["", ""]]
    j.Reference2 = [groups[b], ["", ""]]
    j.Placement1 = plc
    j.Placement2 = plc
    for k, v in props.items():
        setattr(j, k, v)
    if App.GuiUp:
        JointObject.ViewProviderJoint(j.ViewObject)
    return j


def gears(label, a, b, pa, pb, r1, r2):
    j = joints.newObject("App::FeaturePython", label)
    JointObject.Joint(j, JointObject.JointTypes.index("Gears"))
    j.Detach1 = j.Detach2 = True
    j.Reference1 = [groups[a], ["", ""]]
    j.Reference2 = [groups[b], ["", ""]]
    j.Placement1 = App.Placement(App.Vector(*pa), Y)
    j.Placement2 = App.Placement(App.Vector(*pb), Y)
    j.Distance, j.Distance2 = r1, r2
    if App.GuiUp:
        JointObject.ViewProviderJoint(j.ViewObject)


ground = joints.newObject("App::FeaturePython", "Grounded_Frame")
JointObject.GroundedJoint(ground, groups["Frame"])
if App.GuiUp:
    JointObject.ViewProviderGroundedJoint(ground.ViewObject)

r_pin, r_gear = MOD * Z_PIN / 2, MOD * Z_GEAR / 2                # pitch radii 2.5 / 22.5
for s, sy in (("L", 1), ("R", -1)):
    yw = sy * (RW_Y0 + RW_Y1) / 2
    joint(f"Rev_wheel_rear_{s}", "Revolute", "Frame", f"Wheel_rear_{s}", (0, yw, AXLE_Z), Y)
    joint(f"Rev_pinion_{s}", "Revolute", "Frame", f"Pinion_{s}", (X_MOT, sy * (GY0 + GEAR_W / 2), AXLE_Z), Y)
    gears(f"Gears_{s}", f"Pinion_{s}", f"Wheel_rear_{s}",
          (X_MOT, sy * (GY0 + GEAR_W / 2), AXLE_Z), (0, sy * (GY0 + GEAR_W / 2), AXLE_Z), r_pin, r_gear)
    joint(f"Rev_kingpin_{s}", "Revolute", "Frame", f"Knuckle_{s}", (FAX_X, sy * KING_Y, FAX_Z), Z)
    joint(f"Rev_wheel_front_{s}", "Revolute", f"Knuckle_{s}", f"Wheel_front_{s}",
          (FAX_X, sy * (FW_Y0 + FW_Y1) / 2, FAX_Z), Y)
    joint(f"Rev_tierod_horn_{s}", "Revolute", "Horn", f"TieRod_{s}", (SERVO_OUT + HORN_R, 0, HORN_Z1), Z)  # both rods on 1 pin
    joint(f"Cyl_tierod_arm_{s}", "Cylindrical", f"Knuckle_{s}", f"TieRod_{s}", (ARM[0], sy * ARM[1], HORN_Z1), Z)
joint("Rev_servo_horn", "Revolute", "Frame", "Horn", (SERVO_OUT, 0, HORN_Z1), Z)

doc.recompute()
asm.solve()
doc.recompute()

# ---------------------------------------------------------------- simulations (Assembly → Simulation, press play)
# Gears only couple in a simulation (a static solve ignores them), so driving is shown here. Needs the GUI modules.
if App.GuiUp:
    import CommandCreateSimulation as CS
    import UtilsAssembly

    def simulation(label, t_end, motions):
        sim = UtilsAssembly.getSimulationGroup(asm).newObject("App::FeaturePython", label)
        CS.Simulation(sim)
        CS.ViewProviderSimulation(sim.ViewObject)
        sim.bTimeEnd = t_end
        ms = []
        for jname, formula in motions:
            m = asm.newObject("App::FeaturePython", f"Motion_{jname}")
            CS.Motion(m, "Angular", doc.getObject(jname), formula)
            CS.ViewProviderMotion(m.ViewObject)
            ms.append(m)
        sim.Group = ms
        return sim

    # 1 s: pinions 9 turns → rear wheels 1 turn (angles in rad)
    simulation("Sim_rijden", 1.0, [("Rev_pinion_L", f"{Z_GEAR / Z_PIN}*2*pi*time"),
                                   ("Rev_pinion_R", f"{Z_GEAR / Z_PIN}*2*pi*time")])
    # 2 s: servo horn ±17.5° (sine) → inner wheel 30°, knuckles and front wheels follow through the tie rods
    simulation("Sim_sturen", 2.0, [("Rev_servo_horn", f"{math.radians(17.5):.4f}*sin(pi*time)")])
    doc.recompute()

out = CAD / "DIY-Auto.FCStd"
doc.saveAs(str(out))
print("OK", len(groups), "groups,", len(joints.Group), "joints ->", out)
if App.GuiUp:
    import FreeCADGui as Gui
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
