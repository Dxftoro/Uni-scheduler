import copy
import random
import mesa
from mesa import Agent, Model
from enum import Enum
from abc import abstractmethod
from entity_system import Space, IdDecoder

def get_intersection(dict1: dict, dict2: dict) -> set:
    intersection = {}
    for key, value in dict1.items():
        if key in dict2 and dict2[key] == value:
            intersection[key] = value
            #print(f"Общие пары ключ-значение (вложенные циклы): {common_items}")
    return intersection

def week_num(day: int, parity_rank: int, period_len: int):
    day_per_week = period_len // parity_rank
    return day // day_per_week

class AgentType(Enum):
    TEACHER =   0,
    GROUP =     1,
    ROOM =      2

class MessageType(Enum):
    WHENAVAIL = 0,
    USERAVAIL = 1,
    EVALUATE =  2,
    SUBJPREFS = 3,
    TIMEPROPOSAL = 4,
    ACCEPT = 5,
    REJECT = 6,
    LOCPROPOSAL = 7,
    FIXMEETING = 8,
    CANCEL_MEETING = 9,
    WHEREGAPS = 10,
    USERGAPS = 11,
    SET_STATE = 12

class TeacherState(Enum):
    ASK_WHEN_AVAIL = 0,
    IMPOSS_MEETING = 1,
    ASK_SUBJ_PREFS = 2,
    PROPOSE_TIME = 3,
    SOLNOT_FOUND = 4,
    PROPOSE_LOCATION = 5,
    FIX_MEETING = 6,
    BREAK = 7,
    TALK_TO_DEANERY = 8,
    WORK_ENDED = 9

class DeaneryState(Enum):
    ASK_GAPS = 0,
    FIND_FREE_TEACHERS = 1,

    WORK_ENDED = 10

class SolutionType(Enum):
    SOLUTION_NOT_FOUND = 0,
    UNDEFINED = 1,
    SOLUTION_FOUND = 2

class Message:
    def __init__(self, type, content, sender_id = None, receiver_id = None):
        self.type = type
        self.content = content
        self.sender_id = sender_id
        self.receiver_id = receiver_id
    
    def set_sender(self, sender_id) -> int:
        self.sender_id = sender_id
    
    def set_receiver(self, receiver_id) -> int:
        self.receiver_id = receiver_id
    
    def get_type(self):
        return self.type
    
    def get_content(self):
        return self.content
    
    def get_sender(self):
        return self.sender_id
    
    def get_receiver(self):
        return self.receiver_id
    
class SendingAgent(Agent):
    def __init__(self, self_id, model):
        super().__init__(model)
        self.self_id = self_id
        self.message_box = []

    def get_id(self):
        return self.self_id

    def send_message(self, message: Message, receiver_id: int, id_is_index = False):
        message.set_sender(self.self_id)
        message.set_receiver(receiver_id)
        
        if id_is_index:
            self.model.sending_agents[receiver_id].receive_message(message)
        else:
            for agent in self.model.sending_agents:
                if agent.get_id() == receiver_id:
                    log_part = f"{type(self).__name__}[{self.get_id()}] -> {type(agent).__name__}[{agent.get_id()}] : {message.get_type().name}"
                    self.model.log_message(log_part)
                    agent.receive_message(message)
                    break
    
    @abstractmethod
    def on_receive(self): pass

    def receive_message(self, message: Message):
        self.message_box.append(message)
        self.on_receive()
    
    def get_last_message(self) -> Message:
        return self.message_box[-1]
    
    def pop_last_message(self) -> Message:
        if not len(self.message_box): return None
        else: return self.message_box.pop()

class ClassInfo:
    def __init__(self, class_name: str, class_info: dict, group_id: int, global_space: Space):
        self.id = global_space.match(class_name)
        self.group_id = group_id
        self.type_id = global_space.match(class_info["class_type"])
        self.times = ()

        class_tools = []
        for tool in class_info["tools"]:
            tool_id = global_space.match(tool)
            class_tools.append(tool_id)
        self.tools = tuple(class_tools)
    
    def to_string(self) -> str:
        return f"class_id: {self.id} times: {self.times}" #group_id: {self.group_id}, type_id: {self.type}, times: {self.times}, tools: {self.tools}"
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __repr__(self) -> str:
        return self.to_string()
    
    def __format__(self, __format_spec: str) -> str:
        if __format_spec: pass
        return self.to_string()
    
