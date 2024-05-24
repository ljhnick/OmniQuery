from src.memory.memory import MemoryBuilder

class MemoryRetriever():
    def __init__(self,
                 memory: MemoryBuilder = None) -> None:
        self.memory = memory

    def retrieve(self, query):
        return