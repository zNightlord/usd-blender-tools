import bpy
import bmesh

from subprocess import check_output
from mathutils import Vector 

from bpy.types import (
	Object, Context, Image,
	Modifier, Nodes, Node, NodeTree,
	NodeReroute, NodeOutputs, NodeFrame
)

from bpy.app.handlers import persistent

import os
import inspect
import subprocess
import string
import re

import PyOpenColorIO as ocio # type: ignore

from .conf import *
from . import conf

def create_collection(name, parent = None, new = False):
  """Create new or get collection by name """
  if scn == None:
    scn = bpy.context.scene

  if not new:
    coll = bpy.data.collections.get(name)
    if not coll:
      coll = bpy.data.collections.new(name)
  else:
    coll = bpy.data.collections.new(name)
  if parent:
    parent.children.link(collection)
  else:
    scn = bpy.context.scene
    if not scn.collection.children.get(name)):
      scn.collection.children.link(coll)
  return coll

def moveto_collection(objects,collection):
    # Unlink objects in all collection, link it to new one 
    for obj in objects:
        for col in obj.users_collection:
            col.objects.unlink(obj) 
        collection.objects.link(obj)
  
def getobj_coll(obj):
  """Return the first collection of the objecf and collection list"""
  if obj == None:
    obj = bpy.context.object
  colls = obj.users_collection
  if colls[1]:
    return colls[0], colls
  else:
    return colls[0], None
  
  
def getcolls_vlayer(vlayer = None):
  
  if vlayer == None:
    vl_colls = bpy.context.view_layer.layer_collection.children
  else:
    vl_colls = vlayer.layer_collection.children
  
  return vl_colls
  

def create_assignMat(obj, name = "E"):
  # Get material
  mat = bpy.data.materials.get(name)
  if mat is None:
      # create material
      mat = bpy.data.materials.new(name= name)
  mat.use_nodes = True
  # Assign it to object
  if obj.data.materials:
      # assign to 1st material slot
      obj.data.materials[0] = mat
  else:
      # no slots
      obj.data.materials.append(mat)
  return mat
  
def check_object(context:Context = None, name:str = "") -> Object:
	"""Check if Scene profile is there"""
	if not context:
		context = bpy.context
	for ob in context.scene.objects:
		if ob.name.startswith(name):
			break
	return ob

def get_gn_modifier(obj:Object, name:str = "EFX_SceneProfile") -> Modifier:
	mod = obj.modifiers.get(name)
	try:
		if mod.type == 'NODES' and mod.node_group.name == name:
			return mod
	except:
		return None

  
#! Base on MCPrep code
def min_bv(version:tuple, *, inclusive=True) -> bool:
	if hasattr(bpy.app, "version"):
		if inclusive is False:
			return bpy.app.version > version
		return bpy.app.version >= version

def get_user_preferences(context:Context =None):
	"""Intermediate method for pre and post blender 2.8 grabbing preferences"""
	if not context:
		context = bpy.context
	prefs = None
	if hasattr(context, "user_preferences"):
		prefs = context.user_preferences.addons.get(__package__, None)
	elif hasattr(context, "preferences"):
		prefs = context.preferences.addons.get(__package__, None)
	if prefs:
		return prefs.preferences
	# To make the addon stable and non-exception prone, return None
	# raise Exception("Could not fetch user preferences")
	return None

def bv_350():
    return min_bv((3,5,0))

# Node Wrangler Util
def get_active_tree(context, compositor = True):
    tree = context.space_data.node_tree
    path = []
    # Get nodes from currently edited tree.
    # If user is editing a group, space_data.node_tree is still the base level (outside group).
    # context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
    # the same as context.active_node, the user is in a group.
    # Check recursively until we find the real active node_tree:
    
    # Directly use the compositor node tree
    # compositor = True
    if compositor:
      tree = context.scene.node_tree
      path.append(tree)
    else:
      if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree
            path.append(tree)
    
    return tree, path