class TeacherAgent(SendingAgent):
    def _next_class(self, mark_previous_as):
        self.owned_classes[self.viewing_class]["solution"] = mark_previous_as
        self.viewing_class += 1

        if self.viewing_class >= len(self.owned_classes):
            self.state = TeacherState.WORK_ENDED
            print(f"Teacher {self.get_id()} ended working!")
        else:
            self.state = TeacherState.ASK_WHEN_AVAIL
        
        self.groups_subjprefs = []
        self.current_subjpref_index = 0

    def _has_intersection(self, timeslots2: list, week: int, class_id) -> bool:
        parity_rank = self.model.get_parity_rank()

        for day_i, day in enumerate(self.timeslots):
            for slot_i, slot in enumerate(day):
                if week == week_num(day_i, parity_rank, len(self.timeslots)) and slot == class_id and timeslots2[day_i][slot_i] == class_id:
                    return True
        return False

    def __init__(self, model, self_id, timeslots, owned_classes, owned_groups):
        if not isinstance(owned_classes, list):
            owned_classes = [owned_classes]
        if not isinstance(owned_groups, list):
            owned_groups = [owned_groups]

        super().__init__(self_id, model)
#       Main data
        self.owned_classes = []
        self.owned_groups = owned_groups
        self.timeslots = timeslots
#       Step-dependent data
        self.viewing_class = 0
        self.state = TeacherState.ASK_WHEN_AVAIL
#       State-dependent data
        self.groups_subjprefs = []
        self.current_subjpref_index = 0

        for owned_class in owned_classes:
            for _ in range(owned_class.times[1]):
                self.owned_classes.append({
                    "id": owned_class.id,
                    "group_id": owned_class.group_id,
                    "type_id": owned_class.type_id,
                    "week": owned_class.times[0],
                    "tools": owned_class.tools,
                    "solution": SolutionType.UNDEFINED
                })
    
    def on_receive(self): pass
        #message = self.get_last_message()
        #print("Teacher received a message of type ", message.get_type())

    def step(self):
        if self.state == TeacherState.ASK_WHEN_AVAIL:
            empty_intersection = True
            #print("-----------------------------", self.viewing_class)
            week = self.owned_classes[self.viewing_class]["week"]
            group_id = self.owned_classes[self.viewing_class]["group_id"]

            #for group_id in self.owned_groups:
            request = Message(MessageType.WHENAVAIL, self.owned_classes[self.viewing_class])
            request.set_receiver(group_id)
            request.set_sender(self.get_id())
            self.send_message(request, group_id)

            response = self.pop_last_message()
            if response.get_type() == MessageType.USERAVAIL:
                empty_intersection = not self._has_intersection(response.get_content(), week, None) # !!!
            else:
                raise Exception(f"USERAVAIL expected. Got {response.get_type()}")
            
            if empty_intersection:
                self.state = TeacherState.IMPOSS_MEETING
            else:
                self.state = TeacherState.ASK_SUBJ_PREFS

        elif self.state == TeacherState.IMPOSS_MEETING:
            print(f"Teacher {self.get_id()} didn't find free timeslot for this class!")
            self._next_class(SolutionType.SOLUTION_NOT_FOUND)

        elif self.state == TeacherState.ASK_SUBJ_PREFS:
            group_id = self.owned_classes[self.viewing_class]["group_id"]
            self.groups_subjprefs = []

            #for group_id in self.owned_groups:
            request = Message(MessageType.EVALUATE, self.owned_classes[self.viewing_class])
            request.set_receiver(group_id)
            request.set_sender(self.get_id())
            self.send_message(request, group_id)

