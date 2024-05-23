import pyrootutils
pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

from PIL import Image, ExifTags
from pillow_heif import register_heif_opener

from exif import Image as ExifImage
from geopy.geocoders import Nominatim

register_heif_opener()

image = Image.open("data/raw/version_1_nick/IMG_8600.HEIC")
# exif = { ExifTags.TAGS[k]: v for k, v in image._getexif().items() if k in ExifTags.TAGS }

exifdata = image.getexif()

image_info = image.getexif().get_ifd(0x8825)

geo_tagging_info = {}
gps_keys = ['GPSVersionID', 'GPSLatitudeRef', 'GPSLatitude', 'GPSLongitudeRef', 'GPSLongitude',
            'GPSAltitudeRef', 'GPSAltitude', 'GPSTimeStamp', 'GPSSatellites', 'GPSStatus', 'GPSMeasureMode',
            'GPSDOP', 'GPSSpeedRef', 'GPSSpeed', 'GPSTrackRef', 'GPSTrack', 'GPSImgDirectionRef',
            'GPSImgDirection', 'GPSMapDatum', 'GPSDestLatitudeRef', 'GPSDestLatitude', 'GPSDestLongitudeRef',
            'GPSDestLongitude', 'GPSDestBearingRef', 'GPSDestBearing', 'GPSDestDistanceRef', 'GPSDestDistance',
            'GPSProcessingMethod', 'GPSAreaInformation', 'GPSDateStamp', 'GPSDifferential']

for k, v in image_info.items():
    try:
        geo_tagging_info[gps_keys[k]] = str(v)
    except IndexError:
        pass

print(geo_tagging_info)

geolocator = Nominatim(user_agent="omniquery")
location = geolocator.reverse("33.542194, -116.784936")
print(location)




# for tag_id in exifdata:
#     tag = ExifTags.TAGS.get(tag_id, tag_id)
#     data = exifdata.get(tag_id)
#     if tag == "GPSInfo":
#         print(1)
#     if isinstance(data, bytes):
#         data = data.decode()
#     print(f"{tag:25}: {data}")


image_info_flat = image.getexif().get_ifd(0x8769)
print(image_info_flat)

exif_info = image._getexif()
exif = {ExifTags.TAGS.get(k, k): v for k, v in exif_info.items()}
print(exif)

# if exif_info is None:
#     print('Sorry, image has no exif data.')
# else:
#     for key, val in exif_info.items():
#         if key in ExifTags.TAGS:
#             print(f'{ExifTags.TAGS[key]}:{val}')
#         else:
#             print(f'{key}:{val}')

# def print_exif_data(exif_data):
#     for tag_id in exif_data:
#         tag = ExifTags.TAGS.get(tag_id, tag_id)
#         content = exif_data.get(tag_id)
#         print(f'{tag:25}: {content}')

# import exifread

# with open("data/raw/version_1_nick/IMG_8914.JPG", "rb") as f:
#     tags = exifread.process_file(f)
    
# for tag in tags.keys():
#     if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
#         print("Key: %s, value %s" % (tag, tags[tag]))

# with Image.open("data/raw/version_1_nick/IMG_8600.HEIC") as im:
#     exif = im.getexif()
    
#     print_exif_data(exif)
#     print()
#     print_exif_data(exif.get_ifd(0x8769))


import os
from datetime import datetime
from PIL import Image, ExifTags

def get_file_times(file_path):
    creation_time = os.path.getctime(file_path)
    modification_time = os.path.getmtime(file_path)
    creation_time_readable = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
    modification_time_readable = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
    return creation_time_readable, modification_time_readable

def print_exif_data(image_path):
    image = Image.open(image_path)
    exifdata = image.getexif()
    
    if not exifdata:
        print("No EXIF metadata found.")
        return

    for tag_id in exifdata:
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        data = exifdata.get(tag_id)
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                data = "<binary data>"
        print(f"{tag:25}: {data}")

# Example usage
image_path = "data/raw/version_1_nick/IMG_9077.JPG"

# Print EXIF data
print_exif_data(image_path)

# Print file creation and modification times
creation_time, modification_time = get_file_times(image_path)
print(f"Creation Time: {creation_time}")
print(f"Modification Time: {modification_time}")