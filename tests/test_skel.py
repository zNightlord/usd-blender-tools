import requests

from mcskelanim import BedrockJSON

import pytest

def test_request():
  path = "https://raw.githubusercontent.com/Mojang/bedrock-samples/preview/resource_pack/models/entity/armor_stand.geo.json"
  json = BedrockJSON()
  print(json.request_json(path))
