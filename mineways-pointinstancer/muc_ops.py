import bpy
from bpy.types import Nodes, Node
from bpy.utils import register_class, unregister_class

import numpy as np

from .usd import USDMinewaysFile, USDMinewaysStage
from . import util

#### Blender functions start here ####
class BlendHeleper:
  def clean_mesh(meshes):
      for mesh in meshes:
          D.meshes.remove(mesh,do_unlink=True)
  
  def clean_mat(materials):
      for material in materials:
          D.materials.remove(material,do_unlink=True)   
  
  def clean_image(images):
      for img in images:
          D.images.remove(img,do_unlink=True)   
  
  def clean_obj(objs):
      for obj in objs:
          D.objects.remove(obj,do_unlink=True) 
          
  def clean_collection(collection):
      cols = collection.children_recursive
      for col in cols:
          objs = col.objects
          for obj in objs:
              D.objects.remove(obj,do_unlink=True) 
          D.collections.remove(col,do_unlink=True) 
      D.collections.remove(collection,do_unlink=True)
      
  def fix_material(materials):
      """ Basic fix material """
      for mat in materials:
          try:
              imgNode = mat.node_tree.nodes["Image Texture"]
              img = imgNode.image
              if not "_n" in img.name:
                  imgNode.interpolation = 'Closest'
          except:
              pass
            
  def create_collection(name, parent = None):
      """ Use util  
      Create collection, if exist get it."""
      collection = D.collections.get(name)
      if not collection:
          collection =  D.collections.new(name)
          if parent != None:
              parent.children.link(collection)
          else:
              C.scene.collection.children.link(collection)
      return collection

class NodeUtilityMixin:
  nodes: Nodes
  
  def create_nodes(self, bl_idname, **attrs) -> Node:
    return util.create_nodes(self.nodes, bl_idname, **attrs)
  
  def connect_sockets(self, input_socket, output_socket):
    if util.min_bv((3,6,0)):
      connect_sockets(input_socket, output_socket)
    else:
    
    
  
def import_usd(filePath, preview = True, **kwargs):
  bpy.ops.wm.usd_import(
    filepath=filePath, 
    import_usd_preview=preview, **kwargs
  )

def create_set_meshattr(mesh, attr_type, attr_name, value = None):
  """ B4.0 Refactor this so create a function is needed"""
  if hasattr(mesh, attr_type):
    vert_attr = getattr(mesh, attr_type)
    vert_attr.new(name=attr_name)
    
    if value:
      vert_attr.data.foreach_set("value", value)
    return vert_attr
    