#           на этом этапе предпочтение - это свободный таймслот у группы
#           получаемое предпочтение: (id дня учебного ПЕРИОДА, номер пары)
#           получаем список предпочтений

            response = self.pop_last_message()
            if response.get_type() == MessageType.SUBJPREFS:
                self.groups_subjprefs += response.get_content()
            else:
                raise Exception(f"SUBJPREFS expected. Got {response.get_type()}")

            self.state = TeacherState.PROPOSE_TIME
        
        elif self.state == TeacherState.PROPOSE_TIME:
            group_id = self.owned_classes[self.viewing_class]["group_id"]

            if not len(self.groups_subjprefs):
                self.model.log_message(f"Teacher {self.get_id()} has empty groups_subjprefs!!!")

            if self.current_subjpref_index >= len(self.groups_subjprefs):
                self.state = TeacherState.SOLNOT_FOUND
                return

            subjpref = self.groups_subjprefs[self.current_subjpref_index]
            if not (self.timeslots[subjpref[0]][subjpref[1]] is None):
                self.current_subjpref_index += 1
                return

            #for group_id in self.owned_groups:
            timeproposal = (self.owned_classes[self.viewing_class]["id"], subjpref[0], subjpref[1])
            request = Message(MessageType.TIMEPROPOSAL, timeproposal)
            request.set_receiver(group_id)
            request.set_sender(self.get_id())
            self.send_message(request, group_id)

            response = self.pop_last_message()
            if response.get_type() == MessageType.ACCEPT:
                self.timeslots[subjpref[0]][subjpref[1]] = [self.owned_classes[self.viewing_class]["id"], None]
                self.state = TeacherState.PROPOSE_LOCATION
                return
            elif response.get_type() == MessageType.REJECT:
                self.model.log_message(f"Group {group_id} rejected {subjpref}!")
            else:
                raise Exception(f"ACCEPT or REJECT expected. Got {response.get_type()}")

            self.current_subjpref_index += 1
        
        elif self.state == TeacherState.SOLNOT_FOUND:
            print(f"Teacher {self.get_id()} didn't find solution for this class!")
            self._next_class(SolutionType.SOLUTION_NOT_FOUND)
        
        elif self.state == TeacherState.PROPOSE_LOCATION:
            group_id = self.owned_classes[self.viewing_class]["group_id"]
            subjpref = self.groups_subjprefs[self.current_subjpref_index]
            locproposal = (self.owned_classes[self.viewing_class], subjpref[0], subjpref[1])

            request = Message(MessageType.LOCPROPOSAL, locproposal)
            request.set_receiver(self.model.room_agent_id)
            request.set_sender(self.get_id())
            self.send_message(request, self.model.room_agent_id)

            response = self.pop_last_message()
            if response.get_type() == MessageType.ACCEPT:
                room_id = response.get_content()
                self.timeslots[subjpref[0]][subjpref[1]][1] = room_id

                group_request = Message(
                    MessageType.FIXMEETING,
                    (subjpref[0], subjpref[1], room_id), self.get_id(), group_id
                )
                self.send_message(group_request, group_id)
                self.state = TeacherState.FIX_MEETING

            elif response.get_type() == MessageType.REJECT:
                self.timeslots[subjpref[0]][subjpref[1]] = None
                
                group_request = Message(
                    MessageType.CANCEL_MEETING, 
                    (subjpref[0], subjpref[1]), self.get_id(), group_id
                )
                self.send_message(group_request, group_id)
                self.current_subjpref_index += 1
                self.state = TeacherState.PROPOSE_TIME

            else:
                raise Exception(f"ACCEPT or REJECT expected. Got {response.get_type()}")

        elif self.state == TeacherState.FIX_MEETING:
            #for group_id in self.owned_groups:
                #request = Message(MessageType.FIXMEETING, None, self.get_id(), group_id)
                #self.send_message(request, group_id)
            self._next_class(SolutionType.SOLUTION_FOUND)

