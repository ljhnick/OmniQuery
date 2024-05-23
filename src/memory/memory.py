import os
from src.memory.nodes import MemoryNodesBuilder, MemoryNodeSingle


class MemoryBuilder():
    def __init__(self,
                 memory_processed,
                 memory_raw):
        self.memory_raw = memory_raw
        self.memory_nodes_dict = memory_processed['nodes'] if 'nodes' in memory_processed else {}
        self.events = memory_processed['events'] if 'events' in memory_processed else []
        self.event_dict = memory_processed['event_dict'] if 'event_dict' in memory_processed else {}

    def _update_memory(self, memory_nodes_dict, memory_raw):
        # check if the memory is processed and saved in the json
        # load all the file in the memory container

        # convert json to memory nodes
        memory_nodes_builder = MemoryNodesBuilder(memory_nodes_dict=memory_nodes_dict)
        memory_nodes = memory_nodes_builder.get_nodes()

        for memory_filename in memory_raw:
            if memory_filename not in memory_nodes_dict:
                # this step build an insular memory node, this node is not connected to other node yet.
                new_node = self._build_memory_node(memory_raw[memory_filename])
                # connect the new node with the existing memory
                self._connect_memory_node(memory_nodes, new_node)

    def _build_memory_node(self, memory_file_dict):
        new_node = MemoryNodeSingle(params=memory_file_dict, is_build=True)
        pass

    def _connect_memory_node(self, memory_nodes, new_node):
        pass

    def build(self):
        self._update_memory(self.memory_nodes_dict, self.memory_raw)