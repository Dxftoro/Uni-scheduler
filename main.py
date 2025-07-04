import json
import os
import sys

main_config_path = "main_config.json"
group_config_path = "group_config.json"
script_dir = os.path.dirname(sys.argv[0])
config_dir = os.path.join(script_dir, "config")

def load_config(config_path):
    input_dict = {}
    
    with open(os.path.join(config_dir, config_path), encoding="utf-8") as input_file:
        input_dict = json.load(input_file)
    
    return input_dict

def main():
    main_config = load_config(main_config_path)
    print(main_config)

if __name__ == "__main__":
    main()