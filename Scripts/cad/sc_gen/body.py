exec(open('/tmp/scgen/gen.py').read())
par("R_POCKET","CAN_W / 2 + 0.2"); par("R_OUT","R_POCKET + MOUNT_WALL")
par("Z_LO","FLOOR_Z1 - 0.01")
par("YO","BATT_2 + BATT_STOP_gap + BATT_STOP_wall")
par("SERVO_Z0","HORN_Z1 - 1.5 - SERVO_SPLINE_Z"); par("TAB_Z0","SERVO_Z0 + SERVO_TAB_from_base"); par("TAB_Z1","TAB_Z0 + SERVO_TAB_t")
par("C_X0","SERVO_0 / 2 + 0.6 + 0.05"); par("C_XS","7.5"); par("C_X1","16.7"); par("C_HW","16.4")
par("C_SIDE","SERVO_1 / 2 + 0.6 + 0.05"); par("C_SLOT","SERVO_1 / 2 + 0.5"); par("C_BX","12.1"); par("C_BY","11.6")
par("CHAM_C","C_BX + C_BY + (M3_INSERT / 2 + INSERT_WALL) * 1.4142136")
# --- floor
y=["WALL_Y1"]; W="WALL_Y1"
half=[(-46,W),(40,W),(48,37.5),(112,37.5),(124,16),(141,16),(141,13.5),(165,13.5)]
pts=[[a,b] for a,b in half]+[[a,f"-({b})" if isinstance(b,str) else -b] for a,b in reversed(half)]
poly("Floor sketch","XY",pts,off="FLOOR_Z0")
add("solid.extrude",distance="FLOOR_Z1 - FLOOR_Z0",operation="new",name="Floor",body_name="body")
# --- right half (y > 0), built as its own body, mirrored below
S="Side"
box("Gear plate","GEAR_PLATE_X0","TOWER_0 + 0.1","CAN_FACE","WALL_Y1","Z_LO","AXLE_Z + 10",op="new",bn=S)
for i,(y0,y1) in enumerate((("CRADLE_Y0 + 2","21.0"),("27.0","CAN_FACE"))):
    box(f"Motor saddle {i+1}","X_MOT - R_OUT","X_MOT + R_OUT",y0,f"{y1} + 0.01","Z_LO","SPLIT",tgt=S)
box("Back stop","X_MOT - R_OUT","X_MOT + R_OUT","CRADLE_Y0","CRADLE_Y0 + 2.01","Z_LO","29.0",tgt=S)
for i,ey in enumerate(("EAR_Y_0","EAR_Y_1")):
    box(f"Ear bar {i+1}","X_MOT - EAR_X","X_MOT + EAR_X",f"{ey} - EAR_R",f"{ey} + EAR_R","Z_LO","SPLIT",tgt=S)
    for s,sg in (("A","-"),("B","+")):
        cylZ(f"Ear round {i+1}{s}",f"X_MOT {sg} EAR_X",ey,"Z_LO","SPLIT","EAR_R",tgt=S)
pocket("Motor pocket","AXLE_Z + CAN_H/2",S)
cylY("Bearing boss","X_MOT","CAN_FACE - 1","WALL_Y1 + 1","AXLE_Z","3.6",op="cut",tgt=S)
box("Axle tower","TOWER_0","TOWER_1","TOWER_2","WALL_Y1","Z_LO","TOWER_TOP",tgt=S)
box("Nut slot","-NUT_M5_af/2 - NUT_M5_gap","NUT_M5_af/2 + NUT_M5_gap","REAR_NUT_Y0 - NUT_M5_gap","REAR_NUT_Y0 + NUT_M5_h_nyl + NUT_M5_gap",
    "AXLE_Z - NUT_M5_af / 1.7320508 - NUT_M5_gap","TOWER_TOP + 1",op="cut",tgt=S)
cylY("Race collar","0","WALL_Y1 - 0.01","GY0","AXLE_Z","RACE_R",tgt=S)
cylY("Axle bolt hole","0","TOWER_2 - 1","GY0 + 1","AXLE_Z","AXLE_PRESS / 2",op="cut",tgt=S)
for i,x in enumerate(("PCB_X0 + 3.5","PCB_X0 + 96.5")):
    cylZ(f"PCB standoff {i+1}",x,"31.5","Z_LO","PCB_Z","STANDOFF_R",tgt=S)
    cylZ(f"PCB insert hole {i+1}",x,"31.5","PCB_Z - 9","PCB_Z + 1","M3_INSERT / 2",op="cut",tgt=S)
for i,ey in enumerate(("EAR_Y_0","EAR_Y_1")):
    for s,sg in (("A","-"),("B","+")):
        cylZ(f"Ear insert hole {i+1}{s}",f"X_MOT {sg} EAR_X",ey,"SPLIT - 7","SPLIT + 1","M3_INSERT / 2",op="cut",tgt=S)
for i,(xa,xb) in enumerate((("BATT_0 - BATT_STOP_gap - BATT_STOP_wall","BATT_0 + 10"),("BATT_1 - 10","BATT_1 + BATT_STOP_gap + BATT_STOP_wall"))):
    box(f"Battery leg {i+1}",xa,xb,"BATT_2 + BATT_STOP_gap","YO","Z_LO","FLOOR_Z1 + BATT_STOP_h",tgt=S)
