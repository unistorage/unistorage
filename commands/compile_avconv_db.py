# coding: utf-8
import re
import cPickle as pickle
from collections import defaultdict

import sh

import settings


def noop(*args, **kwargs):
    pass


def parse_decoder(line, decoders):
    m = re.match(r'(?P<decoder_type>V|A|S)'
                 r'(?:F|\.)(?:S|\.)(?:X|\.)'
                 r'(?:B|\.)(?:D|\.)\s*'
                 r'(?P<decoder_name>\w+)', line)
    decoders.append({
        'type': m.group('decoder_type'),
        'name': m.group('decoder_name'),
    })


def parse_decoders(stream):
    decoders = []

    parse = noop
    for line in stream:
        # Выкидываем пробел из начала и перевод строки из конца:
        line = line[1:-1]
        if not line:
            parse = noop

        parse(line, decoders)
        
        if line == '------':
            parse = parse_decoder

    return decoders


def parse_encoder(line, encoders):
    m = re.match(r'(?P<encoder_type>V|A|S)'
                 r'(?:F|\.)(?:S|\.)(?:X|\.)'
                 r'(?:B|\.)(?:D|\.)\s*'
                 r'(?P<encoder_name>\w+)', line)
    encoders.append({
        'type': m.group('encoder_type'),
        'name': m.group('encoder_name'),
    })


def parse_encoders(stream):
    encoders = []

    parse = noop
    for line in stream:
        # Выкидываем пробел из начала и перевод строки из конца:
        line = line[1:-1]
        if not line:
            parse = noop

        parse(line, encoders)
        
        if line == '------':
            parse = parse_encoder

    return encoders


def make_avconv_db(decoders, encoders, formats):
    default = lambda: {'decoding': False, 'encoding': False}
    vcodecs = defaultdict(default)
    acodecs = defaultdict(default)

    for decoder in decoders:
        type_ = decoder['type']
        name = decoder['name']
        if type_ == 'V':
            vcodecs[name]['decoding'] = True
        if type_ == 'A':
            acodecs[name]['decoding'] = True
    
    for encoder in encoders:
        type_ = encoder['type']
        name = encoder['name']
        if type_ == 'V':
            vcodecs[name]['encoding'] = True
        if type_ == 'A':
            acodecs[name]['encoding'] = True

    return {
        'acodecs': acodecs,
        'vcodecs': vcodecs,
        'formats': formats,
    }


def parse_format(line, formats):
    m = re.match(r'^(?P<decoding>D|\s)'
                 r'(?P<encoding>E|\s)\s'
                 r'(?P<format_names>[\w,]+)', line)

    decoding_supported = m.group('decoding') == 'D'
    encoding_supported = m.group('encoding') == 'E'

    for format_name in m.group('format_names').split(','):
        format = formats[format_name]
        format['decoding'] = format['decoding'] or decoding_supported
        format['encoding'] = format['encoding'] or encoding_supported


def parse_formats(stream):
    parse = noop
    formats = defaultdict(lambda: {'decoding': False, 'encoding': False})

    for line in stream:
        line = line[1:-1]
        if not line:
            parse = noop
        
        parse(line, formats)

        if line == '--':
            parse = parse_format

    return formats


def compile_avconv_db():
    """Compile avconv database"""
    assert sh.which(settings.AVCONV_BIN)
    avconv = sh.Command(settings.AVCONV_BIN)

    decoders = parse_decoders(avconv('-decoders'))
    encoders = parse_decoders(avconv('-decoders'))
    formats = parse_formats(avconv('-formats'))

    data = make_avconv_db(decoders, encoders, formats)
    with open(settings.AVCONV_DB_PATH, 'w') as avconv_db:
        pickle.dump(data, avconv_db)
