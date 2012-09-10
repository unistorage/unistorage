import os
import tempfile
import subprocess

from converter import Converter

import settings
from actions import ActionException
from actions.utils import *


name = 'convert'
applicable_for = 'video'
result_type_family = 'video'


def validate_and_get_args(args):
    if 'to' not in args:
        raise ValidationError('`to` must be specified.')
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
    all_supported_acodecs =  ('vorbis', 'mp3')
    format_supported_acodecs = acodec_restrictions.get(format, all_supported_acodecs)
    
    if vcodec is None:
        raise ValidationError('vcodec must be specified.')
    elif vcodec not in format_supported_vcodecs:
        raise ValidationError('Format %s allows only following video codecs: %s' % \
                (format, ', '.join(format_supported_vcodecs)))
    if acodec is None:
        raise ValidationError('acodec must be specified.')
    elif acodec not in format_supported_acodecs:
        raise ValidationError('Format %s allows only following audio codecs: %s' % \
                (format, ', '.join(format_supported_acodecs)))

    return [format, vcodec, acodec]


def perform(source_file, format, vcodec, acodec, only_try=False):
    tmp_source_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_source_file.write(source_file.read())
    tmp_source_file.close()

    tmp_target_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_target_file.close()
    
    options = {
        'format': format,
        'audio': {'codec': acodec},
        'video': {'codec': vcodec}
    }
    options['audio']['samplerate'] = 44100
    if vcodec in ('mpeg1', 'mpeg2', 'divx'):
        options['video']['fps'] = '25'

    try:
        c = Converter(ffmpeg_path=settings.FFMPEG_BIN, ffprobe_path=settings.FFPROBE_BIN)
        convertion = c.convert(tmp_source_file.name, tmp_target_file.name, options)
        for timecode in convertion:
            if only_try:
                break
        
        if format == 'flv':
            try:
                proc = subprocess.Popen([settings.FLVTOOL_BIN, '-U', tmp_target_file.name],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as e:
                raise ActionException('Failed to start flvtool: %s' % settings.FLVTOOL_BIN)
            _, stderr = proc.communicate()
            return_code = proc.wait()
            if return_code != 0:
                raise ActionException('flvtool (%s) failed. Stderr: %s' % (settings.FLVTOOL_BIN, stderr))

        result = open(tmp_target_file.name)
    finally:
        os.unlink(tmp_target_file.name)
        os.unlink(tmp_source_file.name)

    return result, format
