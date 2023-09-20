import os
import requests
import numpy as np
from typing import List, Optional

from pxr import Usd, UsdGeom, UsdSkel
from pxr import Sdf, Gf, Vt

FPS = 24

def print_stage(stage, flatten=True):
  if flatten:
    text = stage.Flatten().ExportToString()
  else:
    text = stage.ExportToString()
  print(text)

def loc_matrix(location = (0,0,0), rotation=None):
  if rotation == None:
    rotation = Gf.Rotation().SetIdentity()
  location = Gf.Vec3d(location[0], location[1], location[2])
  return Gf.Matrix4d(rotation, location)

def convert_np_to_vt(my_array: np.ndarray) -> Vt.Vec3fArray:
    return Vt.Vec3fArray.FromNumpy(my_array)


class BedrockJSON:
  def request_json(self, path) -> list | dict:
    response = requests.get(path)
    
    # Check if the request was successful
    if response.status_code != 200:
      return None
    content = response.json()
      
    # with open('t.json', "w") as file:
    #   file.write(str(content))
    if "model" in path:
      d = content.get("minecraft:geometry")
      if d:
        d = d[0]
      else:
        for i in content:
          if isinstance(content[i], dict):
            c = content[i].get("bones")
            if c:
              d = content[i]
              break
      data = d.get("bones")
    elif "animation" in path:
      data = content.get("animations")
    return data