class GroupAgent(SendingAgent):
    def __init__(self, model, self_id, timeslots):
        super().__init__(self_id, model)
        self.timeslots = timeslots
        self.planned_meetings = {}

    def on_receive(self):
        message = self.get_last_message()

        if message.get_type() == MessageType.WHENAVAIL:
            response = Message(MessageType.USERAVAIL, self.timeslots)
            response.set_sender(self.get_id())
            response.set_receiver(message.get_sender())
            self.send_message(response, message.get_sender())

        elif message.get_type() == MessageType.EVALUATE:
            subjpref = []
            week = message.get_content()["week"]
            parity_rank = self.model.get_parity_rank()

            for day_i in range(len(self.timeslots)):
                for slot_i in range(len(self.timeslots[day_i])):
                    if self.timeslots[day_i][slot_i] is None and week == week_num(day_i, parity_rank, len(self.timeslots)):
                        subjpref.append((day_i, slot_i))
            
            if not len(subjpref):
                self.model.log_message(f"{self.get_id()} has empty subjprefs!!!")
            
            response = Message(MessageType.SUBJPREFS, subjpref)
            response.set_sender(self.get_id())
            response.set_receiver(message.get_sender())
            self.send_message(response, message.get_sender())
        
        elif message.get_type() == MessageType.TIMEPROPOSAL:
            class_id = message.get_content()[0]
            day_i = message.get_content()[1]
            slot_i = message.get_content()[2]

            if self.timeslots[day_i][slot_i] is None:
                #self.planned_meetings[message.get_sender()] = (day_i, slot_i, None)
                self.timeslots[day_i][slot_i] = [class_id, message.get_sender(), None]
                response = Message(MessageType.ACCEPT, None)
                response.set_sender(self.get_id())
                response.set_receiver(message.get_sender())
                self.send_message(response, message.get_sender())
            else:
                print(f"Timeslot [{day_i}][{slot_i}] is {self.timeslots[day_i][slot_i]}")
                response = Message(MessageType.REJECT, None, self.get_id(), message.get_sender())
                self.send_message(response, message.get_sender())

        elif message.get_type() == MessageType.FIXMEETING:
            day_i = message.get_content()[0]
            slot_i = message.get_content()[1]
            room_id = message.get_content()[2]

            if not isinstance(self.timeslots[day_i][slot_i], list):
                raise Exception(f"Agent [{message.get_sender()}] tried to set meeting on unsuitable timeslot [{day_i}][{slot_i}] of group {self.get_id()}!")
            
            self.timeslots[day_i][slot_i][2] = room_id
        
        elif message.get_type() == MessageType.CANCEL_MEETING:
            day_i = message.get_content()[0]
            slot_i = message.get_content()[1]

            if not isinstance(self.timeslots[day_i][slot_i], list):
                raise Exception(f"Agent [{message.get_sender()}] tried to cancel meeting on unsuitable timeslot [{day_i}][{slot_i}]!")
            
            self.timeslots[day_i][slot_i] = None
        
        elif message.get_type() == MessageType.FIXMEETING:
            print("Meeting fixed")
    
    def step(self): pass
    
    def get_timeslots(self):
        return self.timeslots

class RoomInfo:
    def __init__(self, room_id: int, room_info: dict, timeslots, global_space: Space):
        self.id = room_id
        self.supported_class_types = []
        for type in room_info["supported_class_types"]:
            type_id = global_space.match(type)
            self.supported_class_types.append(type_id)

        self.tools = []
        for tool in room_info["tools"]:
            tool_id = global_space.match(tool)
            self.tools.append(tool_id)
        
        self.timeslots = timeslots
    
    def avaible_for(self, locproposal) -> bool:
        class_info = locproposal[0]

        if not (class_info["type_id"] in self.supported_class_types): return False
        if not len(class_info["tools"]) == 0 and not all(tool in self.tools for tool in class_info["tools"]): return False
        if not (self.timeslots[locproposal[1]][locproposal[2]] is None): return False

        return True

class RoomAgent(SendingAgent):
    def __init__(self, model, self_id, timeslots, room_config, global_space: Space):
        super().__init__(self_id, model)

        self.owned_rooms = []
        for room_name, room_info in room_config.items():
            room_id = global_space.match(room_name)
            self.owned_rooms.append(RoomInfo(room_id, room_info, copy.deepcopy(timeslots), global_space))
    
    def step(self): pass

    def on_receive(self):
        message = self.get_last_message()

        if message.get_type() == MessageType.LOCPROPOSAL:
            locproposal = message.get_content()
            day_i = locproposal[1]
            slot_i = locproposal[2]

            for room in self.owned_rooms:
                if room.avaible_for(locproposal):
                    room.timeslots[day_i][slot_i] = locproposal[0]["id"]
                    response = Message(MessageType.ACCEPT, room.id, self.get_id(), message.get_sender())
                    self.send_message(response, message.get_sender())
                    return
            response = Message(MessageType.REJECT, None, self.get_id(), message.get_sender())
            self.send_message(response, message.get_sender())
    
    def get_room_timeslots(self) -> dict:
        room_timeslots = {}
        for room in self.owned_rooms:
            room_timeslots[room.id] = room.timeslots
        return room_timeslots