def get_nodes_links(context):
    if type(context) is bpy.types.Context:
      tree, path = get_active_tree(context)
    else:
      tree, path = context, [context]
    return tree.nodes, tree.links

def get_nodes_frame(tree_nodes: Nodes, frame_node, name_) -> list:
    frames_nodes = []
    if type(frame_node) is str:
      frame_node = tree_nodes.get(frame_node)
    for n in tree_nodes:
        if n.parent == frame_node:
            frames_nodes += [n]
    return frames_nodes

def get_node_dim(node: NodeFrame, topleft = (0,0), bottomright = (0,0)): 
  topleft = (min(topleft[0], node.location.x), min(topleft[1], node.location.y))
  bottomright = (min(bottomright[0], node.location.x + node.dimensions.x), min(bottomright[1], node.location.y + node.dimensions.y))
  return topleft, bottomright
 
def connect_sockets(input, output):
  from bpy_extras import node_utils
  if hasattr(node_utils, "connect_sockets"):
    connect_sockets(input, output)
  else:
    node_tree = input.id_data.id_data
    node_tree.links.new(input, output)


def create_node(tree_nodes: Nodes, node_type :str, **attrs:dict[str, any]) -> Node:
	"""Create node with default attributes 
	Args:
		tree_nodes: the material node tree's nodes 
		node_type: the type of the node \n
		**attrs: set attributes if that node type has (eg: location, name, blend_type...)
		"node_tree" can be reference the nodegroup or the name of that nodegroup 
		"hide_sockets" to hide the sockets only display linked when need
	"""
	if node_type == 'ShaderNodeMixRGB': # MixRGB in 3.4
		if min_bv((3, 4, 0)):
			node = tree_nodes.new('ShaderNodeMix')
			node.data_type = 'RGBA'
		else:
			node = tree_nodes.new('ShaderNodeMixRGB')
	else:
		node = tree_nodes.new(node_type) 
	for attr, value in attrs.items():
		if hasattr(node, attr) and attr != 'node_tree':
			setattr(node, attr, value)
		elif attr == 'node_tree': #node group
			if not (value == "" or value == None):
				setattr(node, attr, bpy.data.node_groups[value] if type(value) is str else value)
		elif attr == 'hide_sockets': # option to hide socket for big node 
			try:
				node.inputs.foreach_set('hide', [value] * len(node.inputs))
				node.outputs.foreach_set('hide', [value] * len(node.outputs))
			except:
				pass
	# TODO Node automatic size
	# if hasattr(node,'node_tree'):
	# 	ng_name = node.node_tree.name
	# 	n_label = str(node.label)
	# 	len_name = len(ng_name)*30 if len(n_label) < len(ng_name) else len(n_label)*10
	# 	node.width = len_name	

	return node
	
def remove_node(nodes, node):
  if node is str:
    node = nodes.get(node)
  if not node:
    nodes.remove(node)
  

def switch_node(nodetree, node, to_type):
  nodes, links = get_nodes_links(nodetree)
  # Those types of nodes will not swap.
  src_excludes = ('NodeFrame')
  # Those attributes of nodes will be copied if possible
  attrs_to_pass = ('color', 'hide', 'label', 'mute', 'parent',
    'show_options', 'show_preview', 'show_texture',
    'use_alpha', 'use_clamp', 'use_custom_color', 'location'
  )
  n = node
  if n.rna_type.identifier not in src_excludes and n.rna_type.identifier != to_type:
    new_node = create_node(nodes, to_type)
    for attr in attrs_to_pass:
      if hasattr(node, attr) and hasattr(new_node, attr):
        setattr(new_node, attr, getattr(node, attr))
    return new_node
  
