import bpy
import numpy
import bmesh
import os
from pxr import Usd, UsdGeom   
D = bpy.data

effect = D.node_groups.new('Effect','GeometryNodeTree')
effect.inputs.new(type='NodeSocketGeometry',name='Geo')
out_effect= effect.nodes.new('NodeGroupOutput')
out_effect.location = (300,0)
in_effect = effect.nodes.new('NodeGroupInput')
    
def create_pt():
    mesh_name  = 'PT_' + chunk_name.split('/')[1]
    mesh = D.meshes.new(mesh_name)  # add the new mesh
    obj = D.objects.new(mesh.name, mesh)
    col = D.collections["Collection"]
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    me = bpy.context.object.data
    bm = bmesh.new()   
    bm.from_mesh(me)   
        
    l= bm.verts.layers.int.new("id")
    p= bm.verts.layers.int.new("blockid")
    for i,v in enumerate(pos):
        bm.verts.new(v)
        bm.verts.ensure_lookup_table()
        bm.verts[i][l] = id[i]
        bm.verts[i][p] = blockid_list[id[i]]
        
#    for v in bm.verts:
#        v[p] = bytes(f' Vert','utf-8')

    bm.to_mesh(me)
    bm.free()
    
    
    
    instance = D.node_groups.new(chunk_name.split('/')[1],'GeometryNodeTree')
    out_instance = instance.nodes.new('NodeGroupOutput')
    in_instance = instance.nodes.new('NodeGroupInput')
    
    out_instance.location = (500,0)

    instanceNode = instance.nodes.new('GeometryNodeInstanceOnPoints')
    instanceNode.inputs[3].default_value = True
    instanceNode.location = (300,0)
    
    instance.links.new(instanceNode.inputs[0],in_instance.outputs[0])
    instance.links.new(instanceNode.inputs[4],in_instance.outputs[1])
    
    
    
    

    join_block = instance.nodes.new('GeometryNodeJoinGeometry')
    join_block.location = (0,-200)
    frame_block = instance.nodes.new('NodeFrame')
    frame_block.name = chunk_name.split('/')[1]+'_Blocks'
    frame_block.label = frame_block.name
    join_block.parent = frame_block
#    out_block.location = (2-00,0)
#    blocks.links.new(out_block.inputs[0],join_block.outputs[0])
    
    i = 0                
    for block in reversed(block_instance):
        try:
            inst = D.objects[block.split('/')[1]]
        except:
            inst = D.objects[block.split('/')[1]+'.001']
            inst.name = inst.name.replace('.001','')
        print(inst)
        block_node = instance.nodes.new('GeometryNodeObjectInfo')
        block_node.name = inst.name
        block_node.label = inst.name
        block_node.hide = True
        block_node.location = (-200,-500+i)
        block_node.inputs[1].default_value = True
        block_node.parent = frame_block
        instance.links.new(join_block.inputs[0],block_node.outputs[3])
        i+=100
        if inst.type == 'MESH':
            block_node.inputs[0].default_value = inst
        else:
            merge_mesh = D.meshes.new(inst.name + '_merge')
            merge_obj = D.objects.new(merge_mesh.name, merge_mesh)
            col = inst.users_collection[0]
            bpy.ops.object.select_all(action='DESELECT')
            col.objects.link(merge_obj)
            bpy.context.view_layer.objects.active = merge_obj
            merge_obj.select_set(True)
            for children_mesh in inst.children:
                children_mesh.select_set(True)
            print(bpy.context.view_layer.objects.active)
            bpy.ops.object.join()
            merge_obj.name = inst.name
            merge_obj.parent = inst.parent
            D.objects.remove(inst,do_unlink=True)
            block_node.inputs[0].default_value = merge_obj
    
    effect_group = instance.nodes.new("GeometryNodeGroup")
    effect_group.node_tree = effect
    effect_group.location =  (300,200)
    effect.links.new(out_effect.inputs[0],in_effect.outputs[0])

    instance.links.new(effect_group.inputs[0],instanceNode.outputs[0])
    instance.links.new(out_instance.inputs[0],effect_group.outputs[0])
    instance.links.new(instanceNode.inputs[2],join_block.outputs[0])
    
    mod = obj.modifiers.new('Point Instancer','NODES')
    mod.node_group = instance
    mod["Input_1_use_attribute"] = True 
    mod["Input_1_attribute_name"] = "id"
    
         
   
