#### Blender functions start here ####
def create_pts(paths,chunks,blocks):
    """Create points with attributes"""
    file_name = paths.get("file_name")  # file name
    ch = chunks.get("chunks")       # chunks
    points = chunks.get("points")       # points position
    indicies = chunks.get("indices")    # instance index
    id =  blocks.get("id")              # block index
    sub_id =  blocks.get("sub_id")      # block nbt index
    
    object_mesh = []
    for ic,chunk in enumerate(ch):
        mesh_name  = file_name+ ' - '+ 'PT_' +chunk.split('/')[1]
        if not bool(D.meshes.get(mesh_name)):
            mesh = D.meshes.new(mesh_name)  # add the new 
        else:
            mesh = D.meshes[mesh_name]
            D.meshes.remove(mesh,do_unlink=True) 
            mesh = D.meshes.new(mesh_name)
            
        a = np.array(points[ic])
        a[:,[1, 2]] = a[:,[2, 1]] #swaping Y and Z 
#        e = a
        verts = np.concatenate([np.array(i) for i in a])
        
    
        num_vertices = verts.shape[0] // 3    
        
        mesh.vertices.add(num_vertices)
        mesh.vertices.foreach_set("co", verts)
        
        ins = indicies[ic]
        blo = [id[ic][i] for i in ins]
        sub = [sub_id[ic][i] for i in ins]
        ins_index = mesh.vertex_layers_int.new(name="instance_index")
        blo_index = mesh.vertex_layers_int.new(name="block_index")
        nbt_index = mesh.vertex_layers_int.new(name="nbt_index")
        ins_index.data.foreach_set("value", ins)
        blo_index.data.foreach_set("value", blo)
        nbt_index.data.foreach_set("value", sub)
        
        vertices = np.zeros(len(mesh.vertices) * 3,dtype=np.int32)
        mesh.vertices.foreach_get("co", vertices)
        vertices = vertices.reshape(-1,3)

        bm = bmesh.new()   
        bm.from_mesh(mesh)   
        
#        l= bm.verts.layers.int.new("instance_index")
#        p= bm.verts.layers.int.new("block_index")
#        n= bm.verts.layers.int.new("nbt_index")

        # print(a)
#        for ip,point in a:
#            print(point)
#            v1 = bm.verts.new(point)
#            bm.verts.ensure_lookup_table()
#            bm.verts[ip][l] = indicies[ip]
#            bm.verts[ip][p] = id[indicies[ip]]
#            bm.verts[ip][n] = sub_id[indicies[ip]]
#            for v2 in bm.verts:
#                diff = abs(v1.co[0] - v2.co[0]) + abs(v1.co[1] - v2.co[1]) + abs(v1.co[2] - v2.co[2])
#                if diff == 1 and not v1 == v2:
#                    e = bm.edges.new([v1, v2])

        bm.to_mesh(mesh)
        bm.free()
        
        mesh.update()
        mesh.validate()
        
        object_mesh.append(mesh)
    return object_mesh

def create_collection(name,parent = None):
    #Create collection, if exist get it.
    if not bool(D.collections.get(name)):
        collection =  D.collections.new(name)
        if parent != None:
            parent.children.link(collection)
        else:
            C.scene.collection.children.link(collection)
    else:
        collection = D.collections[name]
    return collection

def moveto_collection(objects,collection):
    # Unlink objects in all collection, link it to new one 
    for obj in objects:
        for col in obj.users_collection:
            col.objects.unlink(obj) 
        collection.objects.link(obj)

