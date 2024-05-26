from PIL import Image
from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer, CLIPTextModel
from sklearn.metrics.pairwise import cosine_similarity
import torch

from pillow_heif import register_heif_opener
register_heif_opener()

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

    
def get_single_image_embedding(my_image):
    image = processor(
		text = None,
		images = my_image,
		return_tensors="pt"
		)["pixel_values"].to(device)
    
    embedding = model.get_image_features(image)
    embedding_as_np = embedding.cpu().detach().numpy()
    return embedding_as_np

image_path1 = "/Users/jiahaoli/Library/CloudStorage/Dropbox/02_Career/Projects/2024_OmniQuery/data/raw/version_2_nick/IMG_9079.PNG"
image_path2 = "/Users/jiahaoli/Library/CloudStorage/Dropbox/02_Career/Projects/2024_OmniQuery/data/raw/version_2_nick/IMG_8779.PNG"

image1 = Image.open(image_path1)
image2 = Image.open(image_path2)

image1_embedding = get_single_image_embedding(image1)
image2_embedding = get_single_image_embedding(image2)

similarity = cosine_similarity(image1_embedding, image2_embedding)
print(similarity)