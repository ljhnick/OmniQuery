import pyrootutils
pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

import argparse
import json
import os
import time

from flask import Flask, request, jsonify

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

    if not os.path.exists(args.semantic_knowledge):
        with open(args.semantic_knowledge, "w") as f:
            json.dump({}, f)
            semantic_knowledge = {}
    else:
        with open(args.semantic_knowledge, "r", encoding='utf-8') as f:
            semantic_knowledge = json.load(f)
    
    memory = MemoryBuilder(
        memory_processed=memory_processed,
        semantic_knowledge=semantic_knowledge,
        memory_raw=memory_data_loader.memory_raw,
        images_embedding_store=args.image_embeddings,
        events_embedding_store=args.event_embeddings,
        semantic_knowledge_embedding_store=args.semantic_knowledge_embeddings,
        is_force_generate=False
    )
    memory.build(save_path_memory=args.memory, save_path_knowledge=args.semantic_knowledge)

    # then
    retriever = MemoryRetriever(
        memory = memory,
        caption_embeddings_database = args.caption_embeddings_database,
        knowledge_embeddings_database = args.knowledge_embeddings_database,
        )
    # query = 'What was the name of the bar of Taiwan Night During CHI?'
    query = "Name of the poke restaurant I ate during CHI"
    # query = "Climbing between palm trees on Big Island."

    # query = "Who is Zijian Ding?"
    # query = "How long did I stay in Hawaii?"
    # query = "Where is Hancheng Cao going to be a professor"
    # query = "When is the presentation of OmniActions"

    start_time = time.time()
    retrieved_nodes, answer = retriever.retrieve(query)
    print("Time cost: ", time.time() - start_time)
    cost = retriever.cost
    print("Cost: ", cost)

    result_filepaths = []
    for node in retrieved_nodes:
        result_filepaths.append(node.filepath)

    print(answer)
    print(1)


def get_args_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--raw_data_folder", default="data/raw/version_2_nick", type=str)
    parser.add_argument("--memory", default="data/memory_processed.json", type=str)
    parser.add_argument("--semantic_knowledge", default="data/semantic_knowledge.json", type=str)


    parser.add_argument("--image_embeddings", default="data/image_embeddings.json", type=str)
    parser.add_argument("--event_embeddings", default="data/event_embeddings.json", type=str)
    parser.add_argument("--semantic_knowledge_embeddings", default="data/semantic_knowledge_embeddings.json", type=str)

    parser.add_argument("--caption_embeddings_database", default="data/caption_embeddings_database.json", type=str)
    parser.add_argument("--knowledge_embeddings_database", default="data/knowledge_embeddings_database.json", type=str)

    return parser

def run_from_app():
    parser = argparse.ArgumentParser("test", parents=[get_args_parser()])
    args = parser.parse_args()
    main(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("test", parents=[get_args_parser()])
    args = parser.parse_args()
    main(args)
