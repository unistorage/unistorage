# coding: utf-8
import re
import subprocess
import binascii
import tempfile
import os.path
from unicodedata import normalize

import magic
import newrelic.agent
from werkzeug.datastructures import FileStorage

import settings
from actions.utils import get_unistorage_type
from actions.avconv import avprobe
from identify import identify_buffer


m = magic.Magic(mime=True, keep_going=True,
                magic_file=settings.MAGIC_FILE_PATH)


def secure_filename(filename):
    """Modified version of :func:`werkzeug.secure_filename`"""
    if isinstance(filename, unicode):
        filename = normalize('NFKC', filename)
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, '_')
    return re.sub(r'^\.+', '_', filename.strip(' '))


def get_content_type(file):
    file.seek(0)
    content_type = m.from_buffer(file.read())
    file.seek(0)
    return content_type


def get_avprobe_result(file_content, file_name=None):
    with tempfile.NamedTemporaryFile(mode='wb') as tmp_file:
        tmp_file.write(file_content)
        tmp_file.flush()
        return avprobe(tmp_file.name)


@newrelic.agent.function_trace()
def get_unistorage_type_and_extra(file, file_name, file_content, content_type):
    inaccurate_unistorage_type = get_unistorage_type(content_type, file_name=file_name)
    inaccurate_extra = {}
    if inaccurate_unistorage_type in ('audio', 'video'):
        if isinstance(file, FileStorage) and hasattr(file.stream, 'name') and \
                os.path.exists(file.stream.name):
            inaccurate_extra = avprobe(file.stream.name)
        else:
            inaccurate_extra = get_avprobe_result(file_content, file_name=file_name)
    elif inaccurate_unistorage_type == 'image':
        try:
            inaccurate_extra = identify_buffer(file_content)
        except:
            pass

    unistorage_type = get_unistorage_type(content_type, file_name=file_name,
                                          extra=inaccurate_extra)
    extra = {}
    if unistorage_type == 'audio':
        extra.update(inaccurate_extra['audio'])
        extra['format'] = inaccurate_extra['format']
    elif unistorage_type == 'video':
        extra = inaccurate_extra
    elif unistorage_type == 'image':
        extra = inaccurate_extra

    return {
        'unistorage_type': unistorage_type,
        'extra': extra,
    }


@newrelic.agent.function_trace()
def get_file_data(file, file_name=None):
    file.seek(0)
    file_content = file.read()
    file.seek(0)
    
    content_type = m.from_buffer(file_content)
    file.seek(0)

    data = {
        'filename': secure_filename(file_name),
        'crc32': binascii.crc32(file_content)
    }
    data.update(get_unistorage_type_and_extra(
        file, file_name, file_content, content_type))
    
    if content_type == 'application/ogg':
        if data['unistorage_type'] == 'video':
            content_type = 'video/ogg'
        elif data['unistorage_type'] == 'audio':
            content_type = 'audio/ogg'
    data['content_type'] = content_type

    return data
