import os
import requests
import numpy as np
from typing import List, Optional, Union
import math
from mathutils import Vector, Matrix

from pxr import Usd, UsdGeom, UsdSkel, UsdShade, UsdUtils
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

def mat3_to_vec_roll(mat: Gf.Matrix3d):
  if isinstance(mat, Gf.Matrix3d):
    vec = mat.GetColumn(1)
    vecmat = vec_roll_to_mat3(vec, 0)
    vecmatinv = vecmat.GetInverse()
    rollmat = vecmatinv * mat
  else:
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(vec, 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv @ mat
  roll = math.atan2(rollmat[0][2], rollmat[2][2])
  return vec, roll

def vec_roll_to_mat3(vec: Union[Gf.Vec3d,Vector], roll: float):
    if isinstance(vec, Gf.Vec3d):
      target = Gf.Vec3d((0, 0.1, 0))
      nor = vec.GetNormalized()
      axis = target.GetCross(nor)
      if axis.GetDot(axis) > 0.0000000001:
        axis.GetNormalized()
        theta = target.GetAngle(nor)
        bMatrix = Gf.Matrix4d().SetRotation(Gf.Rotation(theta, 3, axis))
      else:
        updown = 1 if target.dot(nor) > 0 else -1
        bMatrix = Gf.Matrix4d().SetScale(Gf.Size3(updown, 3))
        bMatrix[2][2] = 1.0
      rMatrix = Gf.Matrix4d().SetRotation(Gf.Rotation(roll, 3, nor))
      mat = rMatrix * bMatrix
    else:
      target = Vector((0, 0.1, 0))
      nor = vec.normalized()
      axis = target.cross(nor)
      if axis.dot(axis) > 0.0000000001:
        axis.normalize()
        theta = target.angle(nor)
        bMatrix = Matrix.Rotation(theta, 3, axis)
      else:
        updown = 1 if target.dot(nor) > 0 else -1
        bMatrix = Matrix.Scale(updown, 3)               
        bMatrix[2][2] = 1.0

      rMatrix = Matrix.Rotation(roll, 3, nor)
      mat = rMatrix @ bMatrix
      return mat


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
  name = "Default"
  def __init__(self):
    self.stage: Optional[Usd.Stage]= None
    self.skel: Optional[UsdSkel.Skeleton] = None
    self.cube_xforms: Optional[List[UsdGeom.Xform]] = None
    self.materials = []
    
    self.bind_skel: Optional[UsdSkel.BindingAPI] = None
    self.root: Optional[UsdSkel.Root] = None
    
    self.use_matrixattr: bool = False
  
  def set_name(self, value):
    self.name = value
  
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
    uv: tuple=(0,0), tex_res:tuple=(64,64),
    mat = None
  ):
    p = self.pixel
    x,y,z = size
    sx = 1/tex_res[0]
    sy = 1/tex_res[1]
    ox, oy = 0,0
    px, py, pz = pivot
    orx, ory, orz = origin
    
    stage = self.stage
    cube_path = f'{path}/{name}'
    xform = UsdGeom.Xform.Define(stage, cube_path)
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
  
    cube = UsdGeom.Mesh.Define(stage, f'{cube_path}/mesh_{name}')
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
      verts[i] = v[0] * x, v[1] * y, v[2] * z
          
    for i,c in enumerate(uv):
      u,v = uv[i]
      uv[i] = (u+ox, v+oy)
    
    # Attibutes
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
    
    # Set Materials
    if mat == None:
      if not self.materials:
        mat = self.create_material(self.name, "/tex/chicken.png", path=cube_path)
        self.materials.append(mat)
      self.assign_mesh_mat(cube, self.materials[0])
    return xform
  
  def create_material(self, name, texture, path="/World"):
    path = f"{path}/{name}"
    material = UsdShade.Material.Define(self.stage, path)

    pbrShader = UsdShade.Shader.Define(self.stage, f"{path}/Shader")
    pbrShader.CreateIdAttr("UsdPreviewSurface")
    pbrShader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.0)
    pbrShader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    
    material.CreateSurfaceOutput().ConnectToSource(pbrShader.ConnectableAPI(), "surface")
    
    stReader = UsdShade.Shader.Define(self.stage, f'{path}/stReader')
    stReader.CreateIdAttr('UsdPrimvarReader_float2')
    
    diffuseTextureSampler = UsdShade.Shader.Define(self.stage, f'{path}/diffuseTexture')
    diffuseTextureSampler.CreateIdAttr('UsdUVTexture')
    diffuseTextureSampler.CreateInput('file', Sdf.ValueTypeNames.Asset).Set(texture)
    diffuseTextureSampler.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(stReader.ConnectableAPI(), 'result')
    diffuseTextureSampler.CreateOutput('rgb', Sdf.ValueTypeNames.Float3)
    pbrShader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(diffuseTextureSampler.ConnectableAPI(), 'rgb')
    stInput = material.CreateInput('frame:stPrimvarName', Sdf.ValueTypeNames.Token)
    stInput.Set('st')
    
    stReader.CreateInput('varname',Sdf.ValueTypeNames.Token).ConnectToSource(stInput)
    return material
  
  def assign_mesh_mat(self, mesh, material):
    mesh.GetPrim().ApplyAPI(UsdShade.MaterialBindingAPI)
    UsdShade.MaterialBindingAPI(mesh).Bind(material)
  
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
    extend_stage_end: bool=True, **kwargs
  ):
    # Convert length to integer frame, set
    frame = 0
    if isinstance(length, float) and length != 0:
      frame = int(round(length*FPS))
    if self.stage.GetEndTimeCode() < length and extend_stage_end:
      self.stage.SetEndTimeCode(frame)
      
    xform = UsdGeom.Xform.Define(self.stage, f"/World/skel/AnimXform_{name}")
    xform_prim = xform.GetPrim()
    attr = xform_prim.CreateAttribute(f'userProperties:mainAnimXform', Sdf.ValueTypeNames.String)
    attr.Set(name)
    
    anim = UsdSkel.Animation.Define(self.stage, f"/World/skel/Anim_{name}")
    anim_prim = anim.GetPrim()
    for ak, av in kwargs.items():
      if isinstance(av, str):
        value_type = Sdf.ValueTypeNames.String
      elif isinstance(av, bool):
        value_type = Sdf.ValueTypeNames.Bool
      else:
        continue
      attr = xform_prim.CreateAttribute(f'userProperties:anim{ak.capitalize()}', value_type)
      attr.Set(av)
    
    translate = {}
    rotate = {}
    scale = {}
    bone_list = []
    _bone_list = []

    increased = False
    if frame == 0:
      frame = 1
      increased = True
    
    loc_keys = {}
    rot_keys = {}
    for f in range(frame):
      _t = []
      _r = []
      _s = []
      has_loc = False
      has_rot = False
      for bk,bv in bones.items():
        # First loop read through the bone
        # Second loop add it in
        if f == 0:
          _bone_list.append(bk)
          bone_list.append(self.topo[bk])
          xform = UsdGeom.Xform.Define(self.stage, f"/World/skel/AnimXform_{name}/Anim_{name}_{bk}")
          xform_prim = xform.GetPrim()
          xform.AddXformOp(UsdGeom.XformOp.TypeTransform).Set(loc_matrix(self.pivot[bk]))
                  
        if f == 1 and increased:
            break
          
        # Get the keyframes infomation
        for k in ["location", "rotation", "scale"]:
          key = bv.get(k)
          if key:
            # has_keyframes = False
            if isinstance(key, dict):
              for fk, fv  in key.items():
                if round(float(fk)*FPS) == f:
                  if k == "location":
                    _t.append(fv)
                    has_loc = True
                    loc_keys[bk] = fv
                  elif k == "rotation":
                    _r.append(fv)
                    has_rot = True
                    rot_keys[bk] = fv
                    
            else:
              if k == "location":
                _t.append(key)
                has_loc = True
                loc_keys = {"0": key}
              elif k == "rotation":
                _r.append(key)
                has_rot = True
                rot_keys = {"0": key}
            
            # Preverse the data in Xformable
            if f == 0:
              attr = xform_prim.CreateAttribute(f'userProperties:{k}Expr', Sdf.ValueTypeNames.String)
              attr.Set(str(key))
          else:
            if k == "location":
              _t.append([0,0,0])
            elif k == "rotation":
              _r.append([0,0,0])
      
      if has_loc:
        translate[f] = loc_keys
      if has_rot:
        rotate[f] = rot_keys
        
    print(rotate)
    anim.CreateJointsAttr().Set(bone_list)
      # print(_t)
      # if frame:
      #   anim.CreateTranslationsAttr().Set(_t, f)
      # else:
      #   anim.CreateTranslationsAttr().Set(_t)
      # anim_rot = {}
    
  mats = ["Texture"] # For now
  
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
      else:
        prev = c['name']
        prev_pivot[prev] = pivot
        prev_topo[prev] = prev
      
      topo.append(prev)
      bind.append(loc_matrix(lpivot))
      rest.append(loc_matrix(pivot))
   
    self.topo = prev_topo
    self.pivot = prev_pivot
   
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
  
  def anim_from_json(self, anims: dict, limit=0):
    for i,(k,v) in enumerate(anims.items()):
      if limit != 0 and i == limit:
        break
      l = v.get("animation_length")
      name_compos = k.split(".", 2)
      if len(name_compos) == 3:
        name = name_compos[2].replace(".", "_")
      else:
        name = i
      self.create_animation(f"{name}", l if l else 0, v.get("bones"), loop=v.get("loop", False), start_delay=v.get("start_delay"))
  
  def output(self):
    print_stage(self.stage)
  
  @classmethod
  def zip(cls, usd_path, path):
    UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(usd_path), path)
    
    