def create_node_aft(nodetree: NodeTree, node_type:str, name, active_node, socket = 0, **attrs):
  """Create node after add between the active node and linked connected node"""
  nodes, links = get_nodes_links(nodetree)
  try:
    output = active_node.outputs[socket]
  except:
    output = active_node.outputs[0]
  to_node = output.to_node
  
  i = 0
  for i,s in enumerate(to_node.inputs):
    if s.from_node == active_node:
      break
    
  nodeAft = create_node(nodes, node_type, location = active_node.location + Vector((100,0)),
    name = name, label = name)
  for v,k in attrs.items():
    if hasattr(nodeAft, k):
      setattr(nodeAft, k, v)
  
  links.new(output, nodeAft.inputs[0])
  links.new(nodeAft.outputs[0], to_node.inputs[i])
  
  return nodeAft
  
def create_from_nodegroup(tree_nodes: Nodes, node_group:str):
	"""Read the nodegroup nodes and their link 
	Recreate it in the tree_node layer above - Un-group the nodegroup"""
	tree_links = tree_nodes.links
	ng = tree_nodes[node_group]
	nt = ng.node_tree

	#loop through the nodes in the node group and copy the attribute as possible
	for node in nt.nodes:
		if not (node.type == 'GROUP_INPUT' or node.type =='GROUP_OUTPUT'):
			new_node = create_node(tree_nodes, node.bl_idname)
			for attr in dir(node):
				if not attr.startswith('__'):
					if attr == 'name':
						setattr(new_node, attr, '_' + getattr(node, attr)) # A way to look for name
					else:
						setattr(new_node, attr, getattr(node, attr))
			new_node.location += Vector(ng.location)
			for inp in node.inputs:
				new_node.inputs[inp.name].default_value = inp.default_value
		else: # Create reroute instead
			for inp in node.inputs:
				new_node = create_node(tree_nodes, NodeReroute.bl_idname, name = inp.name, location = Vector(node.location) + Vector(5,0))
			for outp in node.outputs:
				new_node = create_node(tree_nodes, NodeReroute.bl_idname, name = outp.name, location = Vector(node.location) + Vector(-5,0))

	for link in nt.links:
		fr_node = link.from_node
		to_node = link.to_node
		if not (fr_node.type == 'GROUP_INPUT' or to_node.type =='GROUP_OUTPUT'):
			for k,v in fr_node.outputs.items():
				if v == link.from_socket:
					keyOut = k
			for k,v in to_node.inputs.items():
				if v == link.to_socket:
					keyIn = k
			tree_links.new(tree_nodes.nodes['_' + fr_node.name].outputs[keyOut],tree_nodes.nodes['_' + to_node.name].inputs[keyIn])
		else:
			print(fr_node.outputs.items(),to_node.inputs.items())

	for node in tree_nodes.nodes:
		name = node.name
		if name.startwith('_'):
			setattr(node, attr, name.strip('_'))

def create_nodegroup_tree(name:str, type:str) -> NodeTree:
  if not type in ['CompositorNodeTree','GeometryNodeTree','ShaderNodeTree','TextureNodeTree']:
    return 
  node_tree = bpy.data.node_groups.get(name)
  if node_tree:
    node_tree = bpy.data.node_groups.get(name)
    nodeIn = node_tree.nodes.get("NodeGroupInput")
    nodeOut = node_tree.nodes.get("NodeGroupOutput")
    return node_tree, nodeIn , nodeOut

  node_tree = bpy.data.node_groups.new(name, type=type)
  nodes, links = get_nodes_links(node_tree)

  nodeIn = create_node(nodes,'NodeGroupInput', location= (-800,0), name = "NodeGroupInput", label = "NodeGroupInput")
  nodeOut = create_node(nodes,'NodeGroupOutput',location = (800,0), name = "NodeGroupOutput")
  socket = {
    'CompositorNodeTree':['NodeSocketColor','Image'],
    'GeometryNodeTree': ['NodeSocketGeometry','Geometry'],
    'ShaderNodeTree': ['NodeSocketShader','Shader'],
    'TextureNodeTree':['NodeSocketColor','Color']
    }


  sinput = node_tree.outputs.new(socket[type][0],socket[type][1])
  if type != "ShaderNodeTree":
    soutput = node_tree.inputs.new(socket[type][0],socket[type][1])
	

  return node_tree, nodeIn, nodeOut



