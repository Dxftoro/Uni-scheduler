from abc import abstractmethod

class Space:
    def _exists(self, data):
        for index, entity_data in enumerate(self.entities):
            if entity_data == data: return index
        return False

    def __init__(self):
        self.entities = []
    
    def match(self, entity_data) -> int:
        possible_index = self._exists(entity_data)

        if possible_index == False:
            self.entities.append(entity_data)
            return len(self.entities) - 1
        else:
            return possible_index
    
    def last_created_id(self) -> int:
        entity_count = len(self.entities)
        if entity_count == 0: return None
        else: return entity_count - 1
    
    def get(self, entity_id: int):
        return self.entities[entity_id]
    
    def get_entities(self):
        return self.entities

class IdDecoder:
    def __init__(self, space: Space):
        self.space = space
    
    @abstractmethod
    def decode(self, custom_data): pass