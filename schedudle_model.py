import copy
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

def has_intersection_by_id(timeslots1: list, timeslots2: list, class_id) -> bool:
    for day_i, day in enumerate(timeslots1):
        for slot_i, slot in enumerate(day):
            if slot == class_id and timeslots2[day_i][slot_i] == class_id:
                #print(f"Found intersection in [{day_i}][{slot_i}]")
                return True
    return False

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
            self.model.schedule.agents[receiver_id].receive_message(message)
        else:
            for agent in self.model.schedule.agents:
                if agent.get_id() == receiver_id:
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
    def __init__(self, model, self_id, timeslots, owned_classes, owned_groups):
        super().__init__(self_id, model)
#       Main data
        self.owned_classes = owned_classes
        self.owned_groups = owned_groups
        self.timeslots = timeslots
#       Step-dependent data
        self.viewing_class = 0
        self.state = TeacherState.ASK_WHEN_AVAIL
        self.current_subjpref_index = 0
#       State-dependent data
        self.groups_subjprefs = []
    
    def on_receive(self):
        message = self.get_last_message()
        print("Teacher received a message of type ", message.get_type())

    def step(self):
        if self.state == TeacherState.ASK_WHEN_AVAIL:
            all_empty = True

            for group_id in self.owned_groups:
                request = Message(MessageType.WHENAVAIL, self.owned_classes[self.viewing_class])
                request.set_receiver(group_id)
                request.set_sender(self.get_id())
                self.send_message(request, group_id)

                response = self.pop_last_message()
                if response.get_type() == MessageType.USERAVAIL:
                    all_empty = not has_intersection_by_id(self.timeslots, response.get_content(), None) # !!!
                else:
                    raise Exception(f"USERAVAIL expected. Got {response.get_type()}")
            
            if all_empty:
                self.state = TeacherState.IMPOSS_MEETING
            else:
                self.state = TeacherState.ASK_SUBJ_PREFS

        elif self.state == TeacherState.IMPOSS_MEETING:
            self.owned_classes[self.viewing_class]["solution"] = 0
            self.viewing_class += 1
        
        elif self.state == TeacherState.ASK_SUBJ_PREFS:
            self.groups_subjprefs = []

            for group_id in self.owned_groups:
                request = Message(MessageType.EVALUATE, self.owned_classes[self.viewing_class]["id"])
                request.set_receiver(group_id)
                request.set_sender(self.get_id())
                self.send_message(request, group_id)

#               на этом этапе предпочтение - это свободный таймслот у группы
#               получаемое предпочтение: (id дня учебного ПЕРИОДА, номер пары)
#               получаем список предпочтений

                response = self.pop_last_message()
                if response.get_type() == MessageType.SUBJPREFS:
                    self.groups_subjprefs.append(response.get_content())
                else:
                    raise Exception(f"SUBJPREFS expected. Got {response.get_type()}")

            self.state = TeacherState.PROPOSE_TIME
        
        elif self.state == TeacherState.PROPOSE_TIME:
            if not len(self.groups_subjprefs):
                raise Exception(f"Teacher {self.get_id()} has empty groups_subjprefs!")

            if self.current_subjpref_index >= len(self.groups_subjprefs):
                self.state = TeacherState.SOLNOT_FOUND
                return

            subjpref = self.groups_subjprefs[self.current_subjpref_index]
            
            for group_id in self.owned_groups:
                timeproposal = (self.owned_classes[self.viewing_class]["id"],
                    subjpref[0], subjpref[1]
                )
                request = Message(MessageType.TIMEPROPOSAL, timeproposal)
                request.set_receiver(group_id)
                request.set_sender(self.get_id())
                self.send_message(request, group_id)

                response = self.pop_last_message()
                if response.get_type() == MessageType.ACCEPT:
                    self.state = TeacherState.FIX_MEETING
                    break
                elif response.get_type() == MessageType.REJECT:
                    self.current_subjpref_index += 1
                    break
                else:
                    raise Exception(f"ACCEPT or REJECT expected. Got {response.get_type()}")
        
        elif self.state == TeacherState.FIX_MEETING:
            for group_id in self.owned_groups:
                request = Message(MessageType.FIXMEETING, None, self.get_id(), group_id)
                self.send_message(request, group_id)

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
            self.send_message(message, message.get_sender())

        elif message.get_type() == MessageType.EVALUATE:
            subjpref = ()
            for day_i in range(len(self.timeslots)):
                for slot_i in range(len(self.timeslots[day_i])):
                    if self.timeslots[day_i][slot_i] is None:
                        subjpref = (day_i, slot_i)
                        break
            
            if len(subjpref):
                response = Message(MessageType.SUBJPREFS, subjpref)
                response.set_sender(self.get_id())
                response.set_receiver(message.get_sender())
                self.send_message(response, message.get_sender())
            else:
                raise Exception(f"Group {self.get_id()} has no subjprefs!")
        
        elif message.get_type() == MessageType.TIMEPROPOSAL:
            class_id = message.get_content()[0]
            day_i = message.get_content()[1]
            slot_i = message.get_content()[2]

            if self.timeslots[day_i][slot_i] is None:
                self.last_timepropose = (day_i, slot_i)
                self.timeslots[day_i][slot_i] = class_id
                response = Message(MessageType.ACCEPT, None)
                response.set_sender(self.get_id())
                response.set_receiver(message.get_sender())
                self.send_message(response, message.get_sender())
            else:
                response = Message(MessageType.REJECT, None, self.get_id(), message.get_sender())
        
        elif message.get_type() == MessageType.FIXMEETING:
            print("Meeting fixed")
    
    def step(self):
        print(f"Group {self.get_id()} stepped!")

class ScheduleModel(Model):
    def _make_ids(self, group_config: dict, global_space: Space):
        for group_name, group_plan in group_config.items():
            group_id = global_space.match(group_name)
            self.group_ids.append(group_id)

            for class_name, class_info in group_plan.items():
                class_id = global_space.match(class_name)
                self.class_ids.append(class_id)

                teacher_id = global_space.match(class_info["teacher"])
                if not (teacher_id in self.teacher_ids):
                    self.teacher_ids[teacher_id] = {}
                
                if "owned_classes" in self.teacher_ids[teacher_id]:
                    self.teacher_ids[teacher_id]["owned_classes"].add(class_id)
                else:
                    self.teacher_ids[teacher_id]["owned_classes"] = set()

                if "owned_groups" in self.teacher_ids[teacher_id]:
                    self.teacher_ids[teacher_id]["owned_groups"].add(group_id)
                else:
                    self.teacher_ids[teacher_id]["owned_groups"] = set()
        
        print("Group ids: ", self.group_ids)
        print("Class ids: ", self.class_ids)
        print("Teacher ids: ", self.teacher_ids)

    def _make_agents(self, default_timeslots: list):
        for group_id in self.group_ids:
            GroupAgent.create_agents(self, 1, group_id, copy.deepcopy(default_timeslots))
        for teacher_id, teacher_property in self.teacher_ids.items():
            TeacherAgent.create_agents(self, 1,
                teacher_id,
                copy.deepcopy(default_timeslots),
                list(teacher_property["owned_classes"]),
                list(teacher_property["owned_groups"])
            )

    def __init__(self, default_timeslots: list, group_config: dict, global_space: Space):
        super().__init__(seed=0)
        self.agents

        self.default_timeslots = default_timeslots
        self.group_ids = []
        self.class_ids = []
        self.room_ids = []
        self.teacher_ids = {}

        self._make_ids(group_config, global_space)
        self._make_agents(default_timeslots)
    
    def step(self):
        self.agents.shuffle_do("step")