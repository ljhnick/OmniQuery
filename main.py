import pyrootutils
pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

import argparse
import json
import os


from src.memory.memory import MemoryBuilder
from src.memory.dataloader import MemoryDataLoader
from src.retriever.retriever import MemoryRetriever


def main(args):
    # input image, for each media in the folder, build memory node from it.
    raw_data_folder = args.raw_data_folder

    memory_data_loader = MemoryDataLoader(
        memory_path=raw_data_folder
    )

    if not os.path.exists(args.memory):
        with open(args.memory, "w") as f:
            json.dump({}, f)
            memory_processed = {}
    else:
        with open(args.memory, "r", encoding='utf-8') as f:
            memory_processed = json.load(f)
    
    memory = MemoryBuilder(
        memory_processed=memory_processed,
        memory_raw=memory_data_loader.memory_raw,
        images_embedding_store=args.image_embeddings,
        events_embedding_store=args.event_embeddings,
        semantic_knowledge_embedding_store=args.semantic_knowledge_embeddings,
        is_force_generate=False
    )
    memory.build(save_path=args.memory)

    # then
    retriver = MemoryRetriever(memory)
    # query = retriver.query("find me a photo of a cat")
    # response = ResponseGenerator(query)


def get_args_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--raw_data_folder", default="data/raw/version_2_nick", type=str)
    parser.add_argument("--memory", default="data/memory_processed.json", type=str)

    parser.add_argument("--image_embeddings", default="data/image_embeddings.json", type=str)
    parser.add_argument("--event_embeddings", default="data/event_embeddings.json", type=str)
    parser.add_argument("--semantic_knowledge_embeddings", default="data/semantic_knowledge_embeddings.json", type=str)

    return parser

def run_from_app():
    parser = argparse.ArgumentParser("test", parents=[get_args_parser()])
    args = parser.parse_args()
    main(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("test", parents=[get_args_parser()])
    args = parser.parse_args()
    main(args)