def create_usd_collection(paths):
    """ Create collection to store usd and fix merged blocks
    Example: Grass Block is Block_2_0 need to merge all meshes
    dirt,grass_block_side,grass_block_top into one """
    # Create the USD collections
    collections = []
    file_name = paths.get("file_name")
    world_name = paths.get("world_name")
    
    usd_col = create_collection(file_name + " USD Collection")
    pt_col = create_collection(file_name + " USD Points",usd_col)
    block_col = create_collection(file_name + " USD BlockLib",usd_col)
    
    collections.append([usd_col,pt_col,block_col])
    
    if not bool(D.objects.get(file_name +' Blocks')):
        bpy.ops.wm.usd_import(filepath=filePath,import_usd_preview=True)
        
        objs = C.selected_objects
        moveto_collection(objs,block_col)
    
        #Fix all the block merge and apply 
        block_objs = block_col.objects['Blocks'].children_recursive
        rot = Matrix.Rotation(math.radians(90),4,'X')
        loc = Matrix.Translation((-0.5,-0.5,-0.5))
        
        path = ['Looks','Blocks','VoxelMap',world_name.replace(' ','_')]

        if D.objects[path[2]]:
            for child in D.objects[path[2]].children_recursive:
                D.objects.remove(child,do_unlink=True)
            D.objects.remove(D.objects[path[2]],do_unlink=True)
        for obj in D.objects:
            if obj.name in path and not 'Block' in obj.name:
                for child in obj.children_recursive:
                    child.name = file_name + ' '+ child.name
                obj.name =  file_name + ' '+obj.name
        if bool(D.objects.get('Blocks')):
            obj = D.objects['Blocks']  
            obj.name =  file_name + ' '+obj.name

        new_i = 0
        row = 0
        column = 0
        for i,obj in enumerate(block_objs):
        
            pre_loc = Matrix.Translation((row,-2,column))
            try:
                if obj.type != 'MESH' and 'Block' in obj.name:
                    merge_mesh = D.meshes.new(obj.name + '_merge')
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
                    
                    D.objects.remove(obj,do_unlink=True)                
                    bpy.ops.object.join()
                    
                    ma = rot @ loc
                    me = merge_obj.data
                    me.transform(ma)
                    
                    merge_obj.matrix_world = pre_loc
                elif obj.type == 'MESH':
                    
                    ma = rot @ loc
                    me = obj.data
                    me.transform(ma)
                    
                    obj.matrix_world = pre_loc
            except: # Except broken cause by previous merge RNA blocks
                new_i-=1
                pass
            new_i+=1
            row = new_i % 16
            column = math.floor(new_i / 16)
        fix_material(D.materials)
    return collections

def create_asset():
    """Create node group assets """
    if not bool(D.node_groups.get("Post_Surface")):
        surface = D.node_groups.new('Post_Surface','GeometryNodeTree')
        surface.inputs.new(type='NodeSocketGeometry',name='Geometry')
        surface.outputs.new(type='NodeSocketGeometry',name='Geometry')

    if not bool(D.objects.get('Empty')):
        mesh = D.meshes.new('EmptyMesh')
        D.objects.new('Empty',mesh)    

    if not bool(D.node_groups.get("Process")):
        process = D.node_groups.new('Process','GeometryNodeTree')
        process.inputs.new(type='NodeSocketGeometry',name='Geometry')
        process.outputs.new(type='NodeSocketGeometry',name='Instances')
        process.outputs.new(type='NodeSocketGeometry',name='Geometry')
        out_process= process.nodes.new('NodeGroupOutput')

        out_process.location = (800,0)

        in_process = process.nodes.new('NodeGroupInput')

        instanceNode = process.nodes.new('GeometryNodeInstanceOnPoints')
        instanceNode.inputs[3].default_value = True
        instanceNode.location = (300,0)
        instanceNode.mute = True

        rerouteNode = process.nodes.new('NodeReroute')
        rerouteNode.location = (280,-25)

        process.links.new(rerouteNode.inputs[0],in_process.outputs[0])
        process.links.new(out_process.inputs[1],rerouteNode.outputs[0])
        process.links.new(instanceNode.inputs[0],rerouteNode.outputs[0])
        process.links.new(instanceNode.inputs[2],in_process.outputs[1])
        process.links.new(out_process.inputs[0],instanceNode.outputs[0])
        process.links.new(instanceNode.inputs[4],in_process.outputs[2])

        process.inputs.new(type='NodeSocketInt',name='Block Index')
        process.inputs.new(type='NodeSocketInt',name='Nbt Index')
        
    else:
        process = D.node_groups["Process"]
    return process