class DeaneryAgent(SendingAgent):
    def __init__(self, teacher_ids, group_ids):
        self.teacher_ids = teacher_ids
        self.group_ids = group_ids
        self.completed_teachers_count = 0
        self.group_gaps = {}
        self.corrector_id = None
        self.state = DeaneryState.ASK_GAPS
    
    def step(self):
        if self.state == DeaneryState.WAIT_FOR_TEACHERS:
            if self.completed_teachers_count != len(self.teacher_ids): return 
            
            no_gaps_found = True
            for group_id in self.group_ids:
                request = Message(MessageType.WHEREGAPS, None)
                request.set_sender(self.get_id())
                request.set_receiver(group_id)

                response = self.pop_last_message()
                if response.get_type() == MessageType.USERGAPS:
                    self.group_gaps[response.get_sender()] = response.get_content()
                    if len(response.get_content()): no_gaps_found = False
                else:
                    raise Exception(f"USERGAPS expected. Got {response.get_type()}")
        
            if no_gaps_found:
                for teacher_id in self.teacher_ids:
                    message = Message(
                        MessageType.SET_STATE, 
                        TeacherState.WORK_ENDED,
                        self.get_id(), teacher_id)
                    self.send_message(message, teacher_id)
                self.state = DeaneryState.WORK_ENDED
            else:
                for teacher_id, in self.teacher_ids:
                    message = Message(
                        MessageType.SET_STATE, 
                        TeacherState.TALK_TO_DEANERY,
                        self.get_id(), teacher_id)
                    self.send_message(message, teacher_id)
                self.state = DeaneryState.FIND_FREE_TEACHERS
        
        elif self.state == DeaneryState.FIND_FREE_TEACHERS:
            max_free_times = 0
            for teacher_id in self.teacher_ids:
                request = Message(MessageType.TIMEPROPOSAL, self.group_gaps, self.get_id(), teacher_id)
                self.send_message(request, teacher_id)

                response = self.pop_last_message()
                if response.get_type() == MessageType.ACCEPT:
                    pass

    def on_receive(self): pass

class ScheduleModel(Model):
    def _make_ids(self, group_config: dict, global_space: Space) -> int:
        for group_name, group_plan in group_config.items():
            group_id = global_space.match(group_name)
            self.group_ids.append(group_id)

            self.group_times[group_id] = [0,] * self.parity_rank
            for class_name, class_info in group_plan.items():
                for i in range(len(class_info["times"])):
                    self.group_times[group_id][i] += class_info["times"][i]
            
            self.log_message(f"Times of group {group_id}: {self.group_times[group_id]}")

            for class_name, class_info in group_plan.items():
                _class = ClassInfo(class_name, class_info, group_id, global_space)
                self.class_ids.append(_class.id)

                teacher_id = global_space.match(class_info["teacher"])
                self.log_message(f"{class_name} [{_class.id}] owned by {class_info['teacher']} [{teacher_id}]")
                if not (teacher_id in self.teacher_ids):
                    self.teacher_ids[teacher_id] = {}
                
                for i, time in enumerate(class_info["times"]):
                    _class_copy = copy.deepcopy(_class)
                    _class_copy.times = (i, time)

