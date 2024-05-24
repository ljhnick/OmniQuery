import pyrootutils
pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

import argparse
import json


from src.memory.memory import MemoryBuilder
from src.memory.dataloader import MemoryDataLoader
from src.retriever.retriever import MemoryRetriever


def main(args):
    # input image, for each media in the folder, build memory node from it.
    raw_data_folder = args.raw_data_folder

    memory_data_loader = MemoryDataLoader(
        memory_path=raw_data_folder
    )

    with open(args.memory, "r", encoding='utf-8') as f:
        memory_processed = json.load(f)
    
    memory = MemoryBuilder(
        memory_processed=memory_processed,
        memory_raw=memory_data_loader.memory_raw,
        events_embedding_store=args.event_embeddings,
        semantic_knowledge_embedding_store=args.semantic_knowledge_embeddings
    )
    memory.build(save_path='data/memory_processed.json')

    # then
    retriver = MemoryRetriever(memory)
    # query = retriver.query("find me a photo of a cat")
    # response = ResponseGenerator(query)


def get_args_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--raw_data_folder", default="data/raw/version_2_nick", type=str)
    parser.add_argument("--memory", default="data/memory_processed.json", type=str)

    parser.add_argument("--event_embeddings", default="data/event_embeddings.json", type=str)
    parser.add_argument("--semantic_knowledge_embeddings", default="data/semantic_knowledge_embeddings.json", type=str)

    return parser

if __name__ == "__main__":
    parser = argparse.ArgumentParser("test", parents=[get_args_parser()])
    args = parser.parse_args()
    main(args)