class Points:
  def __init__(self, file):
    self.paths : USDMinewaysFile = file
    self.stage : USDMinewaysStage = 
    self.chunks = 
    self.blocks = 
    self.collections: List[Collection] = []
    
  def create_pts(paths,chunks,blocks):
    """Create mesh points with attributes"""
    file_name = self.paths.get("file_name")  # file name
    ch = self.chunks.get("chunks")       # chunks
    points = self.chunks.get("points")       # points position
    indicies = self.chunks.get("indices")    # instance index
    id = self.blocks.get("id")              # block index
    sub_id =  self.blocks.get("sub_id")      # block nbt index
    
    object_mesh = []
    for ic,chunk in enumerate(ch):
        # TODO
        mesh_name  = f"{file_name} - PT_{chunk.split('/')[1]}"
        mesh = D.meshes.get(mesh_name)
        if not mesh:
            mesh = D.meshes.new(mesh_name)
        else:
            # Clean the mesh 
            D.meshes.remove(mesh, do_unlink=True) 
            mesh = D.meshes.new(mesh_name)
            
        a = np.array(points[ic])
        # swaping Y and Z since this is Blender there is stage_get_axis in usd_util
        a[:,[1, 2]] = a[:,[2, 1]] 
        # e = a
        verts = np.concatenate([np.array(i) for i in a])
        
    
        num_vertices = verts.shape[0] // 3    
        # TODO use pydata
        mesh.vertices.add(num_vertices)
        mesh.vertices.foreach_set("co", verts)
        
        ins = indicies[ic]
        blo = [id[ic][i] for i in ins]
        sub = [sub_id[ic][i] for i in ins]
        ins_index = create_set_meshattr(mesh, 'vertex_layers_int', name = "instance_index", value = ins)
        
        blo_index = create_set_meshattr(mesh, 'vertex_layers_int', name= "block_index", value = blo)
        nbt_index = create_set_meshattr(mesh, 'vertex_layers_int', name="nbt_index", value= sub)
        
        vertices = np.zeros(len(mesh.vertices) * 3,dtype=np.int32)
        mesh.vertices.foreach_get("co", vertices)
        vertices = vertices.reshape(-1,3)

        bm = bmesh.new()   
        bm.from_mesh(mesh)   
        
        bm.to_mesh(mesh)
        bm.free()
        
        mesh.update()
        mesh.validate()
        
        object_mesh.append(mesh)
    return object_mesh

  def create_usd_collection(self):
    """ Create collection to store usd and fix merged blocks
    Example: Grass Block is Block_2_0 need to merge all meshes
    dirt,grass_block_side,grass_block_top into one """
    # Create the USD collections
    collections = []
    file_name = self.paths.get("file_name")
    world_name = self.paths.get("world_name")
    
    
    usd_col = util.create_collection(f"{file_name} USD Collection")
    pt_col = util.create_collection(f"{file_name} USD Points", parent = usd_col)
    block_col = util.create_collection(f"{file_name} USD BlockLib", parent = usd_col)
    
    collections.append([usd_col,pt_col,block_col])
    
    if not D.objects.get(f"{file_name} Blocks"):
        import_usd(filePath)
        
        objs = C.selected_objects
        moveto_collection(objs, block_col)
    
        #Fix all the block merge and apply 
        block_objs = block_col.objects['Blocks'].children_recursive
        rot = Matrix.Rotation(math.radians(90),4,'X')
        loc = Matrix.Translation((-0.5,-0.5,-0.5))
        
        path = ['Looks', 'Blocks','VoxelMap', world_name.replace(' ','_')]

        if D.objects[path[2]]:
            for child in D.objects[path[2]].children_recursive:
                D.objects.remove(child,do_unlink=True)
            D.objects.remove(D.objects[path[2]],do_unlink=True)
        for obj in D.objects:
            if obj.name in path and not 'Block' in obj.name:
                for child in obj.children_recursive:
                    child.name = f"{file_name} {child.name}"
                obj.name =  f"{file_name} {obj.name}"
        block_obj = D.objects.get('Blocks')
        if block_obj:
            block_obj.name =  f"{file_name} {block_obj.name}"

        new_i = 0
        row = 0
        column = 0
        for i,obj in enumerate(block_objs):
        
            pre_loc = Matrix.Translation((row,-2,column))
            try:
                if obj.type != 'MESH' and 'Block' in obj.name:
                    self.merge_block()
                    
                ma = rot @ loc
                me = obj.data
                me.transform(ma)
                    
                obj.matrix_world = pre_loc
            except: # Except broken cause by previous merge RNA blocks
                new_i -=1
                pass
            new_i +=1
            row = new_i % 16
            column = math.floor(new_i / 16)
        # Need better way to do this
        fix_material(D.materials)
    return collections
  
  def merge_block(self):
    """TODO """
    merge_mesh = D.meshes.new(f"{obj.name}_merge")
    merge_obj = D.objects.new(merge_mesh.name, merge_mesh)
    merge_obj.parent = obj.parent
    merge_obj.location = obj.location
    col = obj.users_collection[0]
    col.objects.link(merge_obj)
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = merge_obj
    merge_obj.select_set(True)
    for children_mesh in obj.children:
        children_mesh.select_set(True)
        D.objects.remove(obj, do_unlink= True)
    bpy.ops.object.join()

