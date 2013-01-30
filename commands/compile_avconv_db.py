import re
import cPickle as pickle
from functools import partial
from collections import defaultdict

import sh

import settings


vcodecs = defaultdict(dict)
acodecs = defaultdict(dict)
formats = defaultdict(partial(dict, [
    ('encoding', False),
    ('decoding', False)
]))


def noop(line):
    pass


def parse_codec(line):
    m = re.match(r'^(?P<decoding>D|\.)'
                 r'(?P<encoding>E|\.)'
                 r'(?P<codec_type>V|A|S|\.)'
                 r'(?:I|\.)(?:L|\.)(?:S|\.)\s*'
                 r'(?P<codec_name>\w+)', line)
    codec_name = m.group('codec_name')
    codec_type = m.group('codec_type')

    decoding_supported = m.group('decoding') == 'D'
    encoding_supported = m.group('encoding') == 'E'
    actions_supported = {
        'decoding': decoding_supported,
        'encoding': encoding_supported
    }
    if codec_type == 'V':
        vcodecs[codec_name] = actions_supported
    elif codec_type == 'A':
        acodecs[codec_name] = actions_supported
# V..... = Video
 #A..... = Audio
 #S..... = Subtitle
 #.F.... = Frame-level multithreading
 #..S... = Slice-level multithreading
 #...X.. = Codec is experimental
 #....B. = Supports draw_horiz_band
 #.....D = Supports direct rendering method 1


def parse_decoder(line):
    m = re.match(r'(?P<decoder_type>V|A|S)'
                 r'(?:F|\.)'
                 r'(?:S|\.)'
                 r'(?:X|\.)'
                 r'(?:B|\.)'
                 r'(?:D|\.)\s*'
                 r'(?P<decoder_name>\w+)', line)
    decoder_type = m.group('decoder_type')
    decoder_name = m.group('decoder_name')

    decoding_supported = m.group('decoding') == 'D'
    encoding_supported = m.group('encoding') == 'E'
    actions_supported = {
        'decoding': decoding_supported,
        'encoding': encoding_supported
    }
    if codec_type == 'V':
        vcodecs[codec_name] = actions_supported
    elif codec_type == 'A':
        acodecs[codec_name] = actions_supported


def parse_codecs(avconv):
    parse = noop
    for line in avconv('-codecs'):
        line = line[1:-1]

        if not line:
            parse = noop
        parse(line)
        
        if line == '-------':
            parse = parse_codec


def parse_format(line):
    m = re.match(r'^(?P<decoding>D|\s)'
                 r'(?P<encoding>E|\s)\s'
                 r'(?P<format_names>[\w,]+)', line)

    decoding_supported = m.group('decoding') == 'D'
    encoding_supported = m.group('encoding') == 'E'

    for format_name in m.group('format_names').split(','):
        format = formats[format_name]
        format['decoding'] = format['decoding'] or decoding_supported
        format['encoding'] = format['encoding'] or encoding_supported


def parse_formats(avconv):
    parse = noop
    for line in avconv('-formats'):
        line = line[1:-1]

        parse(line)

        if line == '--':
            parse = parse_format


def compile_avconv_db():
    """Compile avconv database"""
    assert sh.which(settings.AVCONV_BIN)
    avconv = sh.Command(settings.AVCONV_BIN)

    parse_codecs(avconv)
    parse_formats(avconv)
    data = {
        'acodecs': acodecs,
        'vcodecs': vcodecs,
        'formats': dict(formats)
    }
    with open(settings.AVCONV_DB_PATH, 'w') as avconv_db:
        pickle.dump(data, avconv_db)

