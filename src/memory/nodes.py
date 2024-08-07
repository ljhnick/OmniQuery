import uuid
import datetime

from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer, CLIPTextModel
from sklearn.metrics.pairwise import cosine_similarity
import torch

from utils.exif_utils import read_metadata_from_image
from src.parser.llm import OpenAIWrapper
from src.parser.ocr import detect_text

def get_model_info(model_ID, device):
    model = CLIPModel.from_pretrained(model_ID).to(device)
 	# Get the processor
    processor = CLIPProcessor.from_pretrained(model_ID)
    tokenizer = CLIPTokenizer.from_pretrained(model_ID)
    text_model = CLIPTextModel.from_pretrained(model_ID).to(device)
    return model, processor, tokenizer, text_model

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model_ID = "openai/clip-vit-base-patch32"
model, processor, tokenizer, text_model = get_model_info(model_ID, device)

class MemoryBuilderJson():
    def __init__(self,
                 memory_path) -> None:
        pass

class MemoryBuilderSingle():
    def __init__(self) -> None:
        self.multimodal_llm = OpenAIWrapper()
    
    def build_memory_dict(self, raw_memory_dict):
        memory_dict = {}
        memory_dict['nodes'] = self._build_memory_nodes(raw_memory_dict)
        return memory_dict

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
                 raw_info,
                 processed_info) -> None:
        self.raw_info = raw_info
        self.processed_info = processed_info

        self.multimodal_llm = OpenAIWrapper()
        self.cost = 0

        self._load()
        self._load_knowledge()

    def _load(self):
        self.filename = self.raw_info['filename']
        self.filepath = self.raw_info['filepath']
        self.media_type = self.raw_info['media_type']
        self.media = self.raw_info['media']

        self.processed_grouping = False
        self.has_parent = False

        if 'has_parent' in self.processed_info:
            if self.processed_info['has_parent'] == True:
                self.has_parent = True
                self.parent_node_name = self.processed_info['parent_node_name']

        if 'metadata' in self.processed_info:
            self.metadata = self.processed_info['metadata']
        if 'content' in self.processed_info:
            self.content = self.processed_info['content']
        

    def _load_knowledge(self):
        # self.is_processed_event = False
        # self.is_processed_activity = False
        # self.is_processed_general_knowledge = False

        self.is_processed_event = self.processed_info['is_processed_event'] if 'is_processed_event' in self.processed_info else False
        self.is_processed_activity = self.processed_info['is_processed_activity'] if 'is_processed_activity' in self.processed_info else False
        self.is_processed_general_knowledge = self.processed_info['is_processed_general_knowledge'] if 'is_processed_general_knowledge' in self.processed_info else False

        if 'events' in self.processed_info:
            self.events = self.processed_info['events']
        if 'semantic_knowledge' in self.processed_info:
            self.semantic_knowledge = self.processed_info['semantic_knowledge']

        self.activity = self.processed_info['activity'] if 'activity' in self.processed_info else None
        self.knowledge = self.processed_info['knowledge'] if 'knowledge' in self.processed_info else None
        
    def get_timestamp(self):
        if self.metadata is None:
            self._get_metadata()
        date = self.date
        return date

    def _get_metadata(self, forced_generation=False):
        if not hasattr(self, 'metadata') or forced_generation:
            metadata = read_metadata_from_image(self.media, self.filepath)
            self.metadata = metadata
        date = self.metadata['temporal_info']['date_string']
        date = datetime.datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
        self.date = date
        return self.metadata

    def get_metadata(self, forced_generation=False):
        return self._get_metadata(forced_generation)
    
    def _get_image_embeddings(self):
        image = processor(
            text = None,
            images = self.media,
            return_tensors="pt"
            )["pixel_values"].to(device)
        
        embedding = model.get_image_features(image)
        embedding_as_np = embedding.cpu().detach().numpy()
        embedding_as_np = embedding_as_np.tolist()
        self.image_embeddings = embedding_as_np
        return embedding_as_np

    def get_image_embeddings(self, image_embedding_store={}):
        self.image_embedding_store = image_embedding_store
        if self.filename in self.image_embedding_store:
            self.image_embeddings = self.image_embedding_store[self.filename]
        else:
            self._get_image_embeddings()
        return self.image_embeddings
        
    def group_with_similar_images(self, other_nodes):
        if self.processed_grouping == True:
            return
        for node in other_nodes:
            if node == self:
                break
            if node.has_parent == True:
                continue

            similarity = cosine_similarity(self.image_embeddings, node.image_embeddings)
            if self.metadata['capture_method'] == 'photo':
                threshold = 0.85
            else:
                threshold = 0.95
            if similarity[0][0] > threshold:
                self.has_parent = True
                self.parent_node_name = node.filename
                break
        self.processed_grouping = True
    
    def _get_content(self):
        if self.has_parent == True:
            return None
        image = self.media
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
            
    
    def get_content(self, image_embedding_store={}):
        if hasattr(self, 'content'):
            if self.content is not None:
                return
        content = self._get_content()
        self.content = content
    
    def export_dict(self, path=""):
        memory = {}
        memory['filename'] = self.filename
        memory['filepath'] = self.filepath
        memory['media_type'] = self.media_type
        
        if hasattr(self, 'metadata'):
            memory['metadata'] = self.metadata

        if self.has_parent == True:
            memory['has_parent'] = True
            memory['parent_node_name'] = self.parent_node_name
        else:
            memory['has_parent'] = False

        memory['is_processed_event'] = self.is_processed_event
        memory['is_processed_activity'] = self.is_processed_activity
        memory['is_processed_general_knowledge'] = self.is_processed_general_knowledge

        memory['activity'] = self.activity if hasattr(self, 'activity') else None
        memory['knowledge'] = self.knowledge if hasattr(self, 'knowledge') else None

        if hasattr(self, 'content'):
            memory['content'] = self.content
        if hasattr(self, 'events'):
            memory['events'] = self.events
        if hasattr(self, 'semantic_knowledge'):
            self.semantic_knowledge['is_processed_event'] = self.is_processed_event
            self.semantic_knowledge['is_processed_activity'] = self.is_processed_activity
            self.semantic_knowledge['is_processed_general_knowledge'] = self.is_processed_general_knowledge
            memory['semantic_knowledge'] = self.semantic_knowledge
        return memory
    
    def textualize_memory(self):
        output = ""
        time = self.metadata['temporal_info']
        location = self.metadata['location']['address'] if 'address' in self.metadata['location'] else "Unknown"
        capture_method = self.metadata['capture_method']
        content = self.content

        output += f"Captured time: {time}\n"
        output += f"Captured location: {location}\n"
        output += f"Capture method: {capture_method}\n"
        output += f"Content:\n"
        for key, value in content.items():
            output += f"{key}: {value}\n"
        return output

class MemoryNodeSingleOld():
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