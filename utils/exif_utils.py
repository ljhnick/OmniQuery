import os
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
register_heif_opener()

from geopy.geocoders import Nominatim
from datetime import datetime

def convert_gps_to_degree(gps):
    gps = eval(gps)
    d = gps[0]
    m = gps[1]
    s = gps[2]
    return d + (m / 60.0) + (s / 3600.0)

# def read_date_time_from_image(image):
#     exif = image._getexif()
#     exif = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
#     date_time = exif.get('DateTimeOriginal')
#     return date_time

def get_time_of_the_day(hour):
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Afternoon"
    elif 18 <= hour < 23:
        return "Evening"
    else:
        return "Night"

def parse_date_time(exif=None, date_time_string=""):
    if date_time_string == "":
        date_time = exif.get('DateTime')
        if date_time is None:
            date_time = exif.get('DateTimeOriginal')
            if date_time is None:
                return None
    else:
        date_time = date_time_string
    
    date_time_object = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
    day_of_week = date_time_object.strftime('%A')
    time_of_the_day = get_time_of_the_day(date_time_object.hour)

    date_info = {
        'date_string': date_time,
        'day_of_week': day_of_week,
        'time_of_the_day': time_of_the_day
    }
    return date_info

def extract_date_time_modified(filepath=""):
    modification_time = os.path.getmtime(filepath)
    modification_time_readable = datetime.fromtimestamp(modification_time).strftime('%Y:%m:%d %H:%M:%S')
    return modification_time_readable

def read_GPS_from_image(image):
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

    if geo_tagging_info == {}:
        return {}

    latitude_ref = geo_tagging_info['GPSLatitudeRef']
    latitude = geo_tagging_info['GPSLatitude']
    latitude = convert_gps_to_degree(latitude)
    if latitude_ref == 'S':
        latitude = -latitude
    longitude_ref = geo_tagging_info['GPSLongitudeRef']
    longitude = geo_tagging_info['GPSLongitude']
    longitude = convert_gps_to_degree(longitude)
    if longitude_ref == 'W':
        longitude = -longitude
    
    gps = (latitude, longitude)
    geolocator = Nominatim(user_agent="omniquery")
    location = geolocator.reverse(f"{latitude}, {longitude}")
    address = location.address
    address_split = address.split(', ')
    address_split.reverse()

    location_info = {}
    location_info['gps'] = gps
    location_info['address'] = address

    label_list = ['country', 'zip', 'state', 'county', 'city']
    for i, label in enumerate(label_list):
        if i >= len(address_split):
            break
        location_info[label] = address_split[i]

    return location_info

def read_metadata_from_image(image, filepath=""):
    try:
        exif_info = image._getexif()
    except:
        exif_info = image.getexif()
    exif = {ExifTags.TAGS.get(k, k): v for k, v in exif_info.items()}
    
    if 'GPSInfo' in exif:
        gps_data = read_GPS_from_image(image)
    else:
        gps_data = {}

    if 'DateTimeOriginal' in exif or 'DateTime' in exif:
        temporal_data = parse_date_time(exif)
    else:
        date_time = extract_date_time_modified(filepath)
        temporal_data = parse_date_time(exif=None, date_time_string=date_time)
    
    metadata = {
        'temporal_info': temporal_data,
        'location': gps_data
    }
    
    return metadata