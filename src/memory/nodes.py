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
        for node_filename in memory_nodes_dict:
            node_dict = memory_nodes_dict[node_filename]
            
            node = MemoryNodeSingle(node_dict, is_build=False)
            self.node_list.append(node)

    def get_nodes(self):
        return self.node_list

class MemoryNodeSingle():
    def __init__(self,
                 params: dict = {},
                 is_build: bool = False) -> None:
        
        self.params = params
        self.multimodal_llm = OpenAIWrapper()

        self.cost = 0
        # ocr engine
        # whisper engine
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
        visual_content, self.cost = self.multimodal_llm.generate_visual_content(self.params['media'])
        text = detect_text(self.params['media'])

        content = {
            'caption': visual_content['caption'],
            'objects': visual_content['objects'],
            'people': visual_content['people'],
            'text': text
        }
        return content


    def _load(self):
        pass

    def _build(self):
        self.node_id = uuid.uuid4().hex

        self.metadata = self._get_metadata()
        self.content = self._get_content()
        self.events = None
        pass



class EventNode():
    def __init__(self) -> None:
        pass