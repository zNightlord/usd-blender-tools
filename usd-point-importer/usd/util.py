from pxr import UsdGeom

def stage_set_axis(stage, axis):
  if axis == 'Z':
    axis = UsdGeom.Tokens.z
  elif axis == 'Y':
    axis == UsdGeom.Tokens.y
  if isinstance(axis, UsdGeom.Tokens):
    UsdGeom.UsdGeomSetStageUpAxis(stage, axis)

def stage_get_axis(stage):
  return 'Z' if UsdGeomGetStageUpAxis(stage) == UsdGeom.Tokens.z else 'Y'
  
def has_prim_type(prim_type):
  has_type = False
  for x in stage.Traverse():
    if x.IsA(prim_type) # UsdGeom.Mesh
      has_type = True
      break
  return has_type
