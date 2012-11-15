from actions.utils import ValidationError
from actions.avconv import get_codec_supported_actions


def require_acodec_presence(acodec_name, require_encoding_support=False):
    acodec = get_codec_supported_actions('audio', acodec_name)
    if not acodec or not acodec['decoding'] or \
            (require_encoding_support and not acodec['encoding']):
        raise ValidationError('Sorry, we can\'t handle audio stream '
                              'encoded using %s' % acodec_name)
    

def require_vcodec_presence(vcodec_name, require_encoding_support=False):
    vcodec = get_codec_supported_actions('video', vcodec_name)
    if not vcodec or not vcodec['decoding'] or \
            (require_encoding_support and not vcodec['encoding']):
        raise ValidationError('Sorry, we can\'t handle video stream '
                              'encoded using %s' % vcodec_name)
