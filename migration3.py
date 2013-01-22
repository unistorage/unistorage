import file_utils
from wsgi import app
from app import db, fs


def update_bitrate(set_spec, extra, video_or_audio):
    assert video_or_audio in ('video', 'audio')
    bitrate = extra[video_or_audio]['bitrate']
    if bitrate:
        if isinstance(bitrate, basestring) and bitrate.endswith('k'):
            bitrate_int = int(bitrate.rstrip('k')) * 1000
            set_spec.update({'extra.%s.bitrate' % video_or_audio: bitrate_int})
        elif isinstance(bitrate, int):
            pass
        else:
            print 'Strange `extra.%s.bitrate`: %s' % (video_or_audio, bitrate)
    else:
        print '`extra.%s.bitrate` is None!' % video_or_audio


with app.app_context():
    files_to_update = db.fs.files.find({
        'pending': False,
        'unistorage_type': 'video'
    }, timeout=False)

    count = files_to_update.count()
    for i, _file in enumerate(files_to_update):
        _id = _file['_id']
        print 'Processing video %s (%i/%i)' % (_id, i, count)

        set_spec = {}
        extra = _file['extra']
        if extra['video']:
            update_bitrate(set_spec, extra, 'video')
        if extra['audio']:
            update_bitrate(set_spec, extra, 'video')
        print set_spec

        db.fs.files.update({'_id': _id}, {
           '$set': set_spec
        })
        print 'OK'
    

    files_to_update = db.fs.files.find({
        'pending': False,
        'unistorage_type': 'audio'
    })
    count = files_to_update.count()
    for i, _file in enumerate(files_to_update):
        _id = _file['_id']
        print 'Processing audio %s (%i/%i)' % (_id, i, count)

        set_spec = {}
        extra = _file['extra']
        bitrate = extra['bitrate']
        if bitrate:
            if isinstance(bitrate, basestring) and bitrate.endswith('k'):
                bitrate_int = int(bitrate.rstrip('k')) * 1000
                set_spec.update({'extra.bitrate': bitrate_int})
            elif isinstance(bitrate, int):
                pass
            else:
                print 'Strange `extra.bitrate`: %s' % bitrate
        else:
            print '`extra.bitrate` is None!'
        print set_spec

        db.fs.files.update({'_id': _id}, {
           '$set': set_spec
        })
        print 'OK'
