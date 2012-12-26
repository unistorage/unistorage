# -*- coding: utf-8 -*-
import re
import subprocess
import binascii
import tempfile
import os.path
from unicodedata import normalize

import magic
from werkzeug.datastructures import FileStorage

from actions.utils import get_unistorage_type
from actions.avconv import avprobe
import settings


m = magic.Magic(mime=True, magic_file=settings.MAGIC_FILE_PATH)


def secure_filename(filename):
    """Modified version of :func:`werkzeug.secure_filename`"""
    if isinstance(filename, unicode):
        filename = normalize('NFKC', filename)
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, '_')
    return re.sub(r'^\.+', '_', filename.strip(' '))


def identify(file, format):
    args = [settings.IDENTIFY_BIN, '-format', '%s\n' % format, '-']
    proc = subprocess.Popen(args, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc_input = file.read()
    file.seek(0)

    stdout_data, stderr_data = proc.communicate(input=proc_input)
    return stdout_data.split('\n')[0].strip()


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


def get_file_data(file, file_name=None):
    file.seek(0)
    file_content = file.read()
    file.seek(0)
    
    content_type = m.from_buffer(file_content)
    file.seek(0)
    data = {
        'filename': secure_filename(file_name),
        'content_type': content_type,
        'crc32': binascii.crc32(file_content)
    }

    inaccurate_unistorage_type = get_unistorage_type(content_type)
    inaccurate_extra = {}
    if inaccurate_unistorage_type in ('audio', 'video'):
        if isinstance(file, FileStorage) and hasattr(file.stream, 'name') and \
                os.path.exists(file.stream.name):
            inaccurate_extra = avprobe(file.stream.name)
        else:
            inaccurate_extra = get_avprobe_result(file_content, file_name=file_name)
    elif inaccurate_unistorage_type == 'image':
        try:
            image_format, image_size = identify(file, '%m %wx%h').split()
            image_width, image_height = map(int, image_size.split('x'))
            inaccurate_extra = {
                'format': image_format.lower(),
                'width': image_width,
                'height': image_height
            }
        except:
            pass

    unistorage_type = get_unistorage_type(content_type, extra=data.get('extra'))
    extra = {}
    if unistorage_type == 'audio':
        extra.update(inaccurate_extra['audio'])
        extra['format'] = inaccurate_extra['format']
    elif unistorage_type == 'video':
        extra = inaccurate_extra
    elif unistorage_type == 'image':
        extra = inaccurate_extra
        

    data.update({
        'extra': extra,
        'unistorage_type': unistorage_type
    })
    return data