broke = []
def create_nodegroup(chunks,blocks):
    """ Create a node group for instancing on the object"""
    chunks = chunks.get("chunks")
    block_instances = blocks.get("instance")
    mesh_instances = meshes.get("instance")
    node_groups = []
    for ic,chunk in enumerate(chunks):
        nodegroup_name = chunk.split('/')[1]
        if not bool(D.node_groups.get(nodegroup_name)):
            instance = D.node_groups.new(chunk.split('/')[1],'GeometryNodeTree')
            out_instance = instance.nodes.new('NodeGroupOutput')
            in_instance = instance.nodes.new('NodeGroupInput')
            instance.inputs.new(type='NodeSocketGeometry',name='Geometry')
            
            out_instance.location = (800,0)
            join_block = instance.nodes.new('GeometryNodeJoinGeometry')
            join_block.name='Join Block Instances'
            join_block.location = (-200,-200)
            frame_block = instance.nodes.new('NodeFrame')
            frame_block.name = chunk.split('/')[1]+'_Blocks'
            frame_block.label = frame_block.name
            join_block.parent = frame_block
            i = 0                
            
        else:
            instance = D.node_groups[nodegroup_name]
            join_block = instance.nodes['Join Block Instances']
            frame_block = instance.nodes[nodegroup_name+'_Blocks']

        for node in instance.nodes:
            if node.type == 'OBJECT_INFO':
                instance.nodes.remove(node)
        i=0
        for block in reversed(block_instances[ic]):
            if block[0] == 0:
                name = mesh_instances[block[1].strip('/')]   
            else:
                name = block[1].strip('/') + "_merge"
            try:
                inst = D.objects[name]
            except:
                try:
                    inst = D.objects[name+'.001']
                except:
                    inst = D.objects['Empty']
                    broke.append(name)

                
            block_node = instance.nodes.new('GeometryNodeObjectInfo')
            block_node.name = inst.name
            block_node.label = inst.name
            block_node.hide = True
            block_node.location = (-500,-500+i)
            block_node.inputs[1].default_value = True
            block_node.parent = frame_block
            instance.links.new(join_block.inputs[0],block_node.outputs[3])
            i+=50
            if inst.type == 'MESH':
                block_node.inputs[0].default_value = inst
        
        if not bool(instance.nodes.get("Process")):
            process_group = instance.nodes.new("GeometryNodeGroup")
            process_group.name = "Process"
            process_group.node_tree = process
            process_group.location =  (300,0)
        
            instance.links.new(out_instance.inputs[0],process_group.outputs[0])
            instance.links.new(process_group.inputs[1],join_block.outputs[0])
            
            instance.links.new(process_group.inputs[0],in_instance.outputs[0])
            instance.links.new(process_group.inputs[2],in_instance.outputs[1])
            instance.links.new(process_group.inputs[3],in_instance.outputs[2])
            instance.links.new(process_group.inputs[4],in_instance.outputs[3])
        node_groups.append(instance)
    return node_groups

def create_object(meshes,collection):
    """Create the object and apply the point instancing node group"""
    for im,mesh in enumerate(meshes):
        object_name  = mesh.name
        if not bool(D.objects.get(mesh.name)):
            obj = D.objects.new(mesh.name, mesh)
            collection.objects.link(obj)
            # d = Matrix.Rotation(math.radians(90),4,'X')
            # obj.matrix_world = d
        else:
            obj = D.objects[object_name]
#        print(instances[im])
        if not bool(obj.modifiers.get("Point Instancer")):
            mod = obj.modifiers.new('Point Instancer','NODES')
            
            mod.node_group = node_groups[im]
            mod["Input_2_use_attribute"] = True 
            mod["Input_2_attribute_name"] = "instance_index"
            mod["Input_3_use_attribute"] = True 
            mod["Input_3_attribute_name"] = "block_index"
            mod["Input_4_use_attribute"] = True 
            mod["Input_4_attribute_name"] = "nbt_index"
        else:
            pass

def lprint(list):
    for l in list:
        print(l)

def fix_material(materials):
    for mat in materials:
        try:
            img = mat.node_tree.nodes["Image Texture"]
            img.interpolation = 'Closest'
        except:
            pass

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