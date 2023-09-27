import bpy
from bl_ui.generic_ui_list import draw_ui_list

from .io_usd_import import MCU_OT_ImportWorld

class MUC_InstanceBlock(bpy.types.PropertyGroup):
  """ Block info"""
  
  def update(self, context):
    obj = context.obj
    mods = context.modifiers
    mod = mods.get("Mineways Geometry Nodes")
    if mod:
      node_tree = mod.node_group
      if node_tree:
        nodes = node_tree.nodes
        
  
  block: bpy.types.PointerProperty(type=bpy.types.Object, update = update)
  block_id: bpy.props.IntProperty(name = "Block ID", default = 0)
  block_nbt_id: bpy.props.IntProperty(name = "Block NBT ID", default = 0)
  
  
class MUC_InstanceObject(bpy.types.PropertyGroup):
  blocks: bpy.types.CollectionProperty(type=MCU_Instance_Block)
  block_index: bpy.props.IntProperty(name = "Block Index")
  
  def add_block(self, block:Object, index: int, sub_index: int):
    item = self.blocks.add()
    item.block = block
    item.block_id = index
    item.block_nbt_id = sub_index
    return item
  
  def get_active_block(self):
    if self.blocks:
      return self.blocks[self.block_index]
  
  @classmethod
  def register(cls):
    bpy.types.Object.muc = PointerProperty(type=cls)
  
  @classmethod
  def unregister(cls):
    del bpy.types.Object.muc

class MUC_UL_OBJ(bpy.types.UIList):
    bl_idname = "MCU_UL_OBJ"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            obj = item.block
            row.prop(obj, "name", text="")
            

class MUC_PT_BASE_Panel(bpy.types.Panel):
    """Base scene panel"""
    bl_category = "USD"
    bl_label = "Mineways Chunker"
    bl_region_type = 'UI'

    def draw(self, context: Context):
        layout = self.layout
        obj = context.object
        usd = obj.minecraft_usd
        blocks = usd.blocks
        block_index = usd.block_index
        col = layout.column()
        ops = col.operator(MCU_OT_ImportWorld.bl_idname)
        
        layout = self.layout
        draw_ui_list(
            col,
            context,
            class_name=MCU_UL_OBJ.bl_idname,
            list_context_path="context.object.minecraft_usd.blocks",
            active_index_context_path="context.object.minecraft_usd.block_index"
        )
        if blocks:
          active_block = usd.get_active_block()
          col.prop(active_block, "block")
          col.prop(active_block, "block_id")
          col.prop(active_block, "block_sub_id")
          
          mats = active_block.block.data.materials
          box = col.box()
          for mat in mats:
            col = box.column()
            col.prop(mat, "name")

classes = (
  MCU_UL_OBJ,
  MCU_PT_BASE_Panel
)

def register():

  
def unregister():
  
  