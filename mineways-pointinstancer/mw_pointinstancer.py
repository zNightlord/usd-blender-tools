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
    if x.IsA(prim_type) # UsdGeom.Mesh
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

class USDMinewaysStage(USDPxr, USDMinewaysFile):
  
  def __init__(self, path:str) -> None:
    super().__init__(path)
    self.voxel_path =  f"/{str(self.world_name).replace(' ','_')}/VoxelMap"
    self.blocklib_path = f"{self.voxelmap}/BlockLib"
  
  def get_stage(self) -> None:
    self.stage = Usd.Stage.Open(self.path)
    self.blocklib = self.stage_ref.GetPrimAtPath(f"{self.blocklib_path()}/Blocks")
    self.voxelmap = self.stage_ref.GetPrimAtPath(self.voxel_path())
    self.chunks = self.voxel_ref.GetChildren()
  
  def is_point_instance(self) -> bool:
    return self.blocklib_path is None

class USDMinewaysChunk(USDMinewaysStage):
  
  def __init__(self, chunk_filter:str = "") -> None:
    super().__init__()
    self.chunk_filter:str = chunk_filter if chunk_filter else "Chunk"
    
    self.positions:list = []
    self.indicies:list = []
    self.block_path:list = []
    
    self.chunks()

  def chunks(self) -> None:
      for chunk in self.chunks:
        chunk_name = self.base_chunk(chunk)
        if self.chunk_filter in chunk_name:
          chunk_ref = self.get_chunk(chunk_name)
          self.positions.append( chunk_ref.GetAttribute('positions').Get())
          self.indicies.append(chunk_ref.GetAttribute('protoIndices').Get())
          self.block_path.append(chunk_ref.GetRelationship('prototypes').GetTargets())

  @property
  def chunks_list(self) -> list:
    return [self.base_chunk(chunk) for chunk in self.chunks]

  def base_chunk(self, chunk) -> str:
    """
      Get chunk base
      TODO get base name without doing weird string, correct way
    """
    # Something stupid about this
    return str(chunk).split(str(self.voxelmap))[1].split('>')[0]

  def get_chunk(self, chunk_name:str) -> UsdPrim:
    return self.stage.GetPrimAtPath(f"{self.voxelmap}{chunk_name}")
    
  def __repr__(self):
    return (
      f"{self.stage_ref}"
    )
  
  def __str__(self):
    return (
      f"{self.stage_ref}"
    )

class USDMinewaysBlock(USDMinewaysChunk):

  def __init__(self):
    super().__init__()
    
    self.block:list = []
    self.block_name:list = []
    self.block_id:list = []
    self.block_sub_id:list = []
    self.block_mesh_path:list = []
    self.block_instance:list = []
    
    self.block()

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
  
  @property
  def blocks_list(self) -> list:
    return [blocks for blocks in self.blocks_path]
    
  def get_block(self, list_index:int) -> str:
    return (f"{self.block[list_index]} {self.name[list_index]} {self.id[list_index]} {self.sub_id[list_index]}")
  
  def __repr__(self):
    return (
      f"{self.stage_ref}"
    )
  
  def __str__(self):
    return (
      f"{self.stage_ref}"
    )
  
class USDMinewaysMesh(USDMinewaysBlock):
  def __init__(self):
    self.mesh = []
    self.mesh_block = []
    self.mesh_material = []
    self.mesh_texture = []
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
