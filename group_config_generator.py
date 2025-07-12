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
    def __init__(self, name: str, class_type: str, min_class_times: int, max_class_times: int):
        self.name = name
        self.class_type = class_type
        self.times = ()
        self.__make_times(random.randint(min_class_times, max_class_times))
    
    def __make_times(self, max_times: int):
        first_time = max_times - random.randint(0, max_times)
        second_time = max_times - first_time
        self.times = (first_time, second_time)
    
    def get_name(self):
        return self.name
    
    def get_class_type(self):
        return self.class_type
    
    def get_times(self):
        return self.times

    @staticmethod
    def make_class_set(name: str, types: list, min_class_times, max_class_times):
        class_set = []
        for type in types:
            class_set.append(Class(name + ", " + type, type, min_class_times, max_class_times))
        return class_set

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

def generate_classes(group_names, class_count, generator_config):
    #class_name_list = generator_config["classes"]
    teacher_name_list = generator_config["teachers"]
    class_type_list = generator_config["class_types"]
    min_class_times = generator_config["min_class_times"]
    max_class_times = generator_config["max_class_times"]
    
    group_dict = {}
    for group_name in group_names:
        class_name_list = copy.deepcopy(generator_config["classes"])
        for i in range(class_count):
            print(len(class_name_list) - 1)
            choosen_class_index = random.randint(0, len(class_name_list) - 1)
            choosen_class_name = class_name_list[choosen_class_index]
            class_name_list.pop(choosen_class_index)

            class_set = Class.make_class_set(choosen_class_name, class_type_list, min_class_times, max_class_times)
            for _class in class_set:
                if group_name not in group_dict:
                    group_dict[group_name] = {}
                
                if _class.get_name() not in group_dict[group_name]:
                    group_dict[group_name][_class.get_name()] = {}

                group_dict[group_name][_class.get_name()]["class_type"] = _class.get_class_type()
                group_dict[group_name][_class.get_name()]["times"] = _class.get_times()
                group_dict[group_name][_class.get_name()]["teacher"] = random.choice(teacher_name_list)

    return group_dict

def generate():
    generator_config = load_config(generator_config_path)
    group_list = []

    for i in range(4):
        group_list.append(generator_config["groups"][i])

    group_dict = generate_classes(group_list, 7, generator_config)
    with open(os.path.join(config_dir, "group_config.json"), "w", encoding = "utf-8") as group_config_file:
        json.dump(group_dict, group_config_file, indent=4, ensure_ascii=False)

    #group_config = {}
    #for group in group_list:


if __name__ == "__main__":
    generate()