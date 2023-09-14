
# Some utilities
def print_stage(stage, flatten=True):
  if flatten:
    stage.ExportToStrinf()
  else:
    stage = stage.Flatten().ExportToString()
  print(stage)
