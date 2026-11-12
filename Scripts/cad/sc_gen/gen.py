import json,sys
OUT="CAD/solidcraft/scripts/"
C=[]
def add(cmd,**p): C.append({"command":cmd,"params":p})
def par(n,e): add("parameters.add",name=n,expression=e)
def box(name,x0,x1,y0,y1,z0,z1,op="join",tgt=None,bn=None):
    p=dict(length=f"({x1}) - ({x0})",width=f"({y1}) - ({y0})",height=f"({z1}) - ({z0})",corner=[str(x0),str(y0),str(z0)],operation=op,name=name)
    if tgt: p["targets"]=[tgt]
    if bn: p["body_name"]=bn
    add("solid.box",**p)
def cylY(name,x,y0,y1,z,r,op="join",tgt=None,bn=None):
    p=dict(radius=str(r),height=f"({y1}) - ({y0})",base=[str(x),str(y0),str(z)],axis="Y",operation=op,name=name)
    if tgt: p["targets"]=[tgt]
    if bn: p["body_name"]=bn
    add("solid.cylinder",**p)
def cylZ(name,x,y,z0,z1,r,op="join",tgt=None,bn=None):
    p=dict(radius=str(r),height=f"({z1}) - ({z0})",base=[str(x),str(y),str(z0)],axis="Z",operation=op,name=name)
    if tgt: p["targets"]=[tgt]
    if bn: p["body_name"]=bn
    add("solid.cylinder",**p)
def poly(name,plane,pts,off=None):
    sp=dict(plane=plane,name=name)
    if off: sp["offset"]=off
    add("sketch.create",**sp)
    add("sketch.line",points=pts,closed=True)
    add("sketch.finish")
def pocket(name,z_top_expr,tgt):
    """cylinder along y clipped by the flat box (pocket of the motor can) -> body `name`, then cut from tgt"""
    cylY(name,"X_MOT","CRADLE_Y0 - 1","CAN_FACE","AXLE_Z","R_POCKET",op="new",bn=name)
    box(name+" flats","X_MOT - 20","X_MOT + 20","-1","60","AXLE_Z - CAN_H/2 - 0.2",z_top_expr,op="intersect",tgt=name)
    add("solid.combine",target=tgt,tools=[name],operation="cut")
