import math
import numpy as np

from pathlib import Path
from mathutils import Matrix,Vector,Euler

try:
  from pxr import (Usd, UsdGeom, UsdPrim)
except: 
  pass

from pxr import UsdGeom

def stage_set_axis(stage, axis):
  if axis == 'Z':
    axis = UsdGeom.Tokens.z
  elif axis == 'Y':
    axis == UsdGeom.Tokens.y
  if isinstance(axis, UsdGeom.Tokens):
    UsdGeom.UsdGeomSetStageUpAxis(stage, axis)

def stage_get_axis(stage):
  return 'Z' if UsdGeomGetStageUpAxis(stage) == UsdGeom.Tokens.z else 'Y'
  
def has_prim_type(prim_type):
  has_type = False
  for x in stage.Traverse():
    if x.IsA(prim_type): # UsdGeom.Mesh
      has_type = True
      break
  return has_type

class USDMinewaysFile:
  
  def __init__(self, path: Path | str) -> None:
    if isinstance(path, str):
      path = Path(path)
    self.path: Path = path 
    
    self.directory_path = self.path.parent
    self.file_name = self.path.stem
    path = self.directory_path / f"{self.file_name}_materials" / "BlockLibrary.usda"
    self.blocklib_path = path if Path.exists(path) else None
    self.world_name = self.directory_path.name
  
  def __str__(self) -> str:
    return (
      f"{self.world_name}",
      f"{self.directory_path}"
    )
  
  def __repr__(self) -> str:
    return __str__(self)

class USDPxr:

  @property
  def has_pxr(self):
    has_lib = False
    try:
      from pxr import Usd, UsdGeom
      has_lib = True
    except:
      pass
    return has_lib

class MWStage(USDPxr, USDMinewaysFile):
  
  def __init__(self, path:str) -> None:
    super().__init__(path)
    self.voxel_path =  f"/{str(self.world_name).replace(' ','_')}/VoxelMap"
    self.blocklib_path = f"{self.voxelmap}/BlockLib"
    
    self.chunks: List[MWChunk] = []
    self.chunk_filter: str = ""
    
  def get_stage(self) -> None:
    self.stage = Usd.Stage.Open(self.path)
    self.blocklib = self.stage_ref.GetPrimAtPath(f"{self.blocklib_path()}/Blocks")
    self.voxelmap = self.stage_ref.GetPrimAtPath(self.voxel_path())
    self.chunks = self.voxel_ref.GetChildren()
  
  def is_point_instance(self) -> bool:
    return self.blocklib_path is None
    
  def set_chunk_filter(self, chunk_filter: str):
    self.chunk_filter = chunk_filter
  
  def get_chunks(self):
    chunks = []
    for c in self.chunks:
      if self.chunk_filter in c.GetName():
        chunks.append(c)
    
    return chunks
  
  def get_chunk_prim(self, chunk_name:str) -> UsdPrim:
    return self.stage.GetPrimAtPath(f"{self.voxelmap}{chunk_name}")

class MWChunk():
  
  def __init__(self, prim: UsdPrim) -> None:
    self.chunk_prim = prim
    self.name = prim.GetName()
    self.positions: list = self.chunk_prim.GetAttribute('positions').Get()
    self.indicies: list = self.chunk_prim.GetAttribute('protoIndices').Get()
    self.block_path: list = self.chunk_prim.GetRelationship('prototypes').GetTargets()
    self.blocks = []
    self.instance_blocks = []
    
    
    def get_blocks(self):
      _blocks= []
      for blocks in self.blocks_path:
        for block in blocks:
          if not block in _blocks:
            self.instance_blocks.append(MWBlock(block))
          _blocks.append(block)
          self.blocks.append(MWBlock(block))
       
    def get_block(self, list_index:int) -> str:
      return self.instance_blocks[list_index]

class MWBlock:

  def __init__(self):
    self.name: str = ""
    self.id:str = ""
    self.sub_id = ""
    self.mesh_path: Gf.Path = ""
    self.block_instance = ""
    self.meshes: List[MWMesh] = []
    

  def block(self) -> None:
    _full_name = []
    _name = []
    _id = []
    _sub_id = []
    _mesh = []
    _instance = []
    
    for block in self.blocks_list:
      block_name = str(block).split(usd_block_path+'/Blocks')[1]  
      block_ref = stage.GetPrimAtPath(block)
      child_mesh = block_ref.GetChildren()
      name = block_ref.GetAttribute('typeName').Get()
      # blocks['name'].append(name)
      _full_name.append(block_name)
      _name.append(name)
      # TODO better with handling block name
      b_id = block_name.split("/Block_")[1].split('_')
      _id.append(int(b_id[0]))
      _sub_id.append(int(b_id[1]))
      _mesh.append(child_mesh)
      if len(child_mesh) >= 2: # instance pick 
        b_instance = (1,block_name)
      else:
        b_instance = (0,block_name)
      _instance.append(tmp_instance)
      # print(full_name)
      
    self.block.append(_full_name)
    self.block_name.append(_name)
    self.block_id.append(_id)
    self.block_sub_id.append(_sub_id)
    self.block_mesh_path.append(_mesh)
    self.block_instance.append(_instance)
  
class MWMesh:
  def __init__(self):
    self.material = []
    self.texture = []
    self.mesh_instance = {}
    
    self.mesh()
  
  def mesh(self):
    _material = []
    _block = []
    _texture = []
    _mesh = []
    _instance = {}
    for blocks in self.blocklib_path.GetChildren():
      meshes = blocks.GetChildren()
      for mesh in meshes:
        child_name = str(mesh).split(str(self.block_path))[1].split('>')[0]
        child_path = f"{usd_block_path}{child_name}"
            child_material = stage.GetPrimAtPath(child_path)
            # print(child_material)
            mat_rel = child_material.GetRelationship('material:binding')
            mat = mat_rel.GetTargets()   
            if not mat in _material and not mat == []:
                material = str(mat).split('Looks')
                material_path = f"{usd_block_path}/Blocks/Looks{material[1][:-3]}"
                material_ref = stage.GetPrimAtPath(f"{material_path}/diffuse_texture")
                diffuse = material_ref.GetProperty('inputs:file').Get()

                _material.append(mat)
                _texture.append(diffuse)
            if not 'Looks' in str(mesh):
                _mesh.append(mesh)
                mesh_inst = str(mesh).split('/Blocks')[1]
                block_inst = mesh_inst.split('/')
                _instance[block_inst[1]] = block_inst[2].strip('>)')
        _block.append(meshes)
        
    self.mesh_block = _block
    self.mesh = _mesh
    self.mesh_material = _material
    self.mesh_texture = _texture
    self.mesh_instance = _instance

## adjacent function check if 2 points position is different only 1 axis
def adjacent_point():
    ch = chunks.get("chunks")
    pt = chunks.get("points")
    # for ic,c in enumerate(ch[0][0]):
    a =np.array(pt[0])
    for v1 in a:
        for v2 in a: 
            if np.any(np.abs(np.diff([v1,v2],axis=1))) == 1:
                # diff = abs(v1[0] - v2[0]) + abs(v1[1] - v2[1]) + abs(v1[2] - v2[2]) 
                # if diff == 1 and not (v1 == v2):
                #     print([str(v1),str(v2)],[i1,i2])
                print(v1,v2)

if __name__ == '__main__':
  print("TODO")
