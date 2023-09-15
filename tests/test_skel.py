from pathlib import Path
from mcskelanim import BedrockJSON, UsdRigWrite

import pytest

current = Path().cwd()
folder = current / "rig_output"
Path.mkdir(folder, exist_ok=True)

@pytest.fixture
def test_base_json() -> list:
  path = "https://raw.githubusercontent.com/Mojang/bedrock-samples/preview/resource_pack/models/entity/armor_stand.geo.json"
  json = BedrockJSON()
  return json.request_json(path)

def test_request(test_base_json: list):
  assert test_base_json != None

def test_result(test_base_json: list):
  rig = UsdRigWrite()
  rig.create_stage("rig_output/armor_stand.usda")
  rig.from_json(test_base_json)
  rig.output()
  rig.stage.Save()