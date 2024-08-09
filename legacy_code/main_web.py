import pyrootutils
pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

import argparse
import json
import os
import time
import io
import base64

from flask import Flask, request, jsonify, send_file
from PIL import Image
from pillow_heif import register_heif_opener
register_heif_opener()

from src.memory.memory import MemoryBuilder
from src.memory.dataloader import MemoryDataLoader
from src.retriever.retriever import MemoryRetriever

app = Flask(__name__)

def initialize_memory(args):
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

    return memory

def initialize():
    parser = get_args_parser()
    global args
    args = parser.parse_args()

    global memory
    memory = initialize_memory(args)

    # return jsonify({"status": "Memory initialized"}), 200


def retrieve(query):
    if 'memory' not in globals():
        return jsonify({"error": "Memory not initialized"}), 400

    # data = request.get_json()
    # query = data.get('query', '')

    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    # global retriever
    retriever = MemoryRetriever(
        memory=memory,
        caption_embeddings_database=args.caption_embeddings_database,
        knowledge_embeddings_database = args.knowledge_embeddings_database,
    )

    start_time = time.time()
    retrieved_nodes, answer = retriever.retrieve(query)
    time_cost = time.time() - start_time
    cost = retriever.cost
    # print("Time cost: ", time.time() - start_time)

    result_filepaths = [node.filepath for node in retrieved_nodes]
    
    images_transer = []
    for path in result_filepaths:
        image = Image.open(path)
        img_io = io.BytesIO()
        image.save(img_io, 'JPEG')
        img_io.seek(0)
        img_based64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        images_transer.append(img_based64)

    result = {}
    time_cost = round(time_cost, 1)
    result['answer'] = answer
    result['images'] = images_transer
    result['time_cost'] = time_cost
    result['cost'] = cost

    return result

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

# if __name__ == "__main__":
#     app.run(debug=True)

# def main(args):
#     # input image, for each media in the folder, build memory node from it.
#     raw_data_folder = args.raw_data_folder

#     memory_data_loader = MemoryDataLoader(
#         memory_path=raw_data_folder
#     )

#     if not os.path.exists(args.memory):
#         with open(args.memory, "w") as f:
#             json.dump({}, f)
#             memory_processed = {}
#     else:
#         with open(args.memory, "r", encoding='utf-8') as f:
#             memory_processed = json.load(f)

#     if not os.path.exists(args.semantic_knowledge):
#         with open(args.semantic_knowledge, "w") as f:
#             json.dump({}, f)
#             semantic_knowledge = {}
#     else:
#         with open(args.semantic_knowledge, "r", encoding='utf-8') as f:
#             semantic_knowledge = json.load(f)
    
#     memory = MemoryBuilder(
#         memory_processed=memory_processed,
#         semantic_knowledge=semantic_knowledge,
#         memory_raw=memory_data_loader.memory_raw,
#         images_embedding_store=args.image_embeddings,
#         events_embedding_store=args.event_embeddings,
#         semantic_knowledge_embedding_store=args.semantic_knowledge_embeddings,
#         is_force_generate=False
#     )
#     memory.build(save_path_memory=args.memory, save_path_knowledge=args.semantic_knowledge)

#     # then
#     retriever = MemoryRetriever(
#         memory = memory,
#         caption_embeddings_database = args.caption_embeddings_database
#         )
#     # query = 'What was the name of the bar of Taiwan Night During CHI?'
#     query = "Name of the poke restaurant I ate during CHI"
#     # query = "Climbing between palm trees on Big Island."

#     start_time = time.time()
#     retrieved_nodes, answer = retriever.retrieve(query)
#     print("Time cost: ", time.time() - start_time)

#     result_filepaths = []
#     for node in retrieved_nodes:
#         result_filepaths.append(node.filepath)

#     print(answer)


# def get_args_parser():
#     parser = argparse.ArgumentParser(add_help=False)
#     parser.add_argument("--raw_data_folder", default="data/raw/version_2_nick", type=str)
#     parser.add_argument("--memory", default="data/memory_processed.json", type=str)
#     parser.add_argument("--semantic_knowledge", default="data/semantic_knowledge.json", type=str)


#     parser.add_argument("--image_embeddings", default="data/image_embeddings.json", type=str)
#     parser.add_argument("--event_embeddings", default="data/event_embeddings.json", type=str)
#     parser.add_argument("--semantic_knowledge_embeddings", default="data/semantic_knowledge_embeddings.json", type=str)

#     parser.add_argument("--caption_embeddings_database", default="data/caption_embeddings_database.json", type=str)

#     return parser

# def run_from_app():
#     parser = argparse.ArgumentParser("test", parents=[get_args_parser()])
#     args = parser.parse_args()
#     main(args)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser("test", parents=[get_args_parser()])
#     args = parser.parse_args()
#     main(args)
