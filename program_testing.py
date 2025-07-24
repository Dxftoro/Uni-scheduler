import time
import abc
from memory_profiler import memory_usage

class MeasureException(Exception):
    def __init__(self):
        super.__init__("Unclosed beg-end pair on timer call")

class Measurer:
    @abc.abstractmethod
    def begin(): pass

    @abc.abstractmethod
    def end(): pass

    @abc.abstractmethod
    def result(): pass

class Timer(Measurer):
    beg_time = None
    end_time = None

    def __init__(self):
        pass

    def begin(self):
        self.beg_time = time.time()
    
    def end(self):
        self.end_time = time.time()
    
    def result(self):
        if self.beg_time is None or self.end_time is None:
            raise MeasureException()
        
        time_elapsed = self.end_time - self.beg_time
        self.beg_time = None
        self.end_time = None
        return time_elapsed

class MemoryMeasurer(Measurer):
    beg_memory = None
    end_memory = None

    def __init__(self): pass

    def begin(self):
        self.beg_memory = memory_usage(-1)[0]
    
    def end(self):
        self.end_memory = memory_usage(-1)[0]
    
    def result(self):
        if self.beg_memory is None or self.end_memory is None:
            raise MeasureException()
        
        memory_diff = self.end_memory - self.beg_memory
        self.beg_memory = None
        self.end_memory = None
        return memory_diff