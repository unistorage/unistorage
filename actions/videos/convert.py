# -*- coding: utf-8 -*-
import os
import tempfile

from actions import ActionException
from actions.utils import ValidationError
from actions.common import validate_presence
from actions.avconv import avprobe, avconv
from actions.videos.utils import run_flvtool
from actions.common.codecs_validation import require_acodec_presence, require_vcodec_presence


name = 'convert'
applicable_for = 'video'
result_unistorage_type = 'video'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'to')
    format = args['to']

    supported_formats = ('ogg', 'webm', 'flv', 'avi', 'mkv', 'mov', 'mp4', 'mpg')
    if format not in supported_formats:
        raise ValidationError('Source file can be only converted to the one of '
                              'following formats: %s.' % ', '.join(supported_formats))

    vcodec = None
    acodec = None
    if format == 'ogg':
        vcodec = 'theora'
        acodec = 'vorbis'
    elif format == 'webm':
        vcodec = 'vp8'
        acodec = 'vorbis'

    vcodec = args.get('vcodec', vcodec)
    acodec = args.get('acodec', acodec)
    
    vcodec_restrictions = {
        'ogg': ('theora',),
        'webm': ('vp8',),
        'flv': ('h264', 'flv'),
        'mp4': ('h264', 'divx', 'mpeg1', 'mpeg2')
    }
    acodec_restrictions = {
        'ogg': ('vorbis',),
        'webm': ('vorbis',)
    }

    all_supported_vcodecs = ('theora', 'h264', 'vp8', 'divx', 'h263', 'flv', 'mpeg1', 'mpeg2')
    format_supported_vcodecs = vcodec_restrictions.get(format, all_supported_vcodecs)
    all_supported_acodecs = ('vorbis', 'mp3', 'aac')
    format_supported_acodecs = acodec_restrictions.get(format, all_supported_acodecs)
    
    if vcodec is None:
        raise ValidationError('`vcodec` must be specified.')
    elif vcodec not in format_supported_vcodecs:
        raise ValidationError('Format %s allows only following video codecs: %s' %
                              (format, ', '.join(format_supported_vcodecs)))
    if acodec is None:
        raise ValidationError('`acodec` must be specified.')
    elif acodec not in format_supported_acodecs:
        raise ValidationError('Format %s allows only following audio codecs: %s' %
                              (format, ', '.join(format_supported_acodecs)))
    
    if source_file:
        data = source_file.extra
        require_vcodec_presence(data['video']['codec'])
        if data['audio']:
            require_acodec_presence(data['audio']['codec'])

    return [format, vcodec, acodec]


def perform(source_file, format, vcodec, acodec, only_try=False):
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
            'video': {
                'codec': vcodec
            }
        }
        if vcodec in ('mpeg1', 'mpeg2', 'divx'):
            options['video']['fps'] = 25

        source_data = avprobe(tmp_source_file.name)

        if source_data['audio']:
            options['audio'] = {
                'codec': acodec,
                'sample_rate': 44100
            }

            channels = source_data['audio']['channels']
            if channels:
                if acodec == 'mp3' and channels > 2:
                    channels = 2
                options['audio']['channels'] = channels

        video_bitrate = source_data['video']['bitrate']
        if video_bitrate:
            options['video']['bitrate'] = video_bitrate

        result_file_name = avconv(tmp_source_file.name, tmp_target_file.name, options)
        result = open(result_file_name)
    finally:
        os.unlink(tmp_target_file.name)
        os.unlink(tmp_source_file.name)

    return result, format
