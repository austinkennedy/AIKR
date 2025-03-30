import yaml
import os

def load_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def make_dir(path):
    #check if directory in path exists, if not create it
    if not os.path.exists(path):
        os.makedirs(path)