class UsdRigWrite:
  pixel = 0.03125 # Geometry pixel per cm
  def __init__(self):
    self.stage: Optional[Usd.Stage]= None
    self.skel: Optional[UsdSkel.Skeleton] = None
    self.cube_xforms: Optional[List[UsdGeom.Xform]] = None
    
    self.bind_skel: Optional[UsdSkel.BindingAPI] = None
    self.root: Optional[UsdSkel.Root] = None
    
    self.use_matrixattr: bool = False
  
  def create_stage(self, name, start=0, end=0) -> Usd.Stage:
    if not name.endswith('.usda'):
      name += ".usda"
    if os.path.exists(name):
      stage = Usd.Stage.Open(name)
    else:
      stage = Usd.Stage.CreateNew(name)
    stage.SetMetadata('comment', "Minecraft rig stage usda generation by Trung Phạm")
    stage.SetMetadata('documentation', 'Foo')
    xform = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(xform.GetPrim())
    stage.SetFramesPerSecond(FPS)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    if start:
      stage.SetStartTimeCode(start)
    if end:
      stage.SetEndTimeCode(end)
    self.stage = stage
  
  def create_cube(
    self, name: str, path: Sdf.Path | str="", 
    pivot: tuple=(0,0,0), 
    origin: tuple=(0,0,0), size: tuple =(1,2,5), 
    uv: tuple=(0,0), tex_res:tuple=(64,64)
  ):
    p = self.pixel
    x,y,z = size
    sx = 1/tex_res[0]
    sy = 1/tex_res[1]
    ox, oy = 0,0
    px, py, pz = pivot
    orx, ory, orz = origin
    
    stage = self.stage
    
    xform = UsdGeom.Xform.Define(stage, f'{path}/{name}')
    xform_prim = xform.GetPrim()
    if pivot != (0,0,0):
      ops = xform.GetOrderedXformOps()
      if ops:
        ops[0].Set(Gf.Vec3d([px,py,pz]))
      else:
        xform.AddXformOp(UsdGeom.XformOp.TypeTranslate).Set(Gf.Vec3d([px,py,pz]))
           
  
    attr = xform_prim.CreateAttribute('userProperties:blenderName:object', Sdf.ValueTypeNames.String)
    attr.Set(name)
    if size == (0,0,0):
      return xform, None
  
    cube = UsdGeom.Mesh.Define(stage, f'{path}/{name}/mesh_{name}')
    cube_prim = cube.GetPrim()
  
    verts = [
      (p , -p, p),
      (-p, -p, p),
      (-p, -p, -p),
      (p, -p, -p),
      (p, p, p),
      (-p, p, p),
      (-p, p, -p),
      (p, p, -p)]
    faces = [
      0, 1, 2, 3,
      5, 4, 7, 6,
      1, 0, 4, 5,
      7, 6, 2, 3,
      4, 0, 3, 7,
      1, 5, 6, 2]
    count = [4] * 6
    normal = [(0, -1, 0), (0, -1, 0), (0, -1, 0), (0, -1, 0), (0, 1, 0), (0, 1, 0), (0, 1, 0), (0, 1, 0), (0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1), (1, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 0), (-1, 0, 0), (-1, 0, 0), (-1, 0, 0), (-1, 0, 0)]
    
    sxx= sx*x
    sxy= sx*y
    syy = sy*y
    syz = sy*z
    sxx2 = sxx*2
    sxy2 = sxy*2
    uv = [
    (sxx+sxy, 1-syz), (sxx, 1-syz), (sxx, 1-(syz+syy)), (sxx+sxy, 1-(syz+syy)), # North
    (sxx2+sxy2, 1-syz), (sxx2+sxy, 1-syz), (sxx2+sxy, 1-(syz+syy)), (sxx2+sxy2, 1-(syz+syy)), # South
    (sxx, 1-syz), (sxx+sxy, 1-syz), (sxx+sxy, 1), (sxx, 1), # Top
    (sxx+sxy, 1), (sxx2+sxy, 1), (sxx2+sxy, 1-syz), (sxx+sxy, 1-syz), # Down
    (sxx2+sxy, 1-syz), (sxx+sxy, 1-syz), (sxx+sxy, 1-(syz+syy)), (sxx2+sxy, 1-(syz+syy)), # West
    (sxx, 1-syz), (0, 1-syz), (0, 1-(syz+syy)), (sxx, 1-(syz+syy)) # East
    ]
    uv_extent = [uv[11], uv[4]]
    for i, v in enumerate(verts):
      verts[i] = v[0] * x + orx, v[1] * y + ory, v[2] * z + orz
          
    for i,c in enumerate(uv):
      u,v = uv[i]
      uv[i] = (u+ox, v+oy)
    attr1 = cube_prim.CreateAttribute('userProperties:blenderName:mesh', Sdf.ValueTypeNames.String)
    attr1.Set(f"mesh_{name}")# * len(verts))
    cube.CreatePointsAttr(verts)
    cube.CreateFaceVertexIndicesAttr(faces)
    cube.CreateFaceVertexCountsAttr(count)
    cube.CreateExtentAttr([verts[2], verts[4]])
    cube.CreateNormalsAttr(normal)
    cube.SetNormalsInterpolation('faceVarying')
    texcoords = UsdGeom.PrimvarsAPI(cube).CreatePrimvar(
      "st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    texcoords.Set(uv)
    attr = cube_prim.CreateAttribute('userProperties:uvBB:mesh', Sdf.ValueTypeNames.Float2Array)
    attr.Set(uv_extent)
    return xform
  
  def create_skeleton(self, joints, rest, bind, name="Skel", path="/World"):
    stage = self.stage
    # root = UsdSkel.Root.Define(stage, f'{path}/RIG_{name}')
    skel_path = f'{path}/RIG_{name}/{name}' if self.root else f'{path}/{name}'
    self.skel = skel = UsdSkel.Skeleton.Define(stage, skel_path)
    joints = skel.CreateJointsAttr(joints)
    skel.CreateRestTransformsAttr(rest)
    skel.CreateBindTransformsAttr(bind)
    # self.root = root
    return skel

  def bind_skelleton(
    self, mesh, 
    indices = None, weights = None
  ):
    if self.root:
      bind_root = UsdSkel.BindingAPI.Apply(self.skel_root.GetPrim())
    self.bind_skel = UsdSkel.BindingAPI.Apply(self.skel.GetPrim())
    bind_geom = UsdSkel.BindingAPI.Apply(mesh.GetPrim())
    bind_geom.CreateSkeletonRel().AddTarget(self.skel.GetPath())
    joint_indicies = bind_geom.CreateJointIndicesPrimvar(False,1)
    if not indices:
      indices = [0] * 8
    joint_indicies.Set(indices)
    joint_weight = bind_geom.CreateJointWeightsPrimvar(False, 1)
    if not weights:
      weights = [1] * 8
    joint_weight.Set(weights)
    identity = Gf.Matrix4d().SetIdentity()
    if self.use_matrixattr:
      bind_geom.CreateGeomBindTransformAttr(identity)
  
  def create_animation(
    self, 
    name: str, length:float, bones:dict, 
    extend_stage_end: bool=True
  ):
    # Convert length to integer frame, set
    frame = 0
    if isinstance(length, float) and length != 0:
      frame = int(round(length*FPS))
    if self.stage.GetEndTimeCode() < length and extend_stage_end:
      self.stage.SetEndTimeCode(frame)
    
    anim = UsdSkel.Animation.Define(self.stage, f"/World/skel/{name}")
    
    translate = {}
    rotate = {}
    scale = {}
    bone_list = []
    _bone_list = []

    
    for f in range(frame):
      _t = []
      _r = []
      _s = []
      for k,v in bones.items():
        # First loop read through the bone
        # Second loop add it in
        if f == 0:
          _bone_list.append(k)
          bone_list.append(self.topo[k])
        if f == 1:
          anim.CreateJointsAttr().Set(bone_list)
        # Get the keyframes infomation
        for k in ["location", "rotation", "scale"]:
          key = v.get(k)
          if key:
            if isinstance(key, dict):
              for fk, fv  in key.items():
                if round(float(fk)*FPS) == f:
                  if k == "location":
                    _t.append(fv)
                  elif k == "rotation":
                    _r.append(fv)
            else:
              if k == "location":
                _t.append(key)
              elif k == "rotation":
                _r.append(key)
          else:
            if k == "location":
              _t.append([0,0,0])
            elif k == "rotation":
              _r.append([0,0,0])
      if frame:
        anim.CreateTranslationsAttr().Set(_t, f)
      else:
        anim.CreateTranslationsAttr().Set(_t)
      # anim_rot = {}
    
  
  def from_json(self, bones):
    stage = self.stage
    # Create Joint Topology, rest, bind Transforms
    rest = []
    bind = []
    topo = []
    prev_topo = {}
    prev_pivot = {}
    prev = None
    for c in bones:
      parent = c.get("parent")
      pivot = c.get("pivot", (0,0,0))
      if prev == None:
        prev = c['name']
        prev_topo[prev] = prev
        prev_pivot[prev] = pivot
        lpivot = pivot
      elif parent:
        lpivot = (
          pivot[0] - prev_pivot[parent][0], 
          pivot[1] - prev_pivot[parent][1], 
          pivot[2] - prev_pivot[parent][2]
        )
        prev = c['name']
        parent_topo = prev_topo.get(parent)
        t = f"{parent_topo}/{prev}"
        prev_pivot[prev] = lpivot
        prev_topo[prev] = t #f"{parent_topo}/{prev}"
        prev = t
      topo.append(prev)
      bind.append(loc_matrix(lpivot))
      rest.append(loc_matrix(pivot))
   
    self.topo = prev_topo
   
    skel = self.create_skeleton(topo, Vt.Matrix4dArray(rest), Vt.Matrix4dArray(bind), name="skel", path="/World")
    for ib,c in enumerate(bones):
      cubes = c.get('cubes', [])
      pivot = c.get('pivot', [0,0,0])
      if cubes == []:
        self.create_cube(name=c['name'], pivot=pivot, size=(0,0,0), path=skel.GetPath())
      else:
        for i,cu in enumerate(cubes):
          cube = self.create_cube(name=c['name']+f"_{i}", pivot=(0,0,0), origin=cu['origin'], size=cu['size'], path=skel.GetPath())
          self.bind_skelleton(cube.GetPrim().GetChildren()[0], indices=[ib] * 8)
    
      # print(dir(cube), ", dir(xform))
      # stage.Save()
  
  def anim_from_json(self, anims: dict):
    for i,(k,v) in enumerate(anims.items()):
      l = v.get("animation_length")
      self.create_animation(f"anim_{i}", l if l else 0, v.get("bones"))
  
  def output(self):
    print_stage(self.stage)