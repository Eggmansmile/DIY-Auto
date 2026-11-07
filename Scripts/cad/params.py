"""All DIY-Auto dimensions in one place. Imported by the subassembly scripts in Scripts/cad/ and by gen_drawing.py.

Car coordinates in mm: x forward (0 = rear axle), y to the left, z up (0 = ground).
"""
AXLE_Z = 35.0                       # rear axle height = rear wheel radius
RW_R, RIM_R, RW_Y0, RW_Y1 = 35.0, 29.0, 52.0, 72.0
FAX_X, FAX_Z = 150.0, 20.0          # front axle
FW_R, FRIM_R, FW_Y0, FW_Y1 = 20.0, 15.0, 34.0, 46.0
MOD, Z_PIN, Z_GEAR, GEAR_W = 0.5, 10, 90, 5.0      # 2026-09-28: pinion measured Ø5.88 -> m0.5 (the STL's 7.2 was wrong); 9:1
BACKLASH = 0.30                     # removed from the tooth thickness at the pitch circle (≈0.13 mm flank gap)
GY0 = RW_Y0 - GEAR_W                # gear plane 47..52
X_MOT = -MOD * (Z_PIN + Z_GEAR) / 2 # -25
CAN_W, CAN_H, CAN_L = 24.0, 18.3, 30.3          # from Ruben's motor STL (was 28.4)
CAN_FACE = GY0 - 2.6                # 44.4: shaft sticks out 7.6, so the pinion (5 wide) is face+2.6 .. face+7.6
WALL_Y1 = CAN_FACE + 2.0            # 46.4: gear plate 2.0 (boss 1.9 sits in it), 0.6 mm free to rim and pinion
FLOOR_Z0, FLOOR_Z1 = 10.0, 18.0     # 2026-11-05: floor 3 -> 8 mm (upward, ground clearance stays 10): 3 mm flexed
NOSE_Z1, NOSE_X0 = 18.0, 100.0      # nose (x > 100) as thick as the floor (8 mm, z 10..18); the steering beam (z 15..25) sits partly inside it
CLAMP_X0, CLAMP_X1, CLAMP_SPLIT, CLAMP_TOP = -44.0, -4.0, 42.0, 50.0
BEARING_D, BEARING_W = 10.0, 4.0    # MR105: 5 x 10 x 4
# fits for FDM/PETG (2026-09-30): printed holes come out 0.2-0.4 mm small (GrandpaCAD), so holes get that back.
# Sources + reasoning: Engineering/3D printing/Passingen en toleranties.md
AXLE_PRESS, AXLE_FREE, M3_FREE = 5.1, 5.4, 3.5   # printed Ø5 axle: press / turns free; M3 through (ISO 273 normal 3.4 + FDM)
M2_INSERT, M3_INSERT = 3.2, 4.2                   # CNC Kitchen: M2 D2 3.2; Hilitchi M3 OD 5.0 -> 4.2 (between CNC Kitchen 4.0 for D1 4.6 and 4.4 for D1 5.0)
BATT = (13.0, 93.0, 20.5, 18.72)  # ERYNK 2S 1500 mAh measured 2026-11-05: 80 x 41 x 18.72, centred on x = 53
BATT_SEAT = 3.0                     # sunk 3 mm into the 8 mm floor (5 mm stays): 4.3 mm free under the PCB leads for the elastic band
# was  # x0, x1, half width, height: AOLIKES 2S1P 2600 mAh 18650 pack, 66.3 x 37.1 x 18.5 (listing photo), centred on x = 53 as before
PCB_X0, PCB_Z = 5.0, 40.0          # v5 (2026-11-04): 3 mm forward so the rear standoffs clear an M5x40 rear axle bolt
PCB_HOLES = [(PCB_X0 + 3.5, 31.5), (PCB_X0 + 3.5, -31.5), (PCB_X0 + 96.5, 31.5), (PCB_X0 + 96.5, -31.5)]
HALF_OUTLINE = [(-46, WALL_Y1), (40, WALL_Y1), (48, 37.5), (112, 37.5), (124, 16), (141, 16), (141, 13.5), (165.0, 13.5)]   # v5: 37.5 so the Ø10 front standoffs stay on the floor   # v3: nose ends at 165 (no charger pocket)

