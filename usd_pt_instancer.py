import math
import numpy as np
import os,time
from pprint import pprint
from pxr import (Usd, UsdGeom, UsdPrim)
from mathutils import Matrix,Vector,Euler
os.system('cls')
then = time.time()

class USDMinewaysFile(): 
  def __init__(self, path:str) -> None:
    self.path:str = path
  
  @property
  def blocklib_path(self) -> str | None:
    path = f"{self.directory_path} \\ {self.file_name}_materials\\BlockLibrary.usda"
    return path if os.path.exists(path) else None

  @property
  def file_name(self) -> str:
    base = os.path.basename(file_path)
    return os.path.splitext(base)[0]

  @property
  def directory_path(self) -> str:
    return os.path.splitext(self.path)[0]

  @property
  def world_name(self) -> str:
    return os.path.basename(os.path.dirname(self.path))

  def __str__(self) -> str:
    return (
      f"{self.world_name}",
      f"{self.directory_path}"
    )
    
  def __repr__(self) -> str:
    return (f"a")

class USDPxr():

  @property
  def has_pxr(self):
    has_lib = False
    try:
      from pxr import Usd, UsdGeom
      has_lib = True
    except:
      pass
    return has_lib

class USDMinewaysStage(USDPxr):
  def __init__(self, path:str) -> None:
    self.__dict__ =
    USDMinewaysFile(path).__dict__.copy()
    if self.has_pxr:
      self.stage()
  
  def stage(self) -> None:
      self.stage = Usd.Stage.Open(self.path)
      self.blocklib = self.stage_ref.GetPrimAtPath(f"{self.blocklib_path()}/Blocks")
      self.voxelmap = self.stage_ref.GetPrimAtPath(self.voxel_path())
      self.chunks = self.voxel_ref.GetChildren()
  
  def is_point_instance(self) -> bool:
    return self.blocklib_path is None
  
  @property
  def voxel_path(self) -> str:
    return f"/{str(self.world_name).replace(' ','_')}/VoxelMap"

  @property
  def blocklib_path(self) -> str:
    return f"{self.voxelmap}/BlockLib"

  def __repr__(self):
    return (
      f"{self.stage_ref}"
    )
  
  def __str__(self):
    return (
      f"{self.stage_ref}"
    )

class USDMinewaysChunk(USDMinewaysStage):
  
  def __init__(self, chunk_filter:str = "") -> None:
    super().__init__()
    self.chunk_filter:str = chunk_filter if chunk_filter else "Chunk"
    
    self.positions:list = []
    self.indicies:list = []
    self.block_path:list = []
    if self.has_pxr:
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
    return self.stage.GetPrimAtPath(self.voxelmap + chunk_name)
    
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
    
    if self.has_pxr:
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
        child_path = str(usd_block_path)+child_name
            child_material = stage.GetPrimAtPath(child_path)
            # print(child_material)
            mat_rel = child_material.GetRelationship('material:binding')
            mat = mat_rel.GetTargets()   
            if not mat in _material and not mat == []:
                material = str(mat).split('Looks')
                material_path = usd_block_path+'/Blocks'+'/Looks'+material[1][:-3]
                material_ref = stage.GetPrimAtPath(material_path+'/diffuse_texture')
                diffuse = material_ref.GetProperty('inputs:file').Get()

                _material.append(mat)
                _texture.append(diffuse)
            if not 'Looks' in str(mesh):
                _mesh.append(mesh)
                mesh_inst = str(mesh).split('/Blocks')[1]
                block_inst = mesh_inst.split('/')
                _instance[block_inst[1]] = block_inst[2].strip('>)')
        _block.append(meshes)
        
    mesh_dict = {
        "block": _block,
        "mesh": _mesh,
        "material": _material,
        "texture": _texture,
        "instance": _instance,
    }
    return mesh_dict
#### USD functions ####
def read_path(file_path):
    """Create needed paths for the USD to get
    """
    
    path = os.path.splitext(file_path)
    base = os.path.basename(file_path)
    file_name = os.path.splitext(base)[0]

    blocklib_path = path[0]+'\\'+file_name+'_materials\\BlockLibrary.usda' #might need to adjust this
    world_name = os.path.basename(os.path.dirname(file_path))

    paths = {
        "file_path": file_path,
        "directory_filepath": path[0],
        "blocklib_filepath": blocklib_path,
        "file_name": file_name,
        "world_name": world_name,
    }

    return paths

def read_usd(paths):
    """Read the stage creation"""

    world_name = paths.get("world_name")
    world_str = str(world_name).replace(' ','_')
    usd_worldpath = '/'+world_str+'/VoxelMap'
    usd_blockpath = usd_worldpath+'/BlockLib'

    stage_ref = Usd.Stage.Open(paths.get("file_path"))
    block_ref = stage_ref.GetPrimAtPath(usd_blockpath+'/Blocks')
    voxel_ref = stage_ref.GetPrimAtPath(usd_worldpath)
    chunk_ref = voxel_ref.GetChildren()

    stage_dict = {
        "stage": stage_ref,
        "blocklib" :  block_ref,
        "chunk": chunk_ref,
        "voxelmap": voxel_ref,
        "world_path": usd_worldpath,
        "block_path": usd_blockpath,
    }
    return stage_dict

