bl_info = {
    "name": "MCUSD importer",
    "author": "Trung Phạm (zNight)",
    "version": (0, 0, 1),
    "blender": (3, 5, 0),
    "location": "View3D > N Panel",
    "description": "Custom Mineways USD (usda) format imported",
    "warning": "",
    "doc_url": "",
    "category": "IO",
}

mcprep_info = {
  "name": "MCUSD importer"
}

from . import io_usd_import
from . import io_usd_ui

def register():
  io_usd_import.register()
  io_usd_ui.register()
  
def unregister():
  io_usd_import.register()
  io_usd_ui.register()
