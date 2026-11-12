exec(open('/tmp/scgen/gen.py').read())
par("R_POCKET","CAN_W / 2 + 0.2"); par("R_OUT","R_POCKET + MOUNT_WALL")
cylY("Strap shell","X_MOT","CRADLE_Y0 + 2.2","CAN_FACE - 0.2","AXLE_Z","R_OUT",op="new",bn="clamp_L")
box("Strap top flat","X_MOT - 20","X_MOT + 20","0","60","SPLIT","AXLE_Z + CAN_H/2 + MOUNT_WALL",op="intersect",tgt="clamp_L")
for i,ey in enumerate(("EAR_Y_0","EAR_Y_1")):
    box(f"Ear bar {i+1}","X_MOT - EAR_X","X_MOT + EAR_X",f"{ey} - EAR_R",f"{ey} + EAR_R","SPLIT","SPLIT + EAR_T",tgt="clamp_L")
    for s,sg in (("A","-"),("B","+")):
        cylZ(f"Ear round {i+1}{s}",f"X_MOT {sg} EAR_X",ey,"SPLIT","SPLIT + EAR_T","EAR_R",tgt="clamp_L")
pocket("Strap pocket","AXLE_Z + CAN_H/2 - CLAMP_PRELOAD","clamp_L")
for i,ey in enumerate(("EAR_Y_0","EAR_Y_1")):
    for s,sg in (("A","-"),("B","+")):
        cylZ(f"Strap bolt hole {i+1}{s}",f"X_MOT {sg} EAR_X",ey,"SPLIT - 1","SPLIT + EAR_T + 1","1.7",op="cut",tgt="clamp_L")
        cylZ(f"Strap bolt head seat {i+1}{s}",f"X_MOT {sg} EAR_X",ey,"SPLIT + EAR_T - 3","SPLIT + EAR_T + 1","3.05",op="cut",tgt="clamp_L")
add("solid.mirror",bodies=["clamp_L"],plane="XZ",name="Mirror clamp")
add("body.rename",body="clamp_L (2)",name="clamp_R")
json.dump({"commands":C},open(OUT+"clamp.json","w"),indent=1)
