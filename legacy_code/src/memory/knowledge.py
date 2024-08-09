from typing import List
from collections import defaultdict
from tqdm import tqdm


from src.memory.nodes import MemoryNodeSingle
from src.parser.llm import OpenAIWrapper




class MemoryKnowledgeBuilder():
    def __init__(self,
                 memory_nodes: List[MemoryNodeSingle],
                 semantic_processed: dict) -> None:
        self.memory_nodes = memory_nodes
        self.semantic_knowledge = semantic_processed

        self.multimodal_llm = OpenAIWrapper()
        self.cost = 0

        # if 'semantic_knowledge' in semantic_processed:
        # self.semantic_knowledge = semantic_processed['semantic_knowledge']
        if 'events' not in self.semantic_knowledge:
            self.semantic_knowledge['events'] = {}
            if 'by_date' not in self.semantic_knowledge['events']:
                self.semantic_knowledge['events']['by_date'] = {}
            if 'by_event' not in self.semantic_knowledge['events']:
                self.semantic_knowledge['events']['by_event'] = {}
        

    def _build_events(self):
        # group the nodes by date first
        nodes_grouped_by_date = defaultdict(list)
        for memory_node in self.memory_nodes:
            date_key = memory_node.date.date()
            date_key = str(date_key)
            nodes_grouped_by_date[date_key].append(memory_node)

        event_dict_by_date = {}
        print("Building events...")
        for date, nodes, in tqdm(nodes_grouped_by_date.items()):
            date = str(date)
            if date in self.semantic_knowledge['events']['by_date']:
                event_dict_by_date[date] = self.semantic_knowledge['events']['by_date'][date]
                continue
            # extract the events from the nodes
            result, cost = self.multimodal_llm.generate_events_from_multi_nodes(nodes)
            self.cost += cost
            event_dict_by_date[date] = result
        
        self.semantic_knowledge['events']['by_date'] = event_dict_by_date
    
    def _filter_events(self):
        # group the events by a month
        events_dict_by_date = self.semantic_knowledge['events']['by_date']
        events_dict_by_month = defaultdict(list)

        filtered_events = {}
        for date, events in events_dict_by_date.items():
            month = date.split('-')[0] + '-' + date.split('-')[1]
            events_dict_by_month[month].append(events)
    
        print("Filtering events...")
        for month, events in tqdm(events_dict_by_month.items()):
            if month in self.semantic_knowledge['events']['by_event']:
                filtered_events[month] = self.semantic_knowledge['events']['by_event'][month]
                continue
            result, cost = self.multimodal_llm.filter_events(events)
            self.cost += cost
            filtered_events[month] = result

        event_list = []
        for month in filtered_events:
            # self.semantic_knowledge['events']['by_event'][month] = True
            try:
                event_list.extend(filtered_events[month]['events'])
            except:
                event_list.extend(filtered_events[month])

        for i, event in enumerate(event_list):
            event['id'] = i
        self.semantic_knowledge['events']['by_event'][month] = event_list
        return
    
    def _build_activities_and_general_knowledge(self):

        activity_list = []
        knowledge_list = []
        print("Building activities and general knowledge...")
        for memory_node in tqdm(self.memory_nodes[:]):
            if memory_node.is_processed_activity and memory_node.is_processed_general_knowledge:
                activity = memory_node.activity if hasattr(memory_node, 'activity') else None
                knowledge = memory_node.knowledge if hasattr(memory_node, 'knowledge') else None
                memory_name = memory_node.filename
                if activity != "":
                    activity_node = {'activity': activity, 'memory_name': memory_name}
                    activity_list.append(activity_node)
                for k in knowledge:
                    knowledge_node = {'knowledge': k, 'memory_name': memory_name}
                    knowledge_list.append(knowledge_node)
                continue
            if memory_node.has_parent:
                continue
            memory_node.is_processed_activity = True
            memory_node.is_processed_general_knowledge = True
            result, cost = self.multimodal_llm.generate_acitivity_and_knowledge(node=memory_node, events=self.semantic_knowledge['events'])

            activity = result['activity']
            knowledge = result['knowledge']
            memory_node.activity = activity
            memory_node.knowledge = knowledge

            memory_name = memory_node.filename
            if activity != "":
                activity_node = {'activity': activity, 'memory_name': memory_name}
                activity_list.append(activity_node)
            for k in knowledge:
                knowledge_node = {'knowledge': k, 'memory_name': memory_name}
                knowledge_list.append(knowledge_node)

            self.cost += cost

        for i, activity in enumerate(activity_list):
            activity['id'] = i
        for i, knowledge in enumerate(knowledge_list):
            knowledge['id'] = i

        self.semantic_knowledge['activity'] = activity_list
        self.semantic_knowledge['knowledge'] = knowledge_list
        return
    
    def export_knowledge_dict(self):
        return self.semantic_knowledge

        

    def build(self):
        # build the events first
        self._build_events()
        self._filter_events()

        self._build_activities_and_general_knowledge()

        return