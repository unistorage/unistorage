import os
import tempfile

from actions.common import validate_presence
from actions.common.resize_validation import validate_and_get_args
from actions.videos.utils import run_flvtool
from actions.avconv import avprobe, avconv


name = 'resize'
applicable_for = 'video'
result_unistorage_type = 'video'


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
            avconv(source_tmp.name, target_tmp.name, data)
            if data['format'] == 'flv':
                run_flvtool(target_tmp.name)
            return open(target_tmp.name), data['format']