#                   owned_class: tuple (id, group id, appearance, tools)
#                   appearance: tuple (week number, count of class repeats (it's called "time"))
#                   tools: tuple (tool1, tool2, ..., tooln)

                    if "owned_classes" in self.teacher_ids[teacher_id]:
                        self.teacher_ids[teacher_id]["owned_classes"].add(_class_copy)
                    else:
                        self.teacher_ids[teacher_id]["owned_classes"] = {_class_copy}

                if "owned_groups" in self.teacher_ids[teacher_id]:
                    self.teacher_ids[teacher_id]["owned_groups"].add(group_id)
                else:
                    self.teacher_ids[teacher_id]["owned_groups"] = {group_id}
        
        self.log_message(f"Group ids: {self.group_ids}")
        self.log_message(f"Class ids: {self.class_ids}")
        self.log_message(f"Teacher ids: {self.teacher_ids}")
        return global_space.match("This slot is blocked for capturing!")

    def _make_timeslots(self, group_id: int, slot_blocked_id: int):
        class_min_count = self.default_timeslots["class_min_count"]
        new_timeslots = copy.deepcopy(self.default_timeslots["timeslots"])
        slot_per_day = len(new_timeslots[0])
        day_count = len(new_timeslots)
        day_per_week = day_count // self.parity_rank
        #day_checklist = [slot_per_day - 1,] * len(new_timeslots)

        for time_i in range(len(self.group_times[group_id])):
            used_slot_count = self.group_times[group_id][time_i]
            free_slot_count = (slot_per_day * day_per_week) - used_slot_count

            #print(f"{slot_per_day * day_per_week} {used_slot_count} Week {time_i} of group {group_id} has {free_slot_count} free slots")

            for day_i in range(time_i * day_per_week, (time_i * day_per_week) + day_per_week):
                slot_to_block = slot_per_day - 1
                if free_slot_count <= 0: break

                while slot_to_block >= class_min_count:
                    new_timeslots[day_i][slot_to_block] = slot_blocked_id
                    slot_to_block -= 1
                    free_slot_count -= 1
                    if not free_slot_count: break

        return new_timeslots

    def _make_groups_and_teachers(self, default_timeslots: list, slot_blocked_id: int):
        for group_id in self.group_ids:
            group_agent_set = GroupAgent.create_agents(self, 1, group_id, self._make_timeslots(group_id, slot_blocked_id))
            self.sending_agents.append(next(iter(group_agent_set)))

        for teacher_id, teacher_property in self.teacher_ids.items():
            if not len(teacher_property["owned_classes"]) or not len(teacher_property["owned_groups"]):
                raise Exception("Teacher property can't be empty!")

            teacher_agent_set = TeacherAgent.create_agents(self, 1,
                teacher_id,
                copy.deepcopy(default_timeslots),
                list(teacher_property["owned_classes"]),
                list(teacher_property["owned_groups"])
            )
            self.sending_agents.append(next(iter(teacher_agent_set)))

    def __init__(self, default_timeslots, parity_rank: int, config: dict, global_space: Space):
        super().__init__(seed=0)
        random.seed(0)
        self.agents # !!!

        self.default_timeslots = default_timeslots
        self.group_ids = []
        self.class_ids = []
        self.room_ids = []
        self.teacher_ids = {}
        self.sending_agents = []
        self.message_log = []
        self.parity_rank = parity_rank
        self.group_times = {}

        self.room_agent_id = global_space.match("Room agent")
        room_agent_set = RoomAgent.create_agents(self, 1, 
            self.room_agent_id,
            self.default_timeslots["timeslots"],
            config["room_config"],
            global_space)
        
        room_agent = next(iter(room_agent_set))
        self.sending_agents.append(room_agent)

        slot_blocked_id = self._make_ids(config["group_config"], global_space)
        self._make_groups_and_teachers(self.default_timeslots["timeslots"], slot_blocked_id)
    
    def step(self):
        self.agents.shuffle_do("step")
    
    def get_group_timeslots(self):
        timeslots = {}
        for agent in self.sending_agents:
            if isinstance(agent, GroupAgent):
                timeslots[agent.get_id()] = agent.get_timeslots()
        return timeslots
    
    def get_teacher_states(self):
        states = []
        for agent in self.sending_agents:
            if isinstance(agent, TeacherAgent):
                states.append(agent.state)
        return states
    
    def get_room_timeslots(self) -> dict:
        for agent in self.sending_agents:
            if isinstance(agent, RoomAgent):
                room_timeslots = agent.get_room_timeslots()
                return room_timeslots

    def schedule_in_state(self, state) -> bool:
        teacher_states = self.get_teacher_states()
        for teacher_state in teacher_states:
            if not (teacher_state == state):
                return False
        return True

    def schedule_ready(self) -> bool:
        return self.schedule_in_state(TeacherState.WORK_ENDED)

    def log_message(self, log_part: str):
        self.message_log.append(log_part)

    def get_message_log(self):
        return self.message_log

    def get_parity_rank(self):
        return self.parity_rank