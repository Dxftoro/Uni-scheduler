import json
import os
import sys
from datetime import datetime
from schedudle_model import ScheduleModel, TeacherState
from entity_system import Space
from schedule_decoder import ScheduleDecoder
from flask import Flask
import flask_routes

main_config_path = "main_config.json"
group_config_path = "group_config.json"
room_config_path = "room_config.json"
timepref_config_path = "group_timeprefs.json"

script_dir = os.path.dirname(sys.argv[0])
config_dir = os.path.join(script_dir, "config")
output_dir = os.path.join(script_dir, "output")

schedule_model = None
global_space = Space()

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

def build_schedule(schedule_model: ScheduleModel):
    iterations = 0
    while not schedule_model.schedule_ready():
        schedule_model.step()
        iterations += 1
    
    owned_class_count = schedule_model.owned_class_count()
    failed_solution_count = schedule_model.failed_count()
    completed_solution_count = schedule_model.completed_count()
    completed_percent = f"{((completed_solution_count / owned_class_count) * 100):.2f}"
    failed_percent = f"{((failed_solution_count / owned_class_count) * 100):.2f}"

    print(f"Iteration count: {iterations}\n")
    print(f"Owned class count: {owned_class_count}")
    print(f"Completed solutions: {completed_percent}% ({completed_solution_count})")
    print(f"Failed solutions: {failed_percent}% ({failed_solution_count})\n")

def save_timetable(output_dir: str, timetable):
    current_time = datetime.now().strftime("%d-%m-%Y_%H%M%S-%f")

    with open(os.path.join(output_dir, f"timetable_{current_time}.json"), "w", encoding = "utf-8") as timetable_file:
        json.dump(timetable, timetable_file, indent=4, ensure_ascii=False)

def main():
    global schedule_model
    global global_space

    main_config = load_config(main_config_path)
    group_config = load_config(group_config_path)
    room_config = load_config(room_config_path)
    timepref_config = load_config(timepref_config_path)

    week_day_count = len(main_config["week_days"])
    week_parity = len(main_config["week_parity"])
    period_size = week_day_count * week_parity
    empty_timeslots = {
        "class_min_count": main_config["class_min_count"],
        "timeslots": make_timeslots(period_size, main_config["class_max_count"])
    }

    model_config = {"group_config": group_config, "room_config": room_config, "timepref_config": timepref_config}
    schedule_model = ScheduleModel(empty_timeslots, week_parity, model_config, global_space)
    
    print("Building schedule...")
    build_schedule(schedule_model)

    decoder = ScheduleDecoder(main_config, global_space, schedule_model.get_group_timeslots())
    timetables = decoder.decode()
    #save_timetable(output_dir, timetables)

    flask_routes.global_space = global_space
    flask_routes.schedule_model = schedule_model
    flask_routes.timetables = timetables
    flask_routes.run_flask_app()

if __name__ == "__main__":
    main()