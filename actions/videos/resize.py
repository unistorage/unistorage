# coding: utf-8
import os
import tempfile

from actions.common.resize_validation import validate_and_get_args \
    as common_resize_validate_and_get_args
from actions.avconv import avprobe, avconv


name = 'resize'
applicable_for = 'video'
validate_and_get_args = common_resize_validate_and_get_args


def get_result_unistorage_type(*args):
    return 'video'


def to_int(x):
    return int(round(x, 0))


def to_even(x):
    if x % 2 == 0:
        return x
    else:
        return x - 1


def perform(source_file, mode, target_width, target_height):
    file_content = source_file.read()
    with tempfile.NamedTemporaryFile() as source_tmp:
        source_tmp.write(file_content)
        source_tmp.flush()

        with tempfile.NamedTemporaryFile(mode='rb') as target_tmp:
            data = avprobe(source_tmp.name)

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

                vfilters = 'scale=%i:%i' % (to_even(width), to_even(height))
                if mode == 'crop':
                    vfilters += ',crop=%i:%i' % (to_even(target_width), to_even(target_height))

            data['video']['filters'] = vfilters
            result_file_name = avconv(source_tmp.name, target_tmp.name, data)
            return open(result_file_name), data['format']
