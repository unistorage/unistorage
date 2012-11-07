# -*- coding: utf-8 -*-
import string
import binascii
import tempfile
import os.path

import magic
import kaa.metadata
from kaa.metadata.factory import Factory, R_CLASS
from werkzeug.datastructures import FileStorage

from actions.videos.avconv import avprobe
import settings


m = magic.Magic(mime=True, magic_file=settings.MAGIC_FILE_PATH)


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


handlers = {
    kaa.metadata.MEDIA_IMAGE: get_image_info,
    kaa.metadata.MEDIA_AUDIO: get_audio_info
}


def get_metadata_parser(file):
    """Модификация :func:`kaa.metadata.factory.Factory.create_from_file`, не полагающаяся на
    наличие поле `name` у `file`.
    """
    factory = Factory()
    parser = None
    file.seek(0, 0)
    magic = file.read(10)
    for length, magicmap in factory.magicmap.items():
        if magic[:length] in magicmap:
            for p in magicmap[magic[:length]]:
                file.seek(0, 0)
                try:
                    parser = factory.get_class(p[R_CLASS])
                    return parser(file)
                except:
                    pass
            return None

    for e in factory.types:
        if factory.get_class(e[R_CLASS]) == parser:
            continue
        file.seek(0, 0)
        try:
            return factory.get_class(e[R_CLASS])(file)
        except:
            pass
    return None


def get_metadata(file):
    """Аналог функции :func:`kaa.metadata.factory.parse`. Всегда использует
    :func:`get_metadata_parser` для выбора парсера метаданных."""
    result = get_metadata_parser(file)
    if result:
        result._finalize()
    return result


def convert_to_filename(name):
    valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
    return ''.join(c for c in name if c in valid_chars)


def get_content_type(file):
    file.seek(0)
    content_type = m.from_buffer(file.read())
    file.seek(0)
    return content_type


def get_video_data(file_content, file_name=None):
    with tempfile.NamedTemporaryFile(mode='wb') as tmp_file:
        tmp_file.write(file_content)
        tmp_file.flush()
        return avprobe(tmp_file.name)


def get_file_data(file, file_name=None):
    file.seek(0)
    file_content = file.read()
    file.seek(0)

    data = {
        'filename': convert_to_filename(file_name),
        'content_type': m.from_buffer(file_content),
        'crc32': binascii.crc32(file_content)
    }

    metadata = get_metadata(file)
    file.seek(0)

    if metadata:
        if metadata.media == kaa.metadata.MEDIA_AV:
            if isinstance(file, FileStorage) and \
                    hasattr(file.stream, 'name') and \
                    os.path.exists(file.stream.name):
                video_data = avprobe(file.stream.name)
            else:
                video_data = get_video_data(file_content, file_name=file_name)
            data['fileinfo'] = video_data
        elif metadata.media in handlers:
            get_fileinfo = handlers[metadata.media]
            fileinfo = get_fileinfo(metadata.convert())
            data['fileinfo'] = fileinfo
    return data
