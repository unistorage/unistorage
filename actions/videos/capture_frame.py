# coding: utf-8
import os
import tempfile

from actions.utils import ValidationError
from actions.common import validate_presence
from actions.avconv import avconv, acodec_to_format_map
from actions.common.codecs_validation import require_acodec_presence
from actions.images.convert import perform as convert


name = 'capture_frame'
applicable_for = 'video'


def get_result_unistorage_type(*args):
    return 'video'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'to')
    format = args['to']

    ### XXX Проверка идентична той, что производится в actions.images.convert
    supported_formats = ('bmp', 'gif', 'jpeg', 'png', 'tiff')
    if format not in supported_formats:
        raise ValidationError('Frame can be only saved to the one of '
                              'following formats: %s.' % ', '.join(supported_formats))

    validate_presence(args, 'position')
    position = args['position']
    try:
        position = float(position)
    except ValueError:
        raise ValidationError('`position` must be numeric value.')

    if source_file:
        duration = source_file.extra['video']['duration']
        if position > duration:
            raise ValidationError('`position` must be less than video duration.')
    return [format, position]


def perform(source_file, format, position):
    tmp_source_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_source_file.write(source_file.read())
    tmp_source_file.close()

    tmp_target_file = tempfile.NamedTemporaryFile(suffix='.%s' % format, delete=False)
    tmp_target_file.close()
    
    try:
        options = {
            'format': 'image2',
            'video': {'frames': '1', 'codec': format},
            'position': '%.2f' % position
        }

        if format == 'gif':
            # При конвертации в GIF возникает ошибка:
            # No accelerated colorspace conversion found from yuv420p to rgb8.
            # Её исправление требует ручной компиляции ffmpeg, поэтому пока такой workaround.
            options['video']['codec'] = 'jpeg'

        result_file_name = avconv(tmp_source_file.name, tmp_target_file.name, options)
        result = open(result_file_name)
        
        if format == 'gif':
            # Продолжение workaround-а
            old_result = result
            result, ext = convert(old_result, 'gif')
            old_result.close()
    finally:
        os.unlink(tmp_target_file.name)
        os.unlink(tmp_source_file.name)

    return result, format
