import sys
import traceback
import tempfile
import subprocess
import fileinput

from bson import ObjectId
from gridfs import GridFS
from pymongo.read_preferences import ReadPreference

import settings
from app import get_db, fs, create_app
from actions.avconv import parse_stdout


app = create_app()
app.app_context().push()
db = get_db(read_preference=ReadPreference.SECONDARY)
fs = GridFS(db)


h264_videos = db.fs.files.find({
    'unistorage_type': 'video',
    'extra.video.codec': 'h264',
}, timeout=False)


skip_ids = set()
for line in fileinput.input('high.txt'):
    id, profile = line.split(' ', 1)
    skip_ids.add(id)


c = 0
for video in h264_videos:
    video_id = video['_id']

    if video_id in skip_ids:
        continue

    try:
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
    except:
        print >> sys.stderr, 'Something is wrong with {}:'.format(video_id)
        traceback.print_exc(file=sys.stderr)

    c += 1
    if not c % 250:
        print >> sys.stderr, '.',
