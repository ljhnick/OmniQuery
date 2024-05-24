
generate_visual_content = "Generate the following info from the image: caption that describe the image content, visible objects, people. Output a JSON object with key: 'caption', 'objects', 'people'."

generate_events = "Based on the context, list EVENTS inferred for the image owner, ranging from major occurrences like conferences or travel to minor activities like dining out or walking. Be precise and concise. Output the list of events in a JSON object with key: 'events'."

generate_semantic_knowledge = """Based on the metadata and context, reason and generate high-level semantic knowledge, such as a person's birthday, in the format "X verb Y," like "Jerry's birthday is on March 2nd." 
Avoid specific details about individual media, such as the locations or actions. Focus on general semantic memory.
If an image shows a receipt, instead repeating what was on the receipt, output "I ate at a restaurant in XX during YY".
Output a list of semantic knowledge in a JSON object with the key 'semantic_knowledge'.
"""
# generate_semantic_knowledge = """Based on the metadata and context, reason and generate high-level semantic knowledge, such as a person's birthday, in the format "X verb Y", like "Jerry's birthday is on March 2nd." If no significant information is found, do not repeat the provided information. Output a list of semantic knowledge in a JSON object with the key 'semantic_knowledge'.
# """

compare_similarity = "Compare the similarity between the two texts. Rate from 1-10, 1 being completely different and 10 being identical. Output the similarity score only."

def merge_templates_to_dict() -> dict:
    template_dict = {
        'prompt_visual_content': generate_visual_content,
        'prompt_events': generate_events,
        'prompt_semantic_knowledge': generate_semantic_knowledge,
        'prompt_compare_similarity': compare_similarity,
    }

    return template_dict