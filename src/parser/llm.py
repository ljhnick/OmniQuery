from openai import OpenAI
from io import BytesIO
import base64
import json

from src.parser.prompt_templates import merge_templates_to_dict

class LLMWrapper():
    def __init__(self,
                 templates: dict = None,
                 ) -> None:
        self.templates = merge_templates_to_dict() if templates is None else templates

class OpenAIWrapper(LLMWrapper):
    def __init__(self,
                 templates: str = None,
                 ) -> None:
        super().__init__(templates)
        self.llm = OpenAI()
        self.model = 'gpt-4o'

    def _generate_messages(self):
        pass

    def _call_api(self, messages, json_mode=False, model=""):
        if model == "":
            model = self.model

        if json_mode:
            response = self.llm.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=1000
            )
        else:
            response = self.llm.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=1000
            )

        if model == 'gpt-4o':
            rate = 0.000005
        elif model == 'gpt-3.5-turbo-0125':
            rate = 0.0000005
        prompt_token = response.usage.prompt_tokens
        generation_token = response.usage.completion_tokens
        cost = prompt_token*rate + generation_token*rate*3
        result = response.choices[0].message.content

        return response, result, cost

    def generate_visual_content(self, image):
        system_prompt = self.templates['prompt_visual_content']

        # create a base64 image
        buff = BytesIO()
        if image.mode == "RGBA":
            image = image.convert("RGB")
        image.save(buff, format="JPEG")
        base64_img = base64.b64encode(buff.getvalue()).decode("utf-8")
        user_prompt = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "low"}}]
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

        _, result, cost = self._call_api(messages, json_mode=True)
        result = json.loads(result)

        return result, cost

    def generate_events_from_content(self, content):
        system_prompt = self.templates['prompt_events']

        content_str = ""
        for key, value in content.items():
            if key == 'text':
                continue
            content_str += f"{key}: {value}\n"

        user_prompt = content_str
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        response, result, cost = self._call_api(messages, json_mode=True)
        result = json.loads(result)

        return result, cost
    
    def generate_semantic_knowledge_from_content(self, metadata, content):
        system_prompt = self.templates['prompt_semantic_knowledge']

        metadata_str = ""
        metadata_str += f"Captured date: {metadata['temporal_info']['date_string']}, {metadata['temporal_info']['day_of_week']} {metadata['temporal_info']['time_of_the_day']}\n"
        try:
            metadata_str += f"Captured location: {metadata['location']['address']}\n"
        except:
            metadata_str += "Captured location: Unknown (screenshot or saved from online)\n"

        content_str = ""
        for key, value in content.items():
            content_str += f"{key}: {value}\n"

        user_prompt = metadata_str + content_str
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        response, result, cost = self._call_api(messages, json_mode=True)
        result = json.loads(result)

        return result, cost

    def compare_similarity(self, text1, text2):
        system_prompt = self.templates['prompt_compare_similarity']
        user_prompt = f"text1: {text1}\ntext2: {text2}"
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        response, result, cost = self._call_api(messages, json_mode=False, model='gpt-3.5-turbo-0125')
        return result, cost
    
    def calculate_embeddings(self, text, model="text-embedding-3-small"):
        if text == "":
            return None
        return self.llm.embeddings.create(input = [text], model=model).data[0].embedding