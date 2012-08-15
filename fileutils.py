import string

import kaa.metadata
from flask import g


def get_image_info(metadata):
    fileinfo = {}
    for key in ('width', 'height'):
        fileinfo[key] = metadata[key]
    return fileinfo

def get_audio_info(metadata):
    fileinfo = {}
    for key in ('codec', 'length'):
        fileinfo[key] = metadata[key]
    return fileinfo

def get_video_info(metadata):
    fileinfo = {}
    video = metadata['video'][0]
    for key in ('width', 'height', 'codec', 'length'):
        fileinfo[key] = video[key]
    return fileinfo

handlers = {
    kaa.metadata.MEDIA_IMAGE: get_image_info,
    kaa.metadata.MEDIA_AUDIO: get_audio_info,
    kaa.metadata.MEDIA_AV: get_video_info
}

def convert_to_filename(name):
    valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
    return ''.join(c for c in name if c in valid_chars)

def get_file_data(file):
    file.seek(0)
    data = {
        'filename': convert_to_filename(file.filename),
        'content_type': g.magic.from_buffer(file.read(1024))
    }
    file.seek(0)

    metadata = kaa.metadata.parse(file)
    file.seek(0)

    if metadata and handlers.has_key(metadata.media):
        get_fileinfo = handlers[metadata.media]
        fileinfo = get_fileinfo(metadata.convert())
        data['fileinfo'] = fileinfo
    
    return data