def load_resource(path, node_type):
  nodegroup = []
  data = bpy.data
  node_group = data.node_groups.get(node_type)
  if not node_group or node_type in ["EFX_Curve", "EFX_ColorLGG"]:
    # try:
    with data.libraries.load(path) as (data_from, data_to):
      if data_from.node_groups:
        data_to.node_groups = [node_type]

      if data_to.node_groups:
        nodegroup = nodegroup.append(data_to.node_groups)
    # except OSError:
    #     return False #, None
  return True #, nodegroup
	

def load_nodetree_resources(effect_node, node_type):
	with bpy.data.libraries.load(conf.resourceBlend, link=False) as (data_from, data_to):
		if data_from.node_groups:
			data_to.node_groups = [node_type[0]]

		if data_to.node_groups:
			effect_node.node_tree = data_to.node_groups[0]

def read_directory(context):
	"""Use for reading preset directory"""
	try:
		preset_path = bpy.path.abspath(context.scene.efx.preset_path)
	except:
		preset_path = presetsFolder
	
	blends = [
		f for f in os.listdir(preset_path)
		if os.path.isfile(os.path.join(preset_path, f))
		and f.endswith(".blend")
		and not f.startswith(".")]
	nodegroup = []
	for blend_name in blends:
		blend_path = os.path.join(preset_path, blend_name)
		res = load_resource(blend_path, blend_name, "")
		return nodegroup

def nodegroup_append(directory:str, node_tree:str, newname:str):
	if not bpy.data.node_groups.get(node_tree):
		appendLink(directory, node_tree, False) # False in order to edit contents inside
		bpy.data.node_groups[node_tree].name = newname
		
def dupli_nodetree(nodetree):
  """Duplicate NodeTree"""
  duplicated = nodetree.copy()
  return duplicated


def create_relativeFolder(path = '', folder_name = 'render'):
  """Create render folder if not exist"""

  renderdir = os.path.join(bpy.path.abspath(path), folder_name)

  if not os.path.exists(renderdir):
    os.makedirs(renderdir)
  return renderdir
  
def relative_path(path = ''):
  """Get relative path of the blend file"""
  return bpy.path.abspath("//" if path == '' else path)

def get_path():
  """Get the addon path"""
  return os.path.dirname(os.path.realpath(__file__))

def get_name():
  """Get the addon name"""
  return os.path.basename(get_path())

def get_prefs():
  """Get the addon preferences"""
  addon = __package__ #get_name()
  return bpy.context.preferences.addons[addon].preferences 
    
  
def is_name_valid(text):
    """ Is name valid"""
    if text == '':
        return False
    digs = string.digits
    asci = string.ascii_letters
    symb = '_-() '    
    for i in text:
        if i not in (asci + digs + symb):
            return False        
    return True    
 
def is_path_exist(path):
  """Check if path exist"""
  return os.path.exists(path) and os.path.splitext(path)[-1].lower() == ".blend"

def split_components(fname):
    """Split name components"""       
    # Remove digits
    fname = ''.join(i for i in fname if not i.isdigit())
    # Separate CamelCase by space
    fname = re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>",fname)
    # Replace common separators with SPACE
    separators = ['_', '.', '-', '__', '--', '#']
    for sep in separators:
       fname = fname.replace(sep, ' ')

    components = fname.split(' ')
    components = [c.lower() for c in components]
    return components

def is_area(context: Context, type:str) -> list:
  items = []
  for area in context.screen.areas:
    if area.type == type:
      items.append(area)
  return items
