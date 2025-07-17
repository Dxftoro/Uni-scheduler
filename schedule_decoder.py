from entity_system import Space, IdDecoder

class ScheduleDecoder(IdDecoder):
    def __init__(self, main_config, global_space: Space, timeslots):
        self.main_config = main_config
        self.global_space = global_space
        self.timeslots = timeslots
    
    def decode(self):
        result = []
        day_per_week = len(self.main_config["week_days"])

        for group_id, group_timeslots in self.timeslots.items():
            group_timetable = {}
            group_timetable["group_name"] = self.global_space.get(group_id)

            for week_i in range(len(self.main_config["week_parity"])):
                week_name = self.main_config["week_parity"][week_i]
                group_timetable[week_name] = {}

                for day_i in range(week_i * day_per_week, (week_i * day_per_week) + day_per_week):
                    print(f"range {week_i} * {day_per_week}, ({week_i} * {day_per_week}) + {day_per_week}, day_i = {day_i}")
                    #index = day_i - (day_per_week * week_i)
                    day_name = self.main_config["week_days"][day_i - (day_per_week * week_i)]
                    group_timetable[week_name][day_name] = {}

                    for slot_i in range(len(group_timeslots[day_i])):
                        slot_name = self.main_config["class_times"][slot_i]

#                        print(group_timeslots[day_i][slot_i])
                        if isinstance(group_timeslots[day_i][slot_i], list):
                            class_name = self.global_space.get(group_timeslots[day_i][slot_i][0])
                            teacher_name = self.global_space.get(group_timeslots[day_i][slot_i][1])
                            room_name = self.global_space.get(group_timeslots[day_i][slot_i][2])
                            group_timetable[week_name][day_name][slot_name] = [class_name, teacher_name, room_name]
                        elif isinstance(group_timeslots[day_i][slot_i], int): pass
                        elif group_timeslots[day_i][slot_i] is None: 
                            group_timetable[week_name][day_name][slot_name] = "---"

            result.append(group_timetable)
        return result
