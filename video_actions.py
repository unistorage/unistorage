import tempfile
import os
import subprocess

from converter import Converter

import settings
from tasks import ActionException


def convert(source_file, format, vcodec, acodec, only_try=False):
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
