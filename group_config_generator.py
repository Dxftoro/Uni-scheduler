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

class Class:
    def __init__(self, name: str, class_type: str, min_class_times: int, max_class_times: int, priority: float):
        self.name = name
        self.class_type = class_type
        self.class_tools = []
        self.times = ()
        self.priority = priority
        self.__make_times(random.randint(min_class_times, max_class_times))
    
    def __make_times(self, max_times: int):
        first_time = max_times - random.randint(0, max_times)
        second_time = max_times - first_time
        self.times = (first_time, second_time)
    
    def set_tools(self, tool_list: list):
        self.class_tools = tool_list

    def get_name(self):
        return self.name
    
    def get_type(self):
        return self.class_type
    
    def get_times(self):
        return self.times

    def get_tools(self):
        return self.class_tools

    def get_priority(self):
        return self.priority

class ClassMaker:
    def _choose_tools(self) -> list:
        choice_num = random.randint(1, 100)

        if choice_num <= 50:
            return [random.choice(self.possible_tools)]

        elif choice_num > 50 and choice_num <= 90:
            return []

        elif choice_num > 90:
            tool_set = set()
            tool_remaining = self.max_tool_count

            while tool_remaining > 0:
                tool_set.add(random.choice(self.possible_tools))
                tool_remaining -= 1

            return list(tool_set)

    def __init__(self, class_type_list: list, tool_list: list, max_tool_count: int):
        self.class_tools = {}
        self.types = class_type_list
        self.possible_tools = tool_list
        self.max_tool_count = max_tool_count

    def make_class_set(self, name: str, min_class_times, max_class_times):
        class_set = []
        class_priority = random.random()
        for type in self.types:
            new_class = Class(name + ", " + type, type, min_class_times, max_class_times, class_priority)
            class_set.append(new_class)

            if new_class.get_name() in self.class_tools:
                new_class.set_tools(self.class_tools[new_class.get_name()])
            else:
                if new_class.get_type() == "лек.":
                    self.class_tools[new_class.get_name()] = random.choice([["Проектор"], []])
                else:
                    self.class_tools[new_class.get_name()] = self._choose_tools()
                new_class.set_tools(self.class_tools[new_class.get_name()])

        return class_set

    def get_class_tools(self):
        return self.class_tools
    
class Teacher:
    def __init__(self, name: str, class_count: int, class_list: list):
        self.name = name

    def get_name(self):
        return self.name
    
    def get_class_list(self):
        return self.name

class TeacherMaker:
    def __init__(self, class_list):
        self.class_list = class_list
    
    def make_teacher(self, teacher_name, class_count):
        if len(self.class_list) == 0:
            return None

        classes_left = class_count
        teacher_class_list = []

        while classes_left > 0 or len(self.class_list) > 0:
            choosen_class_index = random.randint(0, len(self.class_list) - 1)
            choosen_class = self.class_list[choosen_class_index]
            self.class_list.pop(choosen_class_index)

            teacher_class_list.append(choosen_class)
            classes_left -= 1
        
        return Teacher(teacher_name, teacher_class_list)

def generate_group_timepref(day_count, max_class_times):
    timeprefs = []
    for i in range(day_count):
        day = [random.random() for _ in range(max_class_times)]
        timeprefs.append(day)
    return timeprefs

def generate_classes(group_names, class_count, generator_config):
    main_config = load_config(main_config_path)
    day_count = len(main_config["week_days"]) * len(main_config["week_parity"])

    #class_name_list = generator_config["classes"]
    teacher_name_list = generator_config["teachers"]
    class_type_list = generator_config["class_types"]
    tool_list = generator_config["tools"]
    max_tool_count = generator_config["max_tool_count"]
    min_class_times = generator_config["min_class_times"]
    max_class_times = generator_config["max_class_times"]
    
    class_maker = ClassMaker(class_type_list, tool_list, max_tool_count)
    group_dict = {}
    group_timeprefs = {}
    for group_name in group_names:
        class_name_list = copy.deepcopy(generator_config["classes"])
        group_timeprefs[group_name] = generate_group_timepref(day_count, max_class_times)

        for i in range(class_count):
            #print(len(class_name_list) - 1)
            choosen_class_index = random.randint(0, len(class_name_list) - 1)
            choosen_class_name = class_name_list[choosen_class_index]
            class_name_list.pop(choosen_class_index)

            class_set = class_maker.make_class_set(choosen_class_name, min_class_times, max_class_times)
            for _class in class_set:
                if group_name not in group_dict:
                    group_dict[group_name] = {}
                
                if _class.get_name() not in group_dict[group_name]:
                    group_dict[group_name][_class.get_name()] = {}

                group_dict[group_name][_class.get_name()]["class_type"] = _class.get_type()
                group_dict[group_name][_class.get_name()]["times"] = _class.get_times()
                group_dict[group_name][_class.get_name()]["teacher"] = random.choice(teacher_name_list)
                group_dict[group_name][_class.get_name()]["tools"] = _class.get_tools()
                group_dict[group_name][_class.get_name()]["priority"] = _class.get_priority()

    print(class_maker.get_class_tools())
    return [group_dict, group_timeprefs]

def generate():
    generator_config = load_config(generator_config_path)
    #group_list = generator_config["groups"]
    group_list = []

    for i in range(3):
        group_list.append(generator_config["groups"][i])

    generated = generate_classes(group_list, 7, generator_config)
    group_dict = generated[0]
    group_timeprefs = generated[1]
    
    with open(os.path.join(config_dir, "group_config.json"), "w", encoding = "utf-8") as group_config_file:
        json.dump(group_dict, group_config_file, indent=4, ensure_ascii=False)
    
    with open(os.path.join(config_dir, "group_timeprefs.json"), "w", encoding = "utf-8") as group_config_file:
        json.dump(group_timeprefs, group_config_file, indent=4, ensure_ascii=False)

    #group_config = {}
    #for group in group_list:

if __name__ == "__main__":
    generate()