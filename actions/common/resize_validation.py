from actions.common import validate_presence
from actions.utils import ValidationError


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'mode')
    mode = args['mode']

    supported_modes = ('keep', 'crop', 'resize')
    if mode not in supported_modes:
        raise ValidationError('Unknown `mode`. Supported modes: %s.' %
                              ', '.join('"%s"' % mode for mode in supported_modes))

    w = args.get('w', None)
    h = args.get('h', None)
    try:
        w = w and int(w) or None
        h = h and int(h) or None
    except ValueError:
        raise ValidationError('`w` and `h` must be integer values.')

    if mode in ('crop', 'resize') and not (w and h):
        raise ValidationError('Both `w` and `h` must be specified.')
    elif not (w or h):
        raise ValidationError('Either `w` or `h` must be specified.')

    return [mode, w, h]
