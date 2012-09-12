import string
import os.path

import magic
import kaa.metadata

import settings


MAGIC_PATH = '%s:%s' % (os.path.abspath('./magic.mgc'), settings.MAGIC_PATH)


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


def get_content_type(file):
    m = magic.Magic(mime=True, magic_file=MAGIC_PATH)
    file.seek(0)
    content_type = m.from_buffer(file.read(2048))
    file.seek(0)
    return content_type


def get_file_data(file):
    file.seek(0)
    data = {
        'filename': convert_to_filename(file.filename),
        'content_type': get_content_type(file),
    }

    metadata = kaa.metadata.parse(file)
    file.seek(0)

    if metadata and handlers.has_key(metadata.media):
        get_fileinfo = handlers[metadata.media]
        fileinfo = get_fileinfo(metadata.convert())
        data['fileinfo'] = fileinfo
    
    return data
