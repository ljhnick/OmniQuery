import os
import json
from tqdm import tqdm
from collections import defaultdict
import random
import datetime

from src.memory.nodes import MemoryNodesBuilder, MemoryNodeSingle
from src.memory.knowledge import MemoryKnowledgeBuilder
from src.parser.llm import OpenAIWrapper

from utils.exif_utils import read_metadata_from_image


class MemoryBuilder():
    def __init__(self,
                 memory_processed,
                 semantic_knowledge,
                 memory_raw,
                 images_embedding_store:str = "",
                 events_embedding_store:str = "",
                 semantic_knowledge_embedding_store:str = "",
                 is_force_generate:bool = False) -> None:
        self.memory_raw = memory_raw
        # self.memory_nodes_dict = memory_processed['nodes'] if 'nodes' in memory_processed else {}
        self.processed = memory_processed
        self.semantic_knowledge = semantic_knowledge
        self.memory_dict = memory_processed['memories'] if 'memories' in memory_processed else {}
        # self.events = memory_processed['events'] if 'events' in memory_processed else {}
        # self.event_dict = memory_processed['event_dict'] if 'event_dict' in memory_processed else {}
        # self.semantic_knowledge = memory_processed['semantic_knowledge'] if 'semantic_knowledge' in memory_processed else {}

        self.images_embedding_store_path = images_embedding_store
        if os.path.exists(images_embedding_store) == False:
            self.images_embedding_store = {}
        else:
            with open(images_embedding_store, "r") as f:
                self.images_embedding_store = json.load(f)

        self.llm = OpenAIWrapper()
        self.is_force_generate = is_force_generate

    def _update_memory(self):
        # check if the memory is processed and saved in the json
        # load all the file in the memory container

        # convert json to memory nodes
        # create nodes for every memory file

        self.all_memory_nodes = []
        for memory_filename in self.memory_raw:
            if memory_filename in self.memory_dict:
                # params include: 'filepath', 'actual media', 'metadata', 'content'
                raw_info = self.memory_raw[memory_filename]
                memory_node = MemoryNodeSingle(raw_info=raw_info, processed_info=self.memory_dict[memory_filename])
            else:
                memory_node = MemoryNodeSingle(raw_info=self.memory_raw[memory_filename], processed_info={})
            
            self.all_memory_nodes.append(memory_node)

        print("Start getting metadata... and sorting by date...")
        for memory_node in tqdm(self.all_memory_nodes):
            memory_node.get_metadata(self.is_force_generate)   
        self.all_memory_nodes = sorted(self.all_memory_nodes, key=lambda x: x.date)

        # generate image embeddings for the memory
        print("Start grouping similar image content...")
        for memory_node in tqdm(self.all_memory_nodes[:]):
            # if memory_node.filename not in self.images_embedding_store:
            image_embeddings = memory_node.get_image_embeddings(self.images_embedding_store)
            self.images_embedding_store[memory_node.filename] = image_embeddings
        # save the image embeddings
        with open(self.images_embedding_store_path, "w") as f:
            json.dump(self.images_embedding_store, f)

        nodes_grouped_by_date = defaultdict(list)
        for memory_node in self.all_memory_nodes:
            date_key = memory_node.date.date()
            nodes_grouped_by_date[date_key].append(memory_node)

        for date, nodes in nodes_grouped_by_date.items():
            random.seed(529)
            # random.shuffle(nodes)
            for node in nodes:
                node.group_with_similar_images(nodes)

        # generate content
        print("Start getting content...")
        for memory_node in tqdm(self.all_memory_nodes[:]):
            memory_node.get_content()

    def _update_knowledge(self):
        # load and generate events from the proessed nodes
        knowledge_builder = MemoryKnowledgeBuilder(memory_nodes=self.all_memory_nodes, semantic_processed=self.semantic_knowledge)
        self.knowledge_builder = knowledge_builder 
        self.knowledge_builder.build()
        print(f"Building knowledge cost: {self.knowledge_builder.cost}")


    def _build_memory_node(self, memory_file_dict):
        new_node = MemoryNodeSingle(params=memory_file_dict, is_build=True)
        return new_node

    def _connect_memory_node(self, memory_nodes, new_node):
        # update shared events, update the event_dict, update the semantic memory
        node_event = new_node.events
        self._update_shared_events(new_node, node_event)

        node_semantic_knowledge = new_node.semantic_knowledge
        self._update_shared_semantic_knowledge(new_node, node_semantic_knowledge)

        memory_nodes.append(new_node)
        self.memory_nodes = memory_nodes

        return
    
    def _update_shared_events(self, new_node, node_events):
        # existing shared events {event_id: event_name, event_other_name, children_nodes: [node_ids]}
        for new_event in node_events['events']:
            # check if it can belong to an existing event in the shared events
            merged = False
            for event_id in self.events:
                event_name = self.events[event_id]['name']
                similarity, _ = self.llm.compare_similarity(new_event, event_name)
                if eval(similarity) >= 7:
                    if new_node.node_id not in self.events[event_id]['children_nodes']:
                        self.events[event_id]['children_nodes'].append(new_node.node_id)
                    merged = True
                    break
                    
            if merged == True:
                continue

            # create new event in the shared events
            new_event_id = len(self.events)
            self.events[new_event_id] = {
                'name': new_event,
                'children_nodes': [new_node.node_id]
            }
            event_embedding = self.llm.calculate_embeddings(new_event)
            self.events_embedding_store[new_event_id] = event_embedding

            new_node.event_ids.append(new_event_id)

        return
    
    def _update_shared_semantic_knowledge(self, new_node, node_semantic_knowledge):
        # existing semantic knowledge {knowledge_id, knowledge_name, node_ids: [node_ids]}
        node_knowledges = node_semantic_knowledge['semantic_knowledge']
        for node_knowledge in node_knowledges:
            merged = False
            for knowledge_id in self.semantic_knowledge:
                knowledge_name = self.semantic_knowledge[knowledge_id]['name']
                # compute embeddings
                # self.llm.calculate_embeddings(node_knowledge)

                similarity, _ = self.llm.compare_similarity(node_knowledge, knowledge_name)
                if eval(similarity) >= 7:
                    if new_node.node_id not in self.semantic_knowledge[knowledge_id]['node_ids']:
                        self.semantic_knowledge[knowledge_id]['node_ids'].append(new_node.node_id)
                    merged = True
                    break
            if merged == True:
                continue

            # add the new knowledge to the semantic knowledge
            new_knowledge_id = len(self.semantic_knowledge)
            self.semantic_knowledge[new_knowledge_id] = {
                'name': node_knowledge,
                'node_ids': [new_node.node_id]
            }
            semantic_knowledge_embedding = self.llm.calculate_embeddings(node_knowledge)
            self.semantic_knowledge_embedding_store[new_knowledge_id] = semantic_knowledge_embedding

            new_node.knowledge_ids.append(new_knowledge_id)

        return
    
    def _save(self):
        # save stores
        # with open(self.events_embedding_store_path, "w") as f:
        #     json.dump(self.events_embedding_store, f)
        # with open(self.semantic_knowledge_embedding_store_path, "w") as f:
        #     json.dump(self.semantic_knowledge_embedding_store, f)
        # if self._save_path == "":
        #     raise ValueError("Save path is not defined")
        
        memories = {}
        
        for node in self.all_memory_nodes:
            node_dict = node.export_dict()
            memories[node.filename] = node_dict

        self.processed['memories'] = memories

        try:
            # events = self.knowledge_builder.export_events_dict()
            # self.semantic_knowledge['events'] = events
            self.semantic_knowledge = self.knowledge_builder.export_knowledge_dict()
        except Exception as e:
            print(f"Error: {e}")

        with open(self._save_path_memory, "w") as f:
            json.dump(self.processed, f)
        with open(self._save_path_knowledge, "w") as f:
            json.dump(self.semantic_knowledge, f)

    def get_nodes_and_event_by_event_id(self, month, event_id):
        nodes = []
        event = self.semantic_knowledge['events']['by_event'][month][event_id]
        event_start_date = event['start_date']
        try:
            event_start_date = datetime.datetime.strptime(event_start_date, "%Y-%m-%d")
        except:
            event_start_date = event_start_date.split(":")[0]
            event_start_date = datetime.datetime.strptime(event_start_date, "%Y")
        event_end_date = event['end_date']

        try:
            event_end_date = datetime.datetime.strptime(event_end_date, "%Y-%m-%d")
        except:
            event_end_date = event_end_date.split(":")[0]
            event_end_date = datetime.datetime.strptime(event_end_date, "%Y")
            
        for node in self.all_memory_nodes:
            if node.date.date() >= event_start_date.date() and node.date.date() <= event_end_date.date():
                nodes.append(node)

        return nodes, event


    def get_node_by_filename(self, filename):
        for node in self.all_memory_nodes:
            if node.filename == filename:
                return node
        return None

    def build(self, save_path_memory:str = "", save_path_knowledge:str = ""):
        self._save_path_memory = save_path_memory
        self._save_path_knowledge = save_path_knowledge
        # self._process_metadata()
        try:
            self._update_memory()
            self._update_knowledge()
        except Exception as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        
        print("Start saving...")
        self._save()
        print("Done!")
        