# steering: C-hub knuckles on an M3 kingpin, servo upside down with its long side across the car
KING_Y = 20.5                       # kingpin
BEAM_R, BEAM_Z0, BEAM_Z1 = 4.6, 15.0, 25.0            # beam end: round around the kingpin, z 15..25
PLATE_Y0, PLATE_Y1 = KING_Y + BEAM_R + 0.5, 32.5     # knuckle side plate, holds the front axle (v5: 6.9 thick, spacer 1.5)
LUG_T, GAP = 4.0, 0.4
ARM_L = 10.0
ARM_Z0, ARM_Z1 = BEAM_Z1 + GAP, BEAM_Z1 + GAP + LUG_T   # 25.4..28.4: steering arm in the plane of the upper lug (servo upright,
                                    # 2026-10-01); a boss on the arm end carries the tie rod up to HORN_Z1
LOCK = 30.0                         # checked for collisions at ±LOCK
# servo SpringRC SM-S2309S: dimensions from the GlenSearle servo-s2309s.scad model (GitHub), spline Ø from Ruben (2026-11-05)
SERVO = (23.0, 12.3, 22.0)          # body length (x), thickness (y), body height: GlenSearle servo-s2309s.scad (GitHub), chosen by Ruben 2026-11-05
SERVO_SHAFT_DX = 6.5                # shaft 5.0 from the near body end (GitHub model AxleOffset; Ruben's caliper agrees)
# was 5.55              # drawings: 4.6 (SpringRC, scaled) .. 5.7 (SG90); check_all: steering stays 29.6..31.4° / 26.4°, no hits
SERVO_BOSS_Z, SERVO_BOSS_D = 25.5, 12.3   # GitHub model: round top Ø12.3, 10 above the tab underside
SERVO_SPLINE_Z, SERVO_SPLINE_D = 29.5, 4.76   # spline top: GitHub model (14 above the tab underside); Ø: Ruben's caliper (horn press fit, the model's 4.9 is a clearance)
SERVO_TAB = dict(span=31.8, t=2.3, from_base=15.5,   # GitHub model: flange 31.8 x 2.3, 15.5 above the base
                  hole_dx=13.9, hole_d=1.7)   # tab holes M2: not used (the bars clamp the tabs), only drawn
SERVO_OUT = 124.9                   # output shaft x (v3b: 6 mm back so the forward horn arm reaches the arm ends; rear post just inside the chassis)
SERVO_X = SERVO_OUT - SERVO_SHAFT_DX
HORN_Z1 = 36.0                      # servo UPRIGHT (2026-10-01): horn top face = tie rod plane, horn 1.5 thick below it on the
                                    # shaft; the body hangs through a cutout in the nose floor, base at 5.3 above the ground
                                    # (upside down it could not be assembled: horn trapped between floor and bridge)
PLATE_HW = 7.5                      # knuckle side plate half length in x (v5: 3.4 mm wall around the M5 nut pocket)
HORN_R = 15.2                       # design value (printed horn): single-arm horn pointing forward, hole at x = SERVO_OUT + HORN_R ≈ arm ends (140.1):
                                    # both tie rods on this one pin run almost parallel to the axle (the ±y cross horn locked up at 8°)
KINGPIN = ("M4-0.7", 30)            # v5: ISO 4762 M4x30, head DOWN, 2 jammed plain M4 nuts on top (no locknuts): lugs 10.6..29.4 + 6.4 nuts + 1 = 26.2; old: M3x25 + nylock, lugs 11.6..28.4 leave 8.2 mm past the lug,
                                    # enough for the 4 mm nylock (M3x20 left 3.2 and missed the nylon ring); the end points up, clear of the ground

# fasteners (bd_warehouse): Hilitchi heat-set inserts, ISO 4762 socket head screws, ISO 4032 plain nuts (Ruben has no locknuts)
INSERT_M2 = ("M2-0.4-6", "Hilitchi")    # OD 3.5, length 6
INSERT_M3 = ("M3-0.5-6", "Hilitchi")    # OD 5.0, length 6

