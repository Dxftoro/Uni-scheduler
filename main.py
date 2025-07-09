import json
import os
import sys
from schedudle_model import ScheduleModel
from entity_system import Space

main_config_path = "main_config.json"
group_config_path = "group_config.json"
script_dir = os.path.dirname(sys.argv[0])
config_dir = os.path.join(script_dir, "config")

def load_config(config_path: str) -> dict:
    input_dict = {}
    
    with open(os.path.join(config_dir, config_path), encoding="utf-8") as input_file:
        input_dict = json.load(input_file)
    
    return input_dict

def make_timeslots(day_count, class_count):
    timeslots = []
    for i in range(day_count):
        day = [None for _ in range(class_count)]
        timeslots.append(day)
    return timeslots

def main():
    main_config = load_config(main_config_path)
    group_config = load_config(group_config_path)

    week_day_count = len(main_config["week_days"])
    week_parity = len(main_config["week_parity"])
    period_size = week_day_count * week_parity
    empty_timeslots = make_timeslots(period_size, main_config["class_max_count"])

    global_space = Space()
    model = ScheduleModel(empty_timeslots, group_config, global_space)

if __name__ == "__main__":
    main()