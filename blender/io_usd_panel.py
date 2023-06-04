import bpy
from bl_ui.generic_ui_list import draw_ui_list

from .io_usd_import import MCU_OT_ImportWorld

class MCU_Instance_Block(bpy.types.PropertyGroup):
  """ Block info"""
  def update(self, context):
    obj = context.obj
    mods = context.modifiers
    mod = mods.get("MCU")
  
  block: bpy.types.PointerProperty(type=bpy.types.Object, update = update)
  block_id: bpy.props.IntProperty(name = "Block ID", default = 0)
  block_nbt_id: bpy.props.IntProperty(name = "Block NBT ID", default = 0)
  
  
class MCU_Instance_Object(bpy.types.PropertyGroup):
  blocks: bpy.types.CollectionProperty(type=MCU_Instance_Block)
  block_index: bpy.props.IntProperty(name = "Block Index")

class MCU_UL_OBJ(bpy.types.UIList):
    bl_idname = "MCU_UL_OBJ"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            obj = item.block

            row.prop(obj, "name", text="")
            

class MCU_PT_BASE_Panel(bpy.types.Panel):
    """Base scene panel"""
    bl_category = "MCUSD"
    bl_label = "MCUSD"
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
        if len(blocks):
          active_block = blocks[block_index]
          col.prop(active_block, "block")
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
  bpy.types.Object.minecraft_usd = bpy.types.PointerProperty(
    type=MCU_Instance_Object
  )
  
def unregister():
  del bpy.types.Object.minecraft_usd
  