# frame (subassembly 1, v2 after Ruben's "smaller blocks" feedback): saddles + gear plate + strap clamp
TOWER = (-6.5, 8.0, 35.0)           # rear axle tower x0, x1, y0 (to WALL_Y1, z FLOOR_Z1..CLAMP_SPLIT); x0 -5 -> -6.5 for the nut slot wall
STANDOFF_R = 5.0                    # PCB standoff; 4.5 would touch the floor edge tangentially (non-manifold)
CRADLE_Y0 = CAN_FACE - CAN_L - 2    # 13.0: back stop behind the can
SPLIT = AXLE_Z                      # clamp split at the motor axis
MOUNT_WALL = 3.0                    # saddle / strap wall around the can pocket (pocket = can + 0.2)
EAR_X, EAR_R, EAR_T = 17.5, 5.0, 4.5  # ears at X_MOT ± EAR_X, strap ear thickness; r 4.0 = 1.9 wall around the M3 insert (2026-10-24: no M2)
EAR_Y = (17.0, 29.8)                # rear pair on the rear saddle, front pair just behind the axle tower
SADDLES = [(CRADLE_Y0 + 2, 21.0), (27.0, CAN_FACE)]
GEAR_PLATE_X0 = -40.0               # gear plate from here into the axle tower, y CAN_FACE..WALL_Y1
CLAMP_PRELOAD = 0.2                 # strap pocket 0.2 lower than the can flat: screws press the motor down
STRAP_SLOTS = [(25.0, 40.0), (65.0, 80.0)]   # x ranges, y 31..34 each side

# rear drive (subassembly 2)
SEAT_D = 10.15                      # MR105 press seat: 10.0 was nearly impossible to press (Ruben 2026-09-30); +0.15 gives ~0.1-0.2 interference after FDM undersize
RACE_R = 3.25                       # spacers touch only the bearing inner race (race OD ≈ 6.6)
RIM_LIP, TYRE_FIT = 0.8, 0.3        # lips on the rim edges, tyre 0.3 mm undersize on the rim
AXLE_FLAT = 0.4                     # printed axles: flat on the underside to print lying down
# wheel axles = M5 bolts (2026-10-01, after comparing with other printed RC cars: steel, not printed PLA)
# stack: bolt head -> shim 5x7x0.5 (inner race only) -> MR105 -> rim -> MR105 -> race collar (tower / knuckle) -> nut
SHIM = (5.3, 7.0, 0.5)              # stainless shim washer ID, OD, thickness
AXLE_BOLT_REAR = ("M5-0.8", 40)     # v5: ISO 4762 M5x40 (Ruben has 30/40): end 7.5 mm past the plain nut, 2.5 mm out of the tower
AXLE_BOLT_FRONT = ("M5-0.8", 20)    # ISO 4762 M5x20: a nylock would hit the beam end, so a plain nut in a pocket + threadlocker
NUT_M5 = dict(af=8.0, h_nyl=5.0, h=4.0, gap=0.2)   # DIN 985 / DIN 934 M5: across flats, heights; gap = pocket clearance
REAR_NUT_Y0 = 38.2                  # nut slot in the tower (sized for a nylock, a plain nut fits): y 39.0 .. 44.2, dropped in from the top (open under the PCB)
FRONT_NUT_Y1 = 30.4                 # nut pocket in the knuckle plate: 4.8 deep (ISO 4032 M5 = 4.7), 2.1 mm wall behind it

# electronics (subassembly 5)
TOWER_TOP = PCB_Z - 0.5             # PCB edge runs 0.5 mm over the rear axle tower
BUCK = dict(L=43.2, W=21.0, H=14.0, t=1.6, cx=41.4, cy=21.5, standoff=3.0, hole_dx=29.97, hole_dy=16.0)   # 2026-11-05: LM2596 ON THE PCB (KiCad J6/J7, centre 163.6/156.5 -> car), printed 3 mm spacers; holes from the Handsontec drawing
SW_PLATE = dict(x0=-46.0, t=2.5, half_w=12.5, cut_w=19.0, cut_h=13.0, zc=38.0)    # KCD11 rocker, snap-in 19 x 13
DEVKIT = dict(cx=PCB_X0 + 73.3, cy=10.2, L=51.5, W=28.0)   # ESP32 DevKit on 8.5 mm sockets (from the KiCad placement)
BATT_STOP = dict(gap=0.4, wall=3.0, h=8.0, notch=14.0)   # end walls with a 14 mm notch for the leads
HOOK = dict(t=4.0, w=8.0, top=29.5, tip=2.0, x=(26.0, 80.0))   # elastic band hooks each side, tip outward (45° underside);
                                    # top 2 mm under the pack top (31.5), so the elastic presses the pack down


# v5 (2026-11-04, Ruben: parts too thin): design rules checked in check_all.py
M4_FREE = 4.5                       # M4 through (kingpins, steering pivots)
MIN_WALL, INSERT_WALL = 3.0, 2.5    # load paths / solid plastic around a heat insert
