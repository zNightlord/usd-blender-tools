bl_info = {
    "name": "VoxelDraw",
    "author": "Sreeraj R",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "View3D > Edit Mode > Toolbar",
    "description": "Draw Voxel mesh in Edit Mode",
    "warning": "Made purely for fun, don't expect stuff to work ;)",
    "doc_url": "",
    "category": "Add Mesh",
}

from .blender import io_usd_import
from .blender import io_usd_panel

