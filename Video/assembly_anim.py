"""Assembly animation of the DIY-Auto (V1) for the Remotion video. Reads Video/steps.json + CAD/parts/*/*.stl.

Run from the project folder:
    blender --background --python Video/assembly_anim.py -- stills      # 1 frame per step end -> Video/stills/
    blender --background --python Video/assembly_anim.py -- frames      # all frames -> Video/frames/0000.png ...
Workbench engine (fast on the laptop iGPU), studio light, cavity + outline. 1 Blender unit = 1 mm.
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
VID = ROOT / "Video"
sys.path.insert(0, str(ROOT / "Scripts" / "cad"))
from params import PCB_X0, PCB_Z, FAX_X, KING_Y, BEAM_R, BEAM_Z0, BEAM_Z1, SERVO_OUT, SERVO_SHAFT_DX, SERVO   # noqa: E402

SERVO_X = SERVO_OUT - SERVO_SHAFT_DX

MODE = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "stills"
S = json.loads((VID / "steps.json").read_text())
FPS, INTRO, STEP, FLY, OUTRO = S["fps"], S["intro_frames"], S["step_frames"], S["fly_frames"], S["outro_frames"]
N = len(S["steps"])
END = INTRO + N * STEP + OUTRO

COLOURS = [  # name prefix -> RGB
    (("body", "clamp_", "knuckle_", "tie_rod_", "servo_horn", "servo_clamp"), (0.16, 0.17, 0.19)),   # black ASA
    (("rim_",), (0.93, 0.93, 0.91)), (("tyre_",), (0.09, 0.09, 0.10)),
    (("insert_", "pinion"), (0.86, 0.66, 0.22)),
    (("screw_", "axle_bolt_", "kingpin_"), (0.30, 0.31, 0.34)),
    (("nut_", "shim_", "bearing_"), (0.78, 0.80, 0.83)),
    (("motor_",), (0.72, 0.73, 0.76)), (("servo",), (0.13, 0.22, 0.48)),
    (("buck_",), (0.10, 0.28, 0.70)), (("battery_",), (0.20, 0.42, 0.80)),
]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type = "STUDIO", "MATERIAL"
    sh.show_cavity, sh.cavity_type = True, "BOTH"
    sh.show_object_outline = True
    sh.show_specular_highlight = True
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, END - 1
    w = bpy.data.worlds.new("w"); sc.world = w; w.color = (0.90, 0.91, 0.93)
    sc.display_settings.display_device = "sRGB"
    sc.view_settings.view_transform = "Standard"
    return sc


_mats = {}
def material(rgb):
    if rgb not in _mats:
        m = bpy.data.materials.new(str(rgb)); m.diffuse_color = (*rgb, 1); _mats[rgb] = m
    return _mats[rgb]


def colour(name):
    return next((c for pre, c in COLOURS if name.startswith(pre)), (0.6, 0.6, 0.6))


def import_stl(path, name):
    bpy.ops.wm.stl_import(filepath=str(path))
    ob = bpy.context.selected_objects[0]
    ob.name = name
    ob.data.materials.append(material(colour(name)))
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def split_loose(ob):
    """Compound STLs (both sides in one file) -> one object per loose piece, so left and right can fly apart."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
    return list(bpy.context.selected_objects)


