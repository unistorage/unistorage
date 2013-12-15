# coding: utf-8
import re
import subprocess
import binascii
import tempfile
import os.path
from unicodedata import normalize
from cStringIO import StringIO

import magic
import newrelic.agent
from werkzeug.datastructures import FileStorage
from pyPdf import PdfFileReader

import settings
from actions.utils import get_unistorage_type
from actions.avconv import avprobe, avprobe_buffer
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


def get_content_type_from_buffer(data):
    return m.from_buffer(data)


def get_content_type(file):
    file.seek(0)
    content_type = get_content_type_from_buffer(file.read())
    file.seek(0)
    return content_type


@newrelic.agent.function_trace()
def get_unistorage_type_and_extra(file, file_name, file_content, content_type):
    inaccurate_extra = {}
    inaccurate_unistorage_type = \
        get_unistorage_type(content_type, file_name=file_name)

    try:
        if inaccurate_unistorage_type in ('audio', 'video', 'unknown'):
            if isinstance(file, FileStorage) and hasattr(file.stream, 'name') and \
                    os.path.exists(file.stream.name):
                inaccurate_extra = avprobe(file.stream.name)
            else:
                inaccurate_extra = avprobe_buffer(file_content)
    except:
        pass
    try:
        if inaccurate_unistorage_type in ('image', 'unknown'):
            inaccurate_extra = inaccurate_extra or identify_buffer(file_content)
    except:
        pass

    extra = inaccurate_extra
    unistorage_type = get_unistorage_type(content_type, extra=extra, file_name=file_name)
    if unistorage_type == 'audio':
        extra.update(inaccurate_extra['audio'])
        extra['format'] = inaccurate_extra['format']
    elif unistorage_type == 'doc':
        if content_type == 'application/pdf':
            extra = {
                'pages': PdfFileReader(StringIO(file_content)).getNumPages(),
            }

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
        'crc32': binascii.crc32(file_content),
    }
    data.update(get_unistorage_type_and_extra(
        file, file_name, file_content, content_type))



    if content_type == 'application/ogg':
        if data['unistorage_type'] == 'video':
            content_type = 'video/ogg'
        elif data['unistorage_type'] == 'audio':
            content_type = 'audio/ogg'
    if content_type.endswith('octet-stream'):
        if data['unistorage_type'] == 'video':
            if data['extra']['format'] in ('mov', 'mp4', 'm4a'):
                content_type = 'video/mp4'
    data['content_type'] = content_type

    return data

