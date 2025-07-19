from flask import Flask, render_template, request

schedule_model = None
global_space = None
timetables = None

app = Flask(__name__, template_folder="./pages")
def run_flask_app():
    app.run(use_reloader=False, debug=False, host="0.0.0.0", port=5000)

@app.route("/debug", methods=["post", "get"])
def render_debug_schedules():
    global schedule_model

    timeslots = schedule_model.get_group_timeslots()
    room_timeslots = schedule_model.get_room_timeslots()
    states = schedule_model.get_teacher_states()
    message_log = schedule_model.get_message_log()

    return render_template("debug.html", 
        timeslots=timeslots,
        room_timeslots=room_timeslots,
        states=states, 
        message_log=message_log,
        message_log_len=len(message_log))

@app.route("/space")
def render_global_space():
    entities = global_space.get_entities()
    entity_list_len = len(entities)
    return render_template("space.html", entities=entities, entity_list_len=entity_list_len)

@app.route("/", methods=["get"])
def render_index():
    global timetables
    timetable_count = len(timetables)

    page_index = request.args.get("page")
    if page_index is None: page_index = 0
    else:
        try: page_index = int(page_index)
        except: page_index = 0

    if page_index < 0 or page_index >= timetable_count:
        page_index = 0

    return render_template(
        "index.html", 
        timetable=timetables[page_index], 
        page_index=page_index,
        timetable_count=timetable_count)