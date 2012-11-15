name = 'convert'
applicable_for = 'audio'
result_type_family = 'audio'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'to')
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
    all_supported_acodecs = ('vorbis', 'mp3')
    format_supported_acodecs = acodec_restrictions.get(format, all_supported_acodecs)
    
    if vcodec is None:
        raise ValidationError('`vcodec` must be specified.')
    elif vcodec not in format_supported_vcodecs:
        raise ValidationError('Format %s allows only following video codecs: %s' %
                              (format, ', '.join(format_supported_vcodecs)))
    if acodec is None:
        raise ValidationError('`acodec` must be specified.')
    elif acodec not in format_supported_acodecs:
        raise ValidationError('Format %s allows only following audio codecs: %s' %
                              (format, ', '.join(format_supported_acodecs)))
    
    if source_file:
        validate_source(source_file)

    return [format, vcodec, acodec]