class PointInstance(NodeUtilityMixin):
  def __init__(self):
    self.post_process: NodeGroup = D.node_groups.get("Post_Surface")
    
  def create_asset(self):
    """Create node group assets """
    if not self.post_process:
        self.post_process, nodeIn, nodeOut = util.create_nodegroup_tree("Post_Surface", 'GeometryNodeTree')
        

    empty_obj = D.objects.get("Empty_OBJ")
    if not empty_obj:
        mesh = D.meshes.new('EmptyMesh')
        empty_obj = D.objects.new("Empty_OBJ", mesh)    
    
    process = D.node_groups.get("Process")
    if not process:
        process, processIn, processOut = util.create_nodegroup_tree("Process", 'GeometryNodeTree')
        self.node_tree = process

        instanceNode = self.create_nodes(
          'GeometryNodeInstanceOnPoints', location = (300,0), 
          mute = True
        )
        instanceNode.inputs[3].default_value = True


        rerouteNode = self.create_nodes('NodeReroute', 
          location = (280,-25)
        )

        self.connect_sockets(rerouteNode.inputs[0], in_process.outputs[0])
        self.connect_sockets(out_process.inputs[1],rerouteNode.outputs[0])
        self.connect_sockets(instanceNode.inputs[0],rerouteNode.outputs[0])
        self.connect_sockets(instanceNode.inputs[2],in_process.outputs[1])
        self.connect_sockets(out_process.inputs[0],instanceNode.outputs[0])
        self.connect_sockets(instanceNode.inputs[4],in_process.outputs[2])

        self.new_group_socket('NodeSocketInt', "Block Index")
        self.new_group_socket('NodeSocketInt', "Nbt Index")
    return process

  broke = []
  def create_nodegroup(self):
    """ Create a node group for instancing on the object"""
    chunks = self.chunks.get("chunks")
    block_instances = self.blocks.get("instance")
    mesh_instances = self.meshes.get("instance")
    node_groups = []
    
    for ic,chunk in enumerate(chunks):
        nodegroup_name = chunk.split('/')[1]
        instance = D.node_groups.get(nodegroup_name)
        if not instance:
            instance, in_instance, out_instance = util.create_nodegroup_tree(nodegroup_name, 'GeometryNodeTree')
            
            self.node_tree = instance
            frame_name = f"{chunk.split('/')[1]}_Blocks"
            frame_block = create_nodes(
              'NodeFrame', 
              name = frame_name, label = frame_name
            )
            join_block = self.create_nodes(
              'GeometryNodeJoinGeometry', location = (-200,-200), 
              name='Join Block Instances', label = "Join Block",
              parent = frame_block
            )
            
            i = 0                
            
        else:
            self.node_tree = instance
            join_block = instance.nodes.get("Join Block Instances")
            frame_block = instance.nodes.get(f"{nodegroup_name}'_Blocks")

        # Cleaning up object info node
        for node in instance.nodes:
            if node.type == 'OBJECT_INFO':
                instance.nodes.remove(node)
                
        i=0
        for block in reversed(block_instances[ic]):
            if block[0] == 0:
                name = mesh_instances[block[1].strip('/')]   
            else:
                name = f"{block[1].strip('/')}_merge"
            try:
                inst = D.objects.get(name)
            except:
                try:
                    inst = D.objects.get(f"{name}.001"]
                except:
                    inst = D.objects['Empty']
                    broke.append(name)

                
            block_node = self.create_nodes(
              'GeometryNodeObjectInfo', location = (-500,-500+i),
              name = inst.name, label = inst.name,
              parent = frame_block,
              hide = True
            )
            
            block_node.inputs[1].default_value = True
            
            self.connect_sockets(join_block.inputs[0],block_node.outputs[3])
            
            i += 50
            if inst.type == 'MESH':
                block_node.inputs[0].default_value = inst
        process_group = instance.nodes.get("Process")
        if not process_group:
            process_group = self.create_nodes(
              'GeometryNodeGroup', location =  (300,0)
              name = "Process",
              node_tree = process
            )

            self.connect_sockets(out_instance.inputs[0], process_group.outputs[0])
            self.connect_sockets(process_group.inputs[1], join_block.outputs[0])
            
            self.connect_sockets(process_group.inputs[0], in_instance.outputs[0])
            self.connect_sockets(process_group.inputs[2], in_instance.outputs[1])
            self.connect_sockets(process_group.inputs[3], in_instance.outputs[2])
            self.connect_sockets(process_group.inputs[4], in_instance.outputs[3])
        node_groups.append(instance)
    return node_groups

  def create_object(self):
    """Create the object and apply the point instancing node group"""
    meshes = self.meshes
    collection = self.collection
    for im,mesh in enumerate(meshes):
        
        obj = D.objects.get(mesh.name)
        if not obj:
            obj = D.objects.new(mesh.name, mesh)
            collection.objects.link(obj)
            # d = Matrix.Rotation(math.radians(90),4,'X')
            # obj.matrix_world = d
        
        if not obj.modifiers.get("Point Instancer"):
            mod = create_modifier(obj, 'NODES', 
              name = "Point Instancer", 
              node_group = node_groups[im],
              Input_2_use_attribute = True,
              Input_2_attribute_name = "instance_index",
              Input_3_use_attribute = True, 
              Input_3_attribute_name = "block_index",
              Input_4_use_attribute = True, 
              Input_4_attribute_name = "nbt_index"
            )
        else:
            pass

def create_modifier(obj, modifier_type, **attrs):
  mod = obj.modifiers.new(modifier_type.capitalize(), modifier_type)
  for k,v in attrs.items():
    if hasattr(mod, k):
      setattr(mod, k, v)
  
  return mod

### Operator
class MCU_Base:
  use_new_blocklib: BoolProperty(name="New blocklib instances collection")
  use_new_material: BoolProperty(name="New materials for blocks")
  disable_instance: BoolProperty(name="Disable Instances", default=True)
  
class MCU_OT_ImportWorld(bpy.types.Operator, ImportHelper, MCU_Base):
  """Main functionality of the addon"""
  bl_idname = "mcu.import_world"
  
  filepath  : StringProperty(name = 'Name',
      description = "File Path", subtype='DIR_PATH')
  filter_glob: StringProperty(default="*.usda", options={'HIDDEN'}, maxlen=255)
  
  filename_ext = '.usda'

  def invoke(self, context, event):
    wm = context.window_manager.fileselect_add(self)
    return {'RUNNING_MODAL'}
  
  def execute(self, context):
    if self.use_new_blocklib:
      pass
    return {'FINISHED'}

"""
class MCU_OT_UpdateChunk(bpy.types.Operator)
  \"""Update the chunk mesh with new data\"""
  
  def execute(self, context):
    print("TODO")
"""
    
classes = (
  MCU_OT_ImportWorld,
)

def register():
  for cls in classes:
    register_class(cls)
  
  
def unregister():
  for cls in reversed(classes):
    unregister_class(cls)