filePath = 'D:\\Forge modding\\ModDev\\run\\saves\\modd 4\\mod.usda'
path = os.path.split(filePath)[0]
blocklibPath = path+'\\mod_materials\\BlockLibrary.usda'
mapPath = '/modd_4/VoxelMap'
blockPath = '/modd_4/VoxelMap/BlockLib'

bpy.ops.wm.usd_import(filepath=filePath,import_usd_preview=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name="Collection USD")
stage_ref = Usd.Stage.Open(filePath)

#prim_ref = stage_ref.GetPrimAtPath(mapPath + '/Chunk_P0P0P0')


blocklib = stage_ref.GetPrimAtPath(blockPath+'/Blocks')
voxel_ref = stage_ref.GetPrimAtPath(mapPath)
chunks = voxel_ref.GetChildren()

for chunk in chunks:
    chunk_name = str(chunk).split(str(mapPath))[1].split('>')[0]
    if 'Chunk' in chunk_name:
        print(' === '+chunk_name)
        
        chunk_ref = stage_ref.GetPrimAtPath(mapPath + chunk_name)
        pos = chunk_ref.GetAttribute('positions').Get()
        id = chunk_ref.GetAttribute('protoIndices').Get()
    
        rel = chunk_ref.GetRelationship('prototypes')
        blocks = rel.GetTargets()
        
        blockid_list = []
        block_list = []
        block_instance = []
        block_name = []
        for iblock,bl in enumerate(blocks):
            block = str(bl).split(blockPath+'/Blocks')[1]
            block_path = bl
            
            print(block_path)
            print(block + ' ' +str(iblock))
            blockid_list.append(int(block.split('_')[1].split('_')[0]))
            block_ref = stage_ref.GetPrimAtPath(block_path)
            child = block_ref.GetChildren()
            name = block_ref.GetAttribute('typeName').Get()
            block_name.append(name)
            
            grouped_block =[]
            for imesh,ch in enumerate(child):
                child_name = str(ch).split(str(block_path))[1].split('>')[0]
                child_path = str(block_path)+child_name

                print('mesh= ' + child_name)
                grouped_block.append(child_name)
                child_ref = stage_ref.GetPrimAtPath(child_path)
                mat_rel = child_ref.GetRelationship('material:binding')
                mat = mat_rel.GetTargets()
                
            if imesh != 0:
                block_list.append(grouped_block)
                block_instance.append(block)
            else:
                block_list.append(child_name)
                block_instance.append(child_name)
            
                for m in mat:
                    material = str(m).split('Looks')
                    material_path = blockPath+'/Blocks'+'/Looks'+material[1]
                    
                    material_ref = stage_ref.GetPrimAtPath(material_path+'/Shader')
                    print('material= '+ material[1])
        #            print(material_ref.GetPropertyNames())
                    diffuse = material_ref.GetProperty('inputs:diffuse_texture').Get()
                    print('texture= '+ str(diffuse).strip('@.').strip('@'))
                    print(' ')
                    
        dict = {blockid_list[i]: block_list[i] for i in range(len(blockid_list))}
        print(dict)
        print(block_instance)
        create_pt()
            
    
def fix_material():
    mats = bpy.data.materials
    for mat in mats:
        try:
            img = mat.node_tree.nodes["Image Texture"]
            img.interpolation = 'Closest'
        except:
            pass




#print(prim_ref.GetPropertyNames())


     
