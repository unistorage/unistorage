import tempfile
import os
import subprocess

from converter import Converter


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

    c = Converter()
    convertion = c.convert(tmp_source_file.name, tmp_target_file.name, options)
    for timecode in convertion:
        if only_try:
            break
    
    if format == 'flv':
        proc = subprocess.Popen(['flvtool2', '-U', tmp_target_file.name],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return_code = proc.wait() # TODO assert return_code == 0

    result = open(tmp_target_file.name)
    os.unlink(tmp_target_file.name)
    os.unlink(tmp_source_file.name)
    return result
