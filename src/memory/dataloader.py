import os
from PIL import Image
from pillow_heif import register_heif_opener
register_heif_opener()

from utils.exif_utils import read_metadata_from_image


class MemoryDataLoader():
    img_ext_list = ["jpg", "jpeg", "png", "heic"]
    video_ext_list = ["mp4", "mov", "avi"]

    def __init__(self,
                 memory_path) -> None:
        self.memory_path = memory_path
        self.memory_raw = {}
        self._load_data()

    def _load_data(self):
        files = os.listdir(self.memory_path)
        for file in files:
            if file == ".DS_Store":
                continue
            ext = file.split('.')[-1]
            if ext.lower() in self.img_ext_list:
                filepath = os.path.join(self.memory_path, file)
                media_type = 'image'
                media = Image.open(filepath)
            elif ext.lower() in self.video_ext_list:
                filepath = os.path.join(self.memory_path, file)
                media_type = 'video'
                # sample a few images from the video
                continue


            local_dict = {}
            local_dict['filename'] = file
            local_dict['filepath'] = filepath
            local_dict['media_type'] = media_type
            local_dict['media'] = media

            self.memory_raw[file] = local_dict