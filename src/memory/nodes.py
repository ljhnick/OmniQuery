import uuid

from utils.exif_utils import read_metadata_from_image
from src.parser.llm import OpenAIWrapper
from src.parser.ocr import detect_text

class MemoryNodesBuilder():
    def __init__(self,
                 memory_nodes_dict: dict) -> None:
        self.node_list = []
        self._build_memory_nodes(memory_nodes_dict)
    
    def _build_memory_nodes(self, memory_nodes_dict):
        for node_dict in memory_nodes_dict:
            node = MemoryNodeSingle(node_dict, is_build=False)
            self.node_list.append(node)
        # for node_filename in memory_nodes_dict:
        #     node_dict = memory_nodes_dict[node_filename]
            
        #     node = MemoryNodeSingle(node_dict, is_build=False)
        #     self.node_list.append(node)

    def get_nodes(self):
        return self.node_list

class MemoryNodeSingle():
    def __init__(self,
                 params: dict = {},
                 is_build: bool = False) -> None:
        
        self.cost = 0
        
        self.params = params
        self.events_dict = {}
        self.event_ids = []
        self.knowledge_ids = []

        self.multimodal_llm = OpenAIWrapper()

        if not is_build:
            self._load()
        else:
            self._build()

    def _get_metadata(self):
        image = self.params['media']
        self.image = image

        filepath = self.params['filepath']
        metadata = read_metadata_from_image(image, filepath)
        return metadata
    
    def _get_content(self):
        # get caption, objects, people, text
        image = self.params['media']
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        visual_content, cost = self.multimodal_llm.generate_visual_content(image)
        text = detect_text(image)

        self.cost += cost

        content = {
            'caption': visual_content['caption'],
            'objects': visual_content['objects'],
            'people': visual_content['people'],
            'text': text
        }
        return content
    
    def _get_events(self):
        # get events from the multimodal llm
        related_events, cost = self.multimodal_llm.generate_events_from_content(self.content)
        self.cost += cost
        
        return related_events
    
    def _get_semantic_knowledge(self):
        semantic_knowledge, cost = self.multimodal_llm.generate_semantic_knowledge_from_content(self.metadata, self.content)
        self.cost += cost
        # print(semantic_knowledge)
        return semantic_knowledge

    def _load(self):
        # params should include
        # {"memory": {"metadata":, "content":, "events": , "semantic_knowledge": }, "node_id":, "event_ids"}
        try:
            processed_dict = self.params['processed_memory']
        except Exception as e:
            print(e)
            self._build()

        self.node_id = processed_dict['node_id']
        self.metadata = processed_dict['memory']['metadata']
        self.content = processed_dict['memory']['content']
        self.events = processed_dict['memory']['events']
        self.semantic_knowledge = processed_dict['memory']['semantic_knowledge']
        self.event_ids = processed_dict['event_ids']
        self.knowledge_ids = processed_dict['knowledge_ids']

        self._processed_params = self._get_dict()
        return

    def _build(self):
        self.node_id = uuid.uuid4().hex
        self.metadata = self._get_metadata()
        self.content = self._get_content()
        self.events = self._get_events()
        self.semantic_knowledge = self._get_semantic_knowledge()

        print(self.semantic_knowledge)
        
        self._processed_params = self._get_dict()
    
    def _get_dict(self):
        node_dict = {}
        memory = {}
        memory['metadata'] = self.metadata
        memory['content'] = self.content
        memory['events'] = self.events
        memory['semantic_knowledge'] = self.semantic_knowledge
        node_dict['memory'] = memory

        node_dict['node_id'] = self.node_id
        node_dict['event_ids'] = self.event_ids
        node_dict['knowledge_ids'] = self.knowledge_ids

        save_params = self.params.copy()
        save_params['media'] = None
        save_params['processed_memory'] = node_dict
        return save_params
    
    def get_dict(self):
        return self._processed_params



class EventNode():
    def __init__(self) -> None:
        pass