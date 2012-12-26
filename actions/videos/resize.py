# -*- coding: utf-8 -*-
import os
import tempfile

from actions.common import validate_presence
from actions.common.resize_validation import validate_and_get_args
from actions.videos.utils import run_flvtool
from actions.avconv import avprobe, avconv


name = 'resize'
applicable_for = 'video'
result_unistorage_type = 'video'


def to_int(x):
    return int(round(x, 0))


def to_even(x):
    if x % 2 == 0:
        return x
    else:
        return x - 1


def perform(source_file, mode, target_width, target_height):
    source_file_ext = ''
    if hasattr(source_file, 'filename'):
        source_file_name, source_file_ext = os.path.splitext(source_file.filename)  # XXX?

    file_content = source_file.read()
    with tempfile.NamedTemporaryFile(suffix=source_file_ext) as source_tmp:
        source_tmp.write(file_content)
        source_tmp.flush()

        with tempfile.NamedTemporaryFile(mode='rb') as target_tmp:
            data = avprobe(source_tmp.name)
            
            # TODO Разобраться с upscale
            if mode == 'resize':
                vfilters = 'scale=%i:%i' % (to_even(target_width), to_even(target_height))
            else:
                source_width = float(data['video']['width'])
                source_height = float(data['video']['height'])

                # If mode == 'keep', either target_width or target_height can be None
                factors = [target_width / source_width if target_width else 1,
                           target_height / source_height if target_height else 1]

                factor = max(factors) if mode == 'crop' else min(factors)
                width = to_int(source_width * factor)
                height = to_int(source_height * factor)

                if factor < 1:
                    vfilters = 'scale=%i:%i' % (to_even(width), to_even(height))

                    if mode == 'crop':
                        vfilters += ',crop=%i:%i' % (to_even(target_width), to_even(target_height))

            data['video']['filters'] = vfilters
            avconv(source_tmp.name, target_tmp.name, data)
            if data['format'] == 'flv':
                run_flvtool(target_tmp.name)
            return open(target_tmp.name), data['format']
