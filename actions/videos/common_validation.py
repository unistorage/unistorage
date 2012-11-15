from actions.utils import ValidationError
from actions.videos.avconv import get_codec_supported_actions


def validate_source(source_file, require_encoding_support=False):
    data = source_file.extra
    if not data['video'] or not data['audio']:
        raise ValidationError('Source video file must contain at least one '
                              'audio and video stream')
    
    acodec_name = data['audio']['codec']
    acodec = get_codec_supported_actions('audio', acodec_name)
    if not acodec or not acodec['decoding'] or \
            (require_encoding_support and not acodec['encoding']):
        raise ValidationError('Sorry, we can\'t handle audio stream '
                              'encoded using %s' % acodec_name)
    
    vcodec_name = data['video']['codec']
    vcodec = get_codec_supported_actions('video', vcodec_name)
    if not vcodec or not vcodec['decoding'] or \
            (require_encoding_support and not vcodec['encoding']):
        raise ValidationError('Sorry, we can\'t handle video stream '
                              'encoded using %s' % vcodec_name)
