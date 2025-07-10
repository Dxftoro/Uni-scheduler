dict1 = [
    [2, 3, 6, 1],
    [0, None, None, 1],
    [0, 3, 4, 1],
    [0, 1, 3, 1],
    [5, 4, 2, 1]
]
dict2 = [
    [2, 3, 6, 1],
    [0, None, None, 1],
    [0, 3, 4, 1],
    [0, 1, 3, 1],
    [5, 4, 2, 1]  
]

def has_intersection_by_id(timeslots1: list, timeslots2: list, class_id) -> bool:
    for day_i, day in enumerate(timeslots1):
        for slot_i, slot in enumerate(day):
            if slot == class_id and timeslots2[day_i][slot_i] == class_id:
                print(f"Found intersection in [{day_i}][{slot_i}]")
    return True

has_intersection_by_id(dict1, dict2, None)
print(len((1, 2,3)))

aa = {18}
print(list(aa))

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