def centre(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return (lo + hi) / 2, lo, hi


def load_pcb():
    """Real board from KiCad (glTF, metres, y-up -> Blender z-up): x1000, turned 180° about z (KiCad x runs to the
    rear of the car), board bottom on PCB_Z, board centred on the PCB area. Parented to one empty for the animation."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT / "CAD" / "pcb.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new("pcb", None); bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    root.scale = (1000, 1000, 1000); root.rotation_euler = (0, 0, math.pi)
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == "MESH"]
    board = max(meshes, key=lambda o: (lambda c: (c[2][0] - c[1][0]) * (c[2][1] - c[1][1]))(centre([o])))
    c, lo, hi = centre([board])
    root.location = (PCB_X0 + 50 - c.x, -c.y, PCB_Z - lo.z)
    return root, [root] + new


LM_REF = ROOT / "CAD" / "ref" / "LM2596_module.wrl"   # YAAJ KiCad-Chinese_Modules, no licence: local only (.gitignore)


def load_lm2596(box_ob):
    """Real LM2596 module (KiCad StepUp VRML: flat IndexedFaceSet shapes, 1 unit = 2.54 mm) in place of the CAD box.
    Model x runs IN -> OUT with IN+ at y+, same as the car (IN at low x): only a shift, board bottom on the box bottom.
    Blender 5 has no VRML importer, so the file is parsed here."""
    import re
    verts, faces, mat_idx, mats = [], [], [], []
    for s in re.finditer(r"coordIndex \[([^\]]*)\].*?point \[([^\]]*)\].*?diffuseColor ([\d.]+) ([\d.]+) ([\d.]+)", LM_REF.read_text(), re.S):
        off = len(verts)
        p = [float(v) * 2.54 for v in re.split(r"[\s,]+", s[2].strip()) if v]
        verts += [tuple(p[i:i + 3]) for i in range(0, len(p), 3)]
        rgb = tuple(round(float(s[k]), 3) for k in (3, 4, 5))
        if rgb not in mats:
            mats.append(rgb)
        face = []
        for i in (int(v) for v in re.split(r"[\s,]+", s[1].strip()) if v):
            if i < 0:
                faces.append([off + j for j in face]); mat_idx.append(mats.index(rgb)); face = []
            else:
                face.append(i)
    me = bpy.data.meshes.new("buck_LM2596"); me.from_pydata(verts, [], faces)
    for rgb in mats:
        me.materials.append(material(rgb))
    me.polygons.foreach_set("material_index", mat_idx)
    ob = bpy.data.objects.new("buck_LM2596", me); bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    (mc, _, _), (bc, blo, _) = centre([ob]), centre([box_ob])
    ob.location = (bc.x - mc.x, bc.y - mc.y, blo.z)            # model z 0 = board bottom (pins hang 0.85 below)
    bpy.data.objects.remove(box_ob)
    return ob


def servo_cable():
    """3-wire servo cable as a bevelled curve: out of the servo's front end face low, up through the V-notch in the
    front edge of the floor cutout, then back over the side of the servo clamp towards the PCB."""
    x1, hy = SERVO_X + SERVO[0] / 2, SERVO[1] / 2
    pts = [(x1, 0, 7), (x1 + 0.9, 0, 9), (x1 + 0.9, 0, 21), (x1 + 2.5, 3, 23.5), (SERVO_X + 8, hy + 8, 24),
           (SERVO_X - 14, hy + 8, 24), (SERVO_X - 26, 6, 32), (SERVO_X - 32, 0, 38)]
    cu = bpy.data.curves.new("servo_cable", "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = 0.8, 2
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, (x, y, z) in zip(sp.points, pts):
        p.co = (x, y, z, 1)
    ob = bpy.data.objects.new("servo_cable", cu); bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(material((0.62, 0.30, 0.12)))
    return ob


def beam_highlight():
    """Orange see-through sleeve over both beam ends (round, r BEAM_R around the kingpin): what the knuckle slides onto."""
    obs = []
    for sy in (1, -1):
        bpy.ops.mesh.primitive_cylinder_add(radius=BEAM_R + 0.4, depth=BEAM_Z1 - BEAM_Z0 + 0.8,
                                            location=(FAX_X, sy * KING_Y, (BEAM_Z0 + BEAM_Z1) / 2))
        ob = bpy.context.active_object; ob.name = "beam_hl"
        m = bpy.data.materials.new("hl"); m.diffuse_color = (1.0, 0.45, 0.05, 0.75); ob.data.materials.append(m)
        obs.append(ob)
    return obs


def show_between(objs, f0, f1):
    for o in objs:
        for f, hide in ((0, True), (f0, False), (f1, True)):
            o.hide_render = o.hide_viewport = hide
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)


def ghost(objs, f0, f1, alpha=0.3):
    """Make objs see-through between f0 and f1 (own material copy, alpha keyed; Workbench draws it transparent)."""
    for o in objs:
        m = o.data.materials[0].copy(); o.data.materials[0] = m
        for f, a in ((0, 1.0), (f0, 1.0), (f0 + 10, alpha), (f1 - 10, alpha), (f1, 1.0)):
            m.diffuse_color[3] = a; m.keyframe_insert("diffuse_color", index=3, frame=f)


def show_from(objs, frame):
    for o in objs:
        for f, hide in ((0, True), (frame, False)):
            o.hide_render = o.hide_viewport = hide
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)


def fly(o, direction, dist, f0):
    base = o.location.copy()
    c = centre([o])[0]
    d = {"up": Vector((0, 0, 1)), "down": Vector((0, 0, -1)),
         "out": Vector((0, 1 if c.y >= 0 else -1, 0)), "in": Vector((0, -1 if c.y >= 0 else 1, 0))}[direction]
    o.location = base + d * dist; o.keyframe_insert("location", frame=f0)
    o.location = base; o.keyframe_insert("location", frame=f0 + FLY)


def cam_pos(c):
    t = Vector(c["target"]); az, el = math.radians(c["az"]), math.radians(c["el"])
    return t + 1.3 * c["dist"] * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))), t


def main():
    sc = reset()
    parts = {}
    for stl in sorted((ROOT / "CAD" / "parts").glob("*/*.stl")):
        if stl.stem in ("pcb_envelope", "devkit_ESP32", "test_fit"):
            continue
        parts[stl.stem] = [import_stl(stl, stl.stem)]
    for s in "LR":
        parts[f"motor_{s}"] = [import_stl(VID / "assets" / f"motor_{s}.stl", f"motor_{s}")]
    if LM_REF.exists():
        parts["buck_LM2596"] = [load_lm2596(parts.pop("buck_LM2596")[0])]
    root, pcb_objs = load_pcb()
    parts["pcb"] = pcb_objs
    parts["servo_cable"] = [servo_cable()]
    hl = beam_highlight()
    for name, obs in list(parts.items()):
        if name.startswith(("insert_", "screw_", "nut_", "shim_", "bearing_", "axle_bolt_", "kingpin_", "pinion")):
            parts[name] = split_loose(obs[0])

    # timeline: body from the start, every step's parts appear and fly in, staggered per group
    timeline = []
    for i, st in enumerate(S["steps"]):
        f = INTRO + i * STEP
        timeline.append(f)
        for k, (name, direction, dist) in enumerate(st["parts"]):
            obs = parts[name]
            f0 = f + 14 + 7 * k
            show_from(obs, f0)
            movers = [root] if name == "pcb" else obs
            for o in movers:
                fly(o, direction, dist, f0)
        if st.get("highlight") == "beam":
            show_between(hl, f, f + STEP)
        for name in st.get("ghost", []):
            ghost(parts[name], f + 50, f + STEP)
    for o in bpy.data.objects:                      # constant visibility, eased motion
        if o.animation_data and o.animation_data.action:
            for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT" if fc.data_path.startswith("hide") else "BEZIER"

    # camera on a target empty
    tgt = bpy.data.objects.new("target", None); sc.collection.objects.link(tgt)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens, cam.data.clip_start, cam.data.clip_end = 50, 1, 5000
    cam.data.shift_x = -0.17                        # car right of centre: the Remotion text panel sits on the left
    tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis, tc.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    def cam_key(c, frame):
        p, t = cam_pos(c); cam.location = p; tgt.location = t
        cam.keyframe_insert("location", frame=frame); tgt.keyframe_insert("location", frame=frame)
    ov = S["overview_cam"]
    cam_key({**ov, "az": ov["az"] - 70}, 0); cam_key(ov, INTRO - 10)
    for i, st in enumerate(S["steps"]):
        f = INTRO + i * STEP
        cam_key(S["steps"][i - 1]["cam"] if i else ov, f); cam_key(st["cam"], f + 26)
    last = INTRO + N * STEP
    cam_key(S["steps"][-1]["cam"], last)
    for k in range(5):                              # outro: one slow turn around the car
        cam_key({**ov, "az": ov["az"] + 90 * k}, last + 20 + int(k * (OUTRO - 25) / 4))

    (VID / "frames.json").write_text(json.dumps({"fps": FPS, "frames": END, "intro": INTRO, "step_starts": timeline,
                                                 "outro": last}, indent=1))
    if MODE == "stills":
        out = VID / "stills"; out.mkdir(exist_ok=True)
        for i, f in enumerate(timeline):
            sc.frame_set(f + STEP - 4); sc.render.filepath = str(out / f"step_{i + 1:02d}.png")
            bpy.ops.render.render(write_still=True)
        sc.frame_set(last + 60); sc.render.filepath = str(out / "outro.png"); bpy.ops.render.render(write_still=True)
    else:
        out = VID / "frames"; out.mkdir(exist_ok=True)
        sc.render.filepath = str(out / "####"); sc.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(animation=True)


main()
