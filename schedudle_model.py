import copy
import random
import mesa
from mesa import Agent, Model
from enum import Enum
from abc import abstractmethod
from entity_system import Space

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
    CANCEL_MEETING = 9

class TeacherState(Enum):
    ASK_WHEN_AVAIL = 0,
    IMPOSS_MEETING = 1,
    ASK_SUBJ_PREFS = 2,
    PROPOSE_TIME = 3,
    SOLNOT_FOUND = 4,
    PROPOSE_LOCATION = 5,
    FIX_MEETING = 6,

    WAIT_FOR_AVAIL = 7
    WORK_ENDED = 8

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
                    log_part = f"{type(self)}[{self.get_id()}] sent to {type(agent)}[{agent.get_id()}] a message of type {message.get_type()}"
                    self.model.log_message(log_part)
                    print(log_part)
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
        return self.message_box.pop()
    
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
                    #print(f"Found intersection in [{day_i}][{slot_i}]")
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
            for _ in range(owned_class[2][1]):
                self.owned_classes.append({
                    "id": owned_class[0],
                    "group_id": owned_class[1],
                    "week": owned_class[2][0],
                    "solution": SolutionType.UNDEFINED
                })
    
    def on_receive(self):
        message = self.get_last_message()
        print("Teacher received a message of type ", message.get_type())

    def step(self):
        if self.state == TeacherState.ASK_WHEN_AVAIL:
            empty_intersection = True
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

#               на этом этапе предпочтение - это свободный таймслот у группы
#               получаемое предпочтение: (id дня учебного ПЕРИОДА, номер пары)
#               получаем список предпочтений

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
            timeproposal = (self.owned_classes[self.viewing_class]["id"],
                subjpref[0], subjpref[1]
            )
            request = Message(MessageType.TIMEPROPOSAL, timeproposal)
            request.set_receiver(group_id)
            request.set_sender(self.get_id())
            self.send_message(request, group_id)

            response = self.pop_last_message()
            if response.get_type() == MessageType.ACCEPT:
                self.timeslots[subjpref[0]][subjpref[1]] = self.owned_classes[self.viewing_class]["id"]
                self.state = TeacherState.FIX_MEETING
                return
            elif response.get_type() == MessageType.REJECT:
                self.model.log_message(f"Group {group_id} rejected {subjpref}!")
            else:
                raise Exception(f"ACCEPT or REJECT expected. Got {response.get_type()}")

            self.current_subjpref_index += 1
        
        elif self.state == TeacherState.SOLNOT_FOUND:
            print(f"Teacher {self.get_id()} didn't find solution for this class!")
            self._next_class(SolutionType.SOLUTION_NOT_FOUND)

        elif self.state == TeacherState.FIX_MEETING:
            for group_id in self.owned_groups:
                request = Message(MessageType.FIXMEETING, None, self.get_id(), group_id)
                self.send_message(request, group_id)
            self._next_class(SolutionType.SOLUTION_FOUND)

class GroupAgent(SendingAgent):
    def __init__(self, model, self_id, timeslots):
        super().__init__(self_id, model)
        self.timeslots = timeslots
        self.last_timepropose = ()

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
                self.last_timepropose = (day_i, slot_i)
                self.timeslots[day_i][slot_i] = (class_id, message.get_sender())
                response = Message(MessageType.ACCEPT, None)
                response.set_sender(self.get_id())
                response.set_receiver(message.get_sender())
                self.send_message(response, message.get_sender())
            else:
                print(f"Timeslot [{day_i}][{slot_i}] is {self.timeslots[day_i][slot_i]}")
                response = Message(MessageType.REJECT, None, self.get_id(), message.get_sender())
                self.send_message(response, message.get_sender())
        
        elif message.get_type() == MessageType.FIXMEETING:
            print("Meeting fixed")
    
    def step(self):
        print(f"Group {self.get_id()} stepped!")
    
    def get_timeslots(self):
        return self.timeslots

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
                class_id = global_space.match(class_name)
                self.class_ids.append(class_id)

                teacher_id = global_space.match(class_info["teacher"])
                if not (teacher_id in self.teacher_ids):
                    self.teacher_ids[teacher_id] = {}
                
                for i, time in enumerate(class_info["times"]):
#                   owned_class: tuple (id, group id, appearance)
#                   appearance: tuple (week number, count of class repeats (it's called "time"))

                    if "owned_classes" in self.teacher_ids[teacher_id]:
                        self.teacher_ids[teacher_id]["owned_classes"].add((class_id, group_id, (i, time)))
                    else:
                        self.teacher_ids[teacher_id]["owned_classes"] = {(class_id, group_id, (i, time))}

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

    def _make_agents(self, default_timeslots: list, slot_blocked_id: int):
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

    def __init__(self, default_timeslots: list, parity_rank: int, group_config: dict, global_space: Space):
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

        slot_blocked_id = self._make_ids(group_config, global_space)
        self._make_agents(self.default_timeslots["timeslots"], slot_blocked_id)
    
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
    
    def log_message(self, log_part: str):
        self.message_log.append(log_part)

    def get_message_log(self):
        return self.message_log

    def get_parity_rank(self):
        return self.parity_rank

    def check_group_teacher_collisions(self):
        day_count = len(self.default_timeslots)
        slot_count = len(self.default_timeslots[0])
        
        for day_i in range(day_count):
            for slot_i in range(slot_count):
                for agent in self.sending_agents:
                    if not isinstance(agent, GroupAgent): continue