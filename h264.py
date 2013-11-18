import sys
import tempfile
import subprocess

from bson import ObjectId
from gridfs import GridFS
from pymongo.read_preferences import ReadPreference

import settings
from app import get_db, fs
from actions.avconv import parse_stdout


db = get_db(read_preference=ReadPreference.SECONDARY)
fs = GridFS(db)

h264_videos = db.fs.files.find({
    'unistorage_type': 'video',
    'extra.video.codec': 'h264',
}, timeout=False)


c = 0
for video in h264_videos:
    video_id = video['_id']
    with tempfile.NamedTemporaryFile(mode='wb') as tmp_file:
        tmp_file.write(fs.get(video_id).read())
        tmp_file.flush()

        args = [settings.AVPROBE_BIN, '-print_format', 'json', '-show_format',
                '-show_streams', tmp_file.name]
        stdout, stderr = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate()
        stdout_data = parse_stdout(stdout)

        for stream in stdout_data['streams']:
            if stream.get('codec_type') == 'video':
                profile = stream.get('profile', '')

                if ('High' in profile) or not ('Base' in profile or 'Main' in profile):
                    print video_id, profile
    c += 1
    if not c % 250:
        print >> sys.stderr, '.',
