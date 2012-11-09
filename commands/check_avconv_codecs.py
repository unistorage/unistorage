import cPickle as pickle

import settings


def check_avconv_codecs():
    "Check that avconv supports all necessary codecs and formats"
    with open(settings.AVCONV_DB_PATH) as f:
        avconv_db = pickle.load(f)

    vcodecs = (
        'vp8', 'libvpx',
        'theora', 'libtheora',
        'h264', 'libx264',
        'mpeg4', 'h263', 'h263p',
        'mpeg1video', 'mpeg2video', 'flv'
    )

    acodecs = (
        'vorbis', 'libvorbis',
        'amrnb', 'libopencore_amrnb',
        'mp3', 'libmp3lame',
        'aac'
    )

    formats = ('ogg', 'webm', 'flv', 'avi', 'matroska', 'mov', 'mp4', 'mpeg')
    
    return_code = 0
    for vcodec in vcodecs:
        if vcodec not in avconv_db['vcodecs']:
            print 'Video codec `%s` is missing' % vcodec
            return_code = 1

    for acodec in acodecs:
        if acodec not in avconv_db['acodecs']:
            print 'Audio codec `%s` is missing' % acodec
            return_code = 1
    
    for format in formats:
        if format not in avconv_db['formats']:
            print 'Format `%s` is missing' % format
            return_code = 1

    exit(return_code)
