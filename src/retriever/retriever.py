import json
import os
import numpy as np

from tqdm import tqdm
import time

from src.memory.memory import MemoryBuilder
from src.parser.llm import OpenAIWrapper

class MemoryRetriever():
    def __init__(self,
                 memory: MemoryBuilder = None,
                 caption_embeddings_database: str = "",
                 knowledge_embeddings_database: str = "",
                 top_k = 10) -> None:
        self.memory = memory
        self.caption_em_path = caption_embeddings_database
        self.knowledge_em_path = knowledge_embeddings_database
        if os.path.exists(caption_embeddings_database):
            with open(caption_embeddings_database, "r") as f:
                self.caption_em = json.load(f)
        else:
            self.caption_em = {}

        if os.path.exists(knowledge_embeddings_database):
            with open(knowledge_embeddings_database, "r") as f:
                self.knowledge_em = json.load(f)
        else:
            self.knowledge_em = {}

        self.llm = OpenAIWrapper()
        self.top_k = top_k
        self._generate_caption_em_database()
        self._generate_semantic_knowledge_em_database()

        self.cost = 0
        
    def _generate_caption_em_database(self):
        all_nodes = self.memory.all_memory_nodes
        print("Generating caption embeddings database...")
        for node in tqdm(all_nodes):
            if node.filename not in self.caption_em:
                if node.has_parent:
                    continue
                caption = node.content['caption']
                em = self.llm.calculate_embeddings(caption)
                self.caption_em[node.filename] = em
        
        with open(self.caption_em_path, "w") as f:
            json.dump(self.caption_em, f)

    def _generate_semantic_knowledge_em_database(self):

        all_semantic_knowledge = self.memory.semantic_knowledge['knowledge']
        for each_semantic_knowledge in tqdm(all_semantic_knowledge):
            memory_name = each_semantic_knowledge['memory_name']
            knowledge_id = each_semantic_knowledge['id']
            knowledge_id = str(knowledge_id)
            if knowledge_id not in self.knowledge_em:
                knowledge = each_semantic_knowledge['knowledge']
                em = self.llm.calculate_embeddings(knowledge)
                self.knowledge_em[knowledge_id] = {'memory_name': memory_name, 'knowledge': knowledge, 'embeddings': em}
        with open(self.knowledge_em_path, "w") as f:
            json.dump(self.knowledge_em, f)



    def retrieve(self, query):
        # parse the query first
        # query type: retrieval (retrieve the related media), or query (asking a question, return the answer and reference media)

        # query filtering: 1. does it mention events? 2. does it mention activity? these two are used to filtering memory
        # query searching: 1. search the captions for media related to the query. 2. search for the semantic knowledge related to the query. 
        # if it is a query, retrieve the media and semantic knowledge and use llm to generate the answer.

        query_type, cost = self.llm.identify_query_type(query)
        # result_event_act, cost = self.llm.identify_event_activity(query)

        self.cost += cost

        start_time = time.time()

        query_em = self.llm.calculate_embeddings(query)
        # search the caption embeddings database
        retrieved_media = {}
        for filename, em in self.caption_em.items():
            similarity = np.dot(query_em, em) / (np.linalg.norm(query_em) * np.linalg.norm(em))
            emb = self.caption_em[filename]
            self.caption_em[filename] = {'embeddings': emb, 'similarity': similarity}
        # sort
        sorted_caption_em = sorted(self.caption_em.items(), key=lambda x: x[1]['similarity'], reverse=True)
        top_k_nodes = [self.memory.get_node_by_filename(x[0]) for x in sorted_caption_em[:self.top_k]]

        # search the semantic knowledge embeddings database
        for idx, em_dict in self.knowledge_em.items():
            id_key = str(idx)
            em = em_dict['embeddings']
            similarity = np.dot(query_em, em) / (np.linalg.norm(query_em) * np.linalg.norm(em))
            self.knowledge_em[id_key]['similarity'] = similarity
        # sort
        sorted_knowledge_em = sorted(self.knowledge_em.items(), key=lambda x: x[1]['similarity'], reverse=True)
        top_k_knowledge = sorted_knowledge_em[:self.top_k]

        # filter knowledge that is related to the query
        knowledge_related_to_query, cost = self.llm.filter_knowledge_related_to_query(query, top_k_knowledge)
        self.cost += cost

        knowledge_related_to_query = knowledge_related_to_query['knowledge']
        nodes_knowledge = [] # this will be used for the final nodes
        knowledge_list = []
        for knowledge_each in knowledge_related_to_query:
            k_id = knowledge_each['knowledge_id']
            k_id = str(k_id)
            relatedness = knowledge_each['relatedness']
            if relatedness < 2:
                continue
            knowledge_name = self.knowledge_em[k_id]['knowledge']
            knowledge_list.append(knowledge_name)
            memory_name = self.knowledge_em[k_id]['memory_name']
            node_knowledge = self.memory.get_node_by_filename(memory_name)
            nodes_knowledge.append(node_knowledge)
        

        # filter event
        events = self.memory.semantic_knowledge['events']['by_event']
        related_events, cost = self.llm.filter_related_event(query, events)
        self.cost += cost

        # print(f"time cost: {time.time() - start_time}")

        nodes = []
        filtered_events = []
        for related_event in related_events['events']:
            if related_event['relatedness'] >= 2:
                month = related_event['month']
                # get the media
                nodes_in_event, event_full = self.memory.get_nodes_and_event_by_event_id(month, event_id=related_event['event_id'])
                nodes.extend(nodes_in_event)
                filtered_events.append(event_full)
    

        if nodes == []:
            nodes_within_events = top_k_nodes
        else:
            nodes_within_events = [node for node in top_k_nodes if node in nodes]
        related_nodes, cost = self.llm.filter_nodes_related_to_query(query, nodes_within_events)
        self.cost += cost

        related_nodes = related_nodes['nodes']
        nodes_episodic = []
        for related_node in related_nodes:
            index = related_node['node_id']
            relatedness = related_node['relatedness']
            if relatedness < 2:
                continue
            nodes_episodic.append(nodes_within_events[index])
        # final_nodes = [nodes_within_events[ids['node_id']] for ids in related_nodes_id]

        nodes_knowledge.extend(nodes_episodic)
        final_nodes = nodes_knowledge
        final_nodes = set(final_nodes)

        if query_type == 'retrieval':
            return final_nodes, None
        else:
            # generate the answer
            answer, cost = self.llm.generate_answer(query, final_nodes, filtered_events, knowledge=knowledge_list)
            self.cost += cost
            return final_nodes, answer
