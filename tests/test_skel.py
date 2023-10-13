from pathlib import Path
from mcskelanim import BedrockJSON, UsdRigWrite

import pytest

current = Path().cwd()
folder = current / "rig_output"
Path.mkdir(folder, exist_ok=True)

geom_url = "https://raw.githubusercontent.com/Mojang/bedrock-samples/preview/resource_pack/models/entity/"
anim_url = "https://raw.githubusercontent.com/Mojang/bedrock-samples/preview/resource_pack/animations/"

@pytest.fixture
def test_base_geom() -> list:
  path = geom_url+"armor_stand.geo.json"
  json = BedrockJSON()
  return json.request_json(path)

@pytest.fixture
def test_base_anim_pose() -> dict:
  path = anim_url+"armor_stand.animation.json"
  json = BedrockJSON()
  return json.request_json(path)

@pytest.fixture
def test_base_skel(test_base_geom: list) -> UsdRigWrite:
  rig = UsdRigWrite()
  rig.create_stage("rig_output/armor_stand.usda")
  rig.from_json(test_base_geom)
  return rig
  
def test_request(test_base_geom: list):
  assert test_base_geom != None 

def test_result(test_base_skel: UsdRigWrite):
  rig = test_base_skel
  # rig.output()
  rig.stage.Save()
  UsdRigWrite.zip("rig_output/armor_stand.usda", "rig_output/armor_stand.usdz")
  

def test_anim_pose(test_base_skel: UsdRigWrite, test_base_anim_pose: dict):
  rig = test_base_skel
  print("\n", "Pose:")
  rig.anim_from_json(test_base_anim_pose, limit=1)
  rig.output()

def test_anim_anim():
  path_geo = geom_url+"phantom.geo.json"
  path_anim = anim_url+"phantom.animation.json"
  json = BedrockJSON()
  bones = json.request_json(path_geo)
  anims = json.request_json(path_anim)
  rig = UsdRigWrite()
  rig.create_stage("rig_output/phantom.usda")
  rig.from_json(bones)
  rig.stage.Save()
  UsdRigWrite.zip("rig_output/phantom.usda", "rig_output/phantom.usdz")
  rig.anim_from_json(anims)
  rig.output()
  print("Hard part.")

def test_chicken():
  path_geo = geom_url+"chicken.geo.json"
  path_anim = anim_url+"chicken.animation.json"
  json = BedrockJSON()
  bones = json.request_json(path_geo)
  anims = json.request_json(path_anim)
  rig = UsdRigWrite()
  rig.create_stage("rig_output/chicken.usda")
  rig.from_json(bones)
  rig.stage.Save()
  UsdRigWrite.zip("rig_output/chicken.usda", "rig_output/chicken.usdz")
  rig.anim_from_json(anims)
  rig.output()