a="YO + 1"; t="HOOK_t"; tip="HOOK_tip"; top="HOOK_top"
poly("Hook sketch","YZ",[[a,"Z_LO"],[f"{a} + {t}","Z_LO"],[f"{a} + {t}",f"{top} - 2.5 - {tip}"],[f"{a} + {t} + {tip}",f"{top} - 2.5"],
     [f"{a} + {t} + {tip}",top],[a,top]],off="HOOK_x_0 - HOOK_w / 2")
add("solid.extrude",distance="HOOK_w",operation="join",targets=[S],name="Band hook")
add("solid.pattern.rectangular",features=["Band hook"],dir1=[1,0,0],count1=2,spacing1="HOOK_x_1 - HOOK_x_0",name="Band hooks")
box("Gear plate rib","GEAR_PLATE_X0 - 3.5","GEAR_PLATE_X0 + 0.01","36.0","WALL_Y1","Z_LO","AXLE_Z + 10",tgt=S)
for nm,xa,xb in (("rear","SERVO_X - C_X1","SERVO_X - C_X0"),("front","SERVO_X + C_X0","SERVO_X + C_X1")):
    box(f"Servo tab bar {nm}",xa,xb,"C_SLOT","C_HW","TAB_Z0 - 0.01","TAB_Z1 - 0.2",tgt=S)
for nm,xa,xb in (("rear","SERVO_X - C_X1","SERVO_X - C_XS"),("front","SERVO_X + C_XS","SERVO_X + C_X1")):
    box(f"Servo side block {nm}",xa,xb,"C_SIDE","C_HW","NOSE_Z1 - 0.01","TAB_Z1 - 0.2",tgt=S)
add("solid.mirror",bodies=[S],plane="XZ",name="Mirror side")
add("solid.combine",target="body",tools=[S,"Side (2)"],operation="join",touching="one_body")
# --- full-width parts
for i,(xa,xb) in enumerate((("BATT_0 - BATT_STOP_gap - BATT_STOP_wall","BATT_0 - BATT_STOP_gap"),("BATT_1 + BATT_STOP_gap","BATT_1 + BATT_STOP_gap + BATT_STOP_wall"))):
    box(f"Battery end wall {i+1}",xa,xb,"-YO","YO","Z_LO","FLOOR_Z1 + BATT_STOP_h",tgt="body")
    box(f"Lead notch {i+1}",f"({xa}) - 1",f"({xb}) + 1","-BATT_STOP_notch / 2","BATT_STOP_notch / 2","FLOOR_Z1","FLOOR_Z1 + BATT_STOP_h + 1",op="cut",tgt="body")
for nm,xa,xb in (("rear","SERVO_X - C_X1","SERVO_X - C_X0"),("front","SERVO_X + C_X0","SERVO_X + C_X1")):
    box(f"Servo tower {nm}",xa,xb,"-C_HW","C_HW","NOSE_Z1 - 0.01","TAB_Z0",tgt="body")
h="21.2132034"; cx="SERVO_X + CHAM_C / 2 + 10.6"
for nm,sg in (("R",""),("L","-")):
    cy_=f"{sg}(CHAM_C / 2 + 10.6)"
    poly(f"Tower relief {nm} sketch","XY",[[f"{cx} - {h}",cy_],[cx,f"{cy_} - {h}"],[f"{cx} + {h}",cy_],[cx,f"{cy_} + {h}"]],off="-5")
    add("solid.extrude",distance="60",operation="cut",targets=["body"],name=f"Tower relief {nm}")
box("Steering beam","FAX_X - BEAM_R","FAX_X + BEAM_R","-KING_Y","KING_Y","BEAM_Z0","BEAM_Z1",tgt="body")
for nm,sg in (("R",""),("L","-")):
    cylZ(f"Beam end {nm}","FAX_X",f"{sg}KING_Y","BEAM_Z0","BEAM_Z1","BEAM_R",tgt="body")
    cylZ(f"Kingpin hole {nm}","FAX_X",f"{sg}KING_Y","BEAM_Z0 - 1","BEAM_Z1 + 1","M4_FREE / 2",op="cut",tgt="body")
for i,sx in enumerate(("-","+")):
    for j,sy in enumerate(("-","")):
        cylZ(f"Servo insert hole {i}{j}",f"SERVO_X {sx} C_BX",f"{sy}C_BY","TAB_Z1 - 0.2 - 7","TAB_Z1","M3_INSERT / 2",op="cut",tgt="body")
box("Servo cutout","SERVO_X - SERVO_0 / 2 - 0.6","SERVO_X + SERVO_0 / 2 + 0.6","-SERVO_1 / 2 - 0.6","SERVO_1 / 2 + 0.6","FLOOR_Z0 - 1","NOSE_Z1 + 0.5",op="cut",tgt="body")
xe="SERVO_X + SERVO_0 / 2 + 0.6 - 0.01"
poly("Cable notch sketch","XY",[[xe,-3],[f"{xe} + 3",0],[xe,3]],off="FLOOR_Z0 - 1")
add("solid.extrude",distance="TAB_Z0 + 0.01 - (FLOOR_Z0 - 1)",operation="cut",targets=["body"],name="Cable notch")
box("Battery pocket","BATT_0 - BATT_STOP_gap","BATT_1 + BATT_STOP_gap","-BATT_2 - BATT_STOP_gap","BATT_2 + BATT_STOP_gap","FLOOR_Z1 - BATT_SEAT","FLOOR_Z1 + 1",op="cut",tgt="body")
json.dump({"commands":C},open(OUT+"body.json","w"),indent=1)
