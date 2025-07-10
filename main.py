import json
import os
import sys
import threading
from schedudle_model import ScheduleModel
from entity_system import Space
from flask import Flask, render_template, request

main_config_path = "main_config.json"
group_config_path = "group_config.json"
script_dir = os.path.dirname(sys.argv[0])
config_dir = os.path.join(script_dir, "config")

schedule_model = None
key = ""

app = Flask(__name__, template_folder="./pages")
def run_flask_app():
    app.run(use_reloader=False, debug=True, host="0.0.0.0", port=5000)

def shutdown_server():
    # This function is specific to the Werkzeug development server
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route("/", methods=["post", "get"])
def render_schedules():
    global schedule_model

    if request.method == "POST":
        print("-----------------> STEP <-----------------")
        schedule_model.step()

    timeslots = schedule_model.get_group_timeslots()
    states = schedule_model.get_teacher_states()
    message = ""

    for group_id, slots in timeslots.items():
        message += str(group_id) + ":\n"
        for row in slots:
            message += str(row) + "\n"
        message += "\n\n"

    for state in states:
        message += state.name + "\n"

    return render_template("index.html", timeslots=timeslots, states=states, message=message)

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
    global schedule_model
    global key

    main_config = load_config(main_config_path)
    group_config = load_config(group_config_path)

    week_day_count = len(main_config["week_days"])
    week_parity = len(main_config["week_parity"])
    period_size = week_day_count * week_parity
    empty_timeslots = make_timeslots(period_size, main_config["class_max_count"])

    global_space = Space()
    schedule_model = ScheduleModel(empty_timeslots, group_config, global_space)
    
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    try:
        while key != "e":
            key = str(input("-----------------> STEP <-----------------"))
            schedule_model.step()
    except Exception as exc:
        print(exc)
        #shutdown_server()
    flask_thread.join()

if __name__ == "__main__":
    main()