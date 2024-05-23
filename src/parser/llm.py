from openai import OpenAI
from io import BytesIO
import base64
import json

class LLMWrapper():
    def __init__(self,
                 templates: str = None,
                 ) -> None:
        self.templates = templates

class OpenAIWrapper(LLMWrapper):
    def __init__(self,
                 templates: str = None,
                 ) -> None:
        super().__init__(templates)
        self.llm = OpenAI()
        self.model = 'gpt-4o'

    def _generate_messages(self):
        pass

    def _call_api(self, messages, json_mode=False):
        if json_mode:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=1000
            )
        else:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                max_tokens=1000
            )
        return response

    def generate_visual_content(self, image):
        system_prompt = f"Generate the following info from the image: caption that describe the image content, visible objects, people. Output a JSON object with key: 'caption', 'objects', 'people'."

        # create a base64 image
        buff = BytesIO()
        image.save(buff, format="JPEG")
        base64_img = base64.b64encode(buff.getvalue()).decode("utf-8")
        user_prompt = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "low"}}]
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

        response = self._call_api(messages, json_mode=True)
        prompt_token = response.usage.prompt_tokens
        generation_token = response.usage.completion_tokens
        cost = prompt_token*0.000005 + generation_token*0.0000015

        result = response.choices[0].message.content
        result = json.loads(result)

        return result, cost

    def generate_info(self, image):
        system_prompt = "Generate the following info from the image: caption, visible objects, people, text. Output a JSON object with key: 'caption', 'objects', 'people', 'text'."

