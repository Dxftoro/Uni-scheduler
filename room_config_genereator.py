import os
import sys
import json
import random
import copy

script_dir = os.path.dirname(sys.argv[0])
config_dir = os.path.join(script_dir, "config")
generator_config_path = "generator_config.json"
main_config_path = "main_config.json"

def load_config(config_path):
    input_dict = {}
    
    with open(os.path.join(config_dir, config_path), encoding="utf-8") as input_file:
        input_dict = json.load(input_file)
    
    return input_dict

class Room:
    def __init__(self, name: str, type_list: list, tool_list: list):
        self.name = name
        self.type_list = type_list
        self.tool_list = tool_list

class RoomMaker:
    def __init__(self, room_config: dict):
        pass

def generate():
    pass

if __name__ == "__main__":
    generate()