def read_chunk(usd_paths):
    """Reading though the chunks of the usd file
    'path' : reference path of blocks in the chunks
    'chunks' : chunks
    'points' : point postions 
    'indicies': block indicies to use for instancing
    """
    stage = usd_paths.get("stage")
    chunks = usd_paths.get("chunk")
    world_path = usd_paths.get("world_path")
    
    chunk_dict = {
        "chunks": [],
        "path" : [],
        "points" : [],
        "indices": []
    }

    for ch in chunks:
        chunk_name = str(ch).split(str(world_path))[1].split('>')[0]
        if 'Chunk' in chunk_name:            
            chunk_ref = stage.GetPrimAtPath(world_path + chunk_name)
            pos = chunk_ref.GetAttribute('positions').Get()
            id = chunk_ref.GetAttribute('protoIndices').Get()
            rel = chunk_ref.GetRelationship('prototypes')
            blocks_path = rel.GetTargets()
            
            chunk_dict['path'].append(blocks_path)
            chunk_dict['chunks'].append(chunk_name)
            chunk_dict['points'].append(pos) 
            chunk_dict['indices'].append(id)
            
    return chunk_dict

def read_block(usd_paths,chunks):
    """Read through the blocks of the chunks
    'path' : reference mesh path
    'block' : block name in number form
    'name': block real name
    'id' : the Minecraft block id
    'sub_id': the sub nbt id of that block 
    'instance' : object name block use for instancing 
    """
    stage = usd_paths.get("stage")
    usd_block_path = usd_paths.get("block_path")
    block_path = chunks.get("path")
    block_dict = {
        "block": [],
        "name" : [],
        "id": [],
        "sub_id": [],
        "path" : [],
        "instance": []
    }

    for blocks in block_path:
        _full_name = []
        _name = []
        _id = []
        _sub_id = []
        _mesh = []
        _instance = []

        for block in blocks:  
            block_name = str(block).split(usd_block_path+'/Blocks')[1]  
            block_ref = stage.GetPrimAtPath(block)
            child_mesh = block_ref.GetChildren()
            name = block_ref.GetAttribute('typeName').Get()
            # blocks['name'].append(name)
            _full_name.append(block_name)
            _name.append(name)
            id = block_name.split("/Block_")[1].split('_')
            _id.append(int(id[0]))
            _sub_id.append(int(id[1]))
            _mesh.append(child_mesh)
            if len(child_mesh) >= 2: # instance pick 
                tmp_instance = [1,block_name]
            else:
                tmp_instance = [0,block_name]
            _instance.append(tmp_instance)
        # print(full_name)
        block_dict['block'].append(_full_name)
        block_dict['name'].append(_name)
        block_dict['id'].append(_id)
        block_dict['sub_id'].append(_sub_id)
        block_dict['path'].append(_mesh)
        block_dict['instance'].append(_instance)

    # print(block_dict.get("block_name"))
    return block_dict

def read_mesh(usd_paths,blocks):
    """ Read the block mesh
    'block' : a list meshes of blocks, some blocks can have multiple meshes
    'mesh' : a list of meshes used
    'material': a list of materials used
    'texture': a list of textures used and its path
    'instance': a list of name for referencing instance
    """
    stage = usd_paths.get("stage")
    usd_block_path = usd_paths.get("block_path")
    usd_blocklib_path = usd_paths.get("blocklib")

    _material = []
    _block = []
    _texture = []
    _mesh = []
    _instance = {}
    for blocks in usd_blocklib_path.GetChildren():
        meshes = blocks.GetChildren()
        for mesh in meshes:
            child_name = str(mesh).split(str(usd_block_path))[1].split('>')[0]
            child_path = str(usd_block_path)+child_name
            child_material = stage.GetPrimAtPath(child_path)
            # print(child_material)
            mat_rel = child_material.GetRelationship('material:binding')
            mat = mat_rel.GetTargets()   
            if not mat in _material and not mat == []:
                material = str(mat).split('Looks')
                material_path = usd_block_path+'/Blocks'+'/Looks'+material[1][:-3]
                material_ref = stage.GetPrimAtPath(material_path+'/diffuse_texture')
                diffuse = material_ref.GetProperty('inputs:file').Get()

                _material.append(mat)
                _texture.append(diffuse)
            if not 'Looks' in str(mesh):
                _mesh.append(mesh)
                mesh_inst = str(mesh).split('/Blocks')[1]
                block_inst = mesh_inst.split('/')
                _instance[block_inst[1]] = block_inst[2].strip('>)')
        _block.append(meshes)
        
    mesh_dict = {
        "block": _block,
        "mesh": _mesh,
        "material": _material,
        "texture": _texture,
        "instance": _instance,
    }
    return mesh_dict

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




filePath = '\path' # add your path here

paths = read_path(filePath)
usd_paths = read_usd(paths)
chunks = read_chunk(usd_paths)
blocks = read_block(usd_paths,chunks)
meshes = read_mesh(usd_paths,blocks)

blender = False
clean = False # don't touch
try:
    import bpy
    blender = True
except:
    pass

if blender:
    import bmesh
    D = bpy.data
    C = bpy.context
    if clean:
        file_name = paths.get("file_name")
        clean_collection(D.collections[file_name + " USD Collection"])
    
    process = create_asset()
    collections = create_usd_collection(paths)
    node_groups = create_nodegroup(chunks,blocks)

    point_collection = collections[0][1]
    object_mesh = create_pts(paths,chunks,blocks)
    create_object(object_mesh,point_collection)


now = time.time() #Time after it finished
print("It took: ", now-then, " seconds")