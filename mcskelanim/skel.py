import requests
from typing import List, Optional

from pxr import Usd, UsdGeom, UsdSkel
from pxr import Sdf, Gf

def print_stage(stage, flatten=True):
  if flatten:
    stage.ExportToStrinf()
  else:
    stage = stage.Flatten().ExportToString()
  print(stage)

class BedrockJSON:
  def request_json(self, path):
    response = requests.get(path)
    
    # Check if the request was successful
    if response.status_code != 200:
      return None
    content = response.json()
      
    with open('t.json', "w") as file:
      file.write(str(content))
    bones = content.get("minecraft:geometry")[0].get("bones")
    return bones

class UsdRigWrite:
  pixel = 0.03125 # Geometry pixel per cm
  def __init__(self):
    self.stage: Optional[Usd.Stage]= None
    self.skel: Optional[UsdSkel.Skeleton] = None
    self.cube_xforms: Optional[List[UsdGeom.Xform]] = None
  
  def create_stage(self, name, start=0, end=0) -> Usd.Stage:
    if not name.endswith('.usda'):
      name += ".usda"
    stage = Usd.Stage.CreateNew(name)
    stage.SetMetadata('comment', "Minecraft rig stage usda generation by Trung Phạm")
    xform = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(xform.GetPrim())
    if start:
      stage.SetStartTimecode(start)
    if end:
      stage.SetEndTimecode(end)
    self.stage = stage
  
  def create_cube(
    self, name: str, path: Sdf.Path | str="", 
    pivot: tuple =(0,0,0), origin: tuple=(0,0,0), 
    size: tuple =(1,2,5), uv: tuple=(0,0), tex_res:tuple=(64,64)
  ):
    p = self.pixel
    x,y,z = size
    sx = 1/tex_res[0]
    sy = 1/tex_res[1]
    ox, oy = 0,0
    px,py, pz = pivot
    orx, ory, orz = origin
    
    stage = self.stage
    
    xform = UsdGeom.Xform.Define(stage, f'{path}/{name}')
    xform_prim = xform.GetPrim()
  
    attr = xform_prim.CreateAttribute('userProperties:blenderName:object', Sdf.ValueTypeNames.Token)
    attr.Set(name)
    if size == (0,0,0):
      return xform, None
  
    cube = UsdGeom.Mesh.Define(stage, f'{path}/{name}/{name}')
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
    uv_extent = (uv[11], uv[4])
    for i, v in enumerate(verts):
          verts[i] = v[0] * x, v[1] * y, v[2] * z
    for i,c in enumerate(uv):
      u,v = uv[i]
      uv[i] = (u+ox, v+oy)
    attr1 = cube_prim.CreateAttribute('userProperties:blenderName:mesh', Sdf.ValueTypeNames.String)
    attr1.Set("H")# * len(verts))
    cube.CreatePointsAttr(verts)
    cube.CreateFaceVertexIndicesAttr(faces)
    cube.CreateFaceVertexCountsAttr(count)
    cube.CreateExtentAttr([verts[2], verts[4]])
    cube.CreateNormalsAttr(normal)
    cube.SetNormalsInterpolation('faceVarying')
    texcoords = UsdGeom.PrimvarsAPI(cube).CreatePrimvar(
      "st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    texcoords.Set(uv)
    attr = cube.CreateAttribute('userProperties:uvBB:mesh', Sdf.ValueTypeNames.Float2)
    attr.Set(uv_extent)
    return xform
  
  def create_skeleton(self, joints, rest, bind, name="Skel", path=""):
    stage = self.stage
    root = UsdSkel.Root.Deone(stage, f'{path}/RIG_{name}')
    skel = UsdSkel.Skeleton.Define(stage, f'{path}/RIG_{name}/{name}')
    joints = skel.CreateJointsAttr(joints)
    skel.CreateRestTransformsAttr(rest)
    skel.CreateBindTransformsAttr(bind)
    self.skel = skel
    return skel, root

  def bind_skeleton(
    self, mesh, 
    indices = None, weights = None
  ):
    bind_ske = UsdSkel.BindingAPI.Apply(self.skel.GetPrim())
    bind_geo = UsdSkel.BindingAPI.Apply(mesh.GetPrim())
    bind_geo.CreateSkeletonRel().AddTarget(self.skel.GetPath())
    joint_indicies = bind_geo.CreateJointIndicesPrimvar(False,1)
    if not indices:
      indices = [0] * 8
    joint_indicies.Set(indices)
    joint_weight = bind_geo.CreateJointWeightsPrimvar(False, 1)
    if not weights:
      weights = [1] * 8
    joint_weight.Set(weights)
    
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
        bind.append(pivot)
      elif parent:
        lpivot = (prev_pivot[parent][0] - pivot[0], prev_pivot[parent][1] - pivot[1], prev_pivot[parent][2] - pivot[2])
        bind.append(lpivot)
        prev = c['name']
        parent_topo = prev_topo.get(parent)
        t = f"{parent_topo}/{prev}"
        prev_pivot[prev] = lpivot
        prev_topo[prev] = t #f"{parent_topo}/{prev}"
        prev = t
      topo.append(prev)
      rest.append(pivot)
   
    
    
    skel, root = self.create_skeleton(topo, rest, bind, name="skel", path="/World")
    for ib,c in enumerate(bones):
      cubes = c.get('cubes', [])
      pivot = c.get('pivot', [0,0,0])
      if cubes == []:
        self.create_cube(stage, name=c['name'], pivot=pivot, size=(0,0,0), path='/World')
      else:
        for i,cu in enumerate(cubes):
          cube = self.create_cube(stage, name=c['name']+f"_{i}",pivot=pivot, origin=cu['origin'], size=cu['size'], path='/World')
          self.bind_skeleton(cube.GetPrim().GetChildren()[0], indices=[ib] * 8)
    
      # print(dir(cube), ", dir(xform))
      # stage.Save()
      
  def output(self):
    print_stage(self.stage)