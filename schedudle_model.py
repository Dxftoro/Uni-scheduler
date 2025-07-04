from mesa import Agent, Model
from enum import Enum

def get_intersection(dict1: dict, dict2: dict) -> set:
    intersection = {}
    for key, value in dict1.items():
        if key in dict2 and dict2[key] == value:
            intersection[key] = value
            #print(f"Общие пары ключ-значение (вложенные циклы): {common_items}")
            return intersection

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
    def __init__(self, type, content):
        self.type = type
        self.content = content
        self.sender_id = None
        self.receiver_id = None
    
    def set_sender(self, sender_id) -> int:
        self.sender_id = sender_id
    
    def set_receiver(self, receiver_id) -> int:
        self.receiver_id = receiver_id
    
    def get_type(self):
        return self.type
    
    def get_content(self):
        return self.content
    
class SendingAgent(Agent):
    def __init__(self, self_id, model):
        super().__init__(self_id, model)
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
    
    def receive_message(self, message: Message):
        self.message_box.append(message)
    
    def get_last_message(self) -> Message:
        return self.message_box[-1]
    
    def pop_last_message(self) -> Message:
        return self.message_box.pop()

class TeacherAgent(SendingAgent):
    def __init__(self, self_id, model, timeslots):
        super().__init__(self_id, model)
#       Main data
        self.owned_classes = []
        self.owned_groups = []
        self.timeslots = timeslots
#       Step-dependent data
        self.viewing_class = 0
        self.state = TeacherState.ASK_WHEN_AVAIL
        self.current_subjpref_index = 0
#       State-dependent data
        self.groups_subjprefs = []
    
    def step(self):
        if self.state == TeacherState.ASK_WHEN_AVAIL:
            all_empty = True

            for group_id in self.owned_groups:
                request = Message(MessageType.WHENAVAIL, {
                    "class_id": self.owned_classes[self.viewing_class],
                    "timeslots": self.timeslots
                })
                request.set_receiver(group_id)
                request.set_sender(self.get_id())
                self.send_message(request, group_id)

                response = self.pop_last_message()
                if response.get_type() == MessageType.USERAVAIL:
                    intersection = get_intersection(self.timeslots, response.get_content())
                    if not len(intersection):
                        all_empty = False
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

#            for subjpref in self.groups_subjprefs:
#               subjpref[0] - group_id
#               subjpref[1] - day_id
#               subjpref[2] - time number
#
#                timeproposal = (
#                    self.owned_classes[self.viewing_class]["id"],
#                    subjpref[1], subjpref[2]
#                )
#                request = Message(MessageType.TIMEPROPOSAL, timeproposal)
#                request.set_receiver(subjpref[0])
#                request.set_sender(self.get_id())
#                self.send_message(request, subjpref[0])


class GroupAgent(SendingAgent):
    def __init__(self, self_id, model):
        super().__init__(self_id, model)

class ScheduleModel(Model):
    def __init__(self, teachers: SendingAgent, groups: SendingAgent, classes: SendingAgent):
        pass