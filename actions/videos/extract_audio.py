# -*- coding: utf-8 -*-
import os
import tempfile

from actions.utils import ValidationError
from actions.common import validate_presence
from actions.avconv import avconv, acodec_to_format_map
from actions.common.codecs_validation import require_acodec_presence


name = 'extract_audio'
applicable_for = 'video'
result_unistorage_type = 'audio'


# XXX Код ниже почти один-в-один совпадает с кодом из actions/audios/convert.py.

def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'to')
    codec = args['to']

    supported_codecs = ('alac', 'aac', 'vorbis', 'ac3', 'mp3', 'flac')
    if codec not in supported_codecs:
        raise ValidationError('Source file can be only converted to the one of '
                              'following formats: %s.' % ', '.join(supported_codecs))

    if source_file:
        data = source_file.extra
        if not data['audio']:
            raise ValidationError('Source file has no audio stream.')
        require_acodec_presence(data['audio']['codec'])

    return [codec]


def perform(source_file, codec):
    format = acodec_to_format_map[codec]

    source_file_ext = ''
    if hasattr(source_file, 'filename'):
        source_file_name, source_file_ext = os.path.splitext(source_file.filename)

    tmp_source_file = tempfile.NamedTemporaryFile(suffix=source_file_ext, delete=False)
    tmp_source_file.write(source_file.read())
    tmp_source_file.close()

    tmp_target_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_target_file.close()
    
    try:
        options = {
            'format': format,
            'audio': {
                'codec': codec,
                'sample_rate': 44100
            }
        }
        avconv(tmp_source_file.name, tmp_target_file.name, options)
        result = open(tmp_target_file.name)
    finally:
        os.unlink(tmp_target_file.name)
        os.unlink(tmp_source_file.name)

    return result, format
