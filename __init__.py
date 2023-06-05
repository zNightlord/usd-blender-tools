bl_info = {
    "name": "MCUSD importer",
    "author": "Trung Phạm (zNight)",
    "version": (0, 0, 1),
    "blender": (3, 5, 0),
    "location": "View3D > N Panel",
    "description": "Import Mineways USD (usda) format",
    "warning": "",
    "doc_url": "",
    "category": "IO",
}

from .blender import io_usd_import
from .blender import io_usd_panel

def register():
  ...
  
def unregister():
  ...
