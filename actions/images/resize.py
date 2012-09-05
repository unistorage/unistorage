from PIL import Image
from utils import *
from ..utils import ValidationError


name = 'resize'
type_families_applicable_for = ['image']
result_type_family = 'image'


def validate_and_get_args(args):
    if 'mode' not in args:
        raise ValidationError('`mode` must be specified.')
    
    if args['mode'] not in ('keep', 'crop', 'resize'):
        raise ValidationError('Unknown `mode`. Available options: "keep", "crop" and "resize".')
    mode = args['mode']
    
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


def perform(source_file, mode, target_width, target_height):
    source_image = Image.open(source_file)
    target_image = wrap(source_image)

    if mode == 'resize':
        return target_image.resize(target_width, target_height).finalize()

    source_width, source_height = map(float, source_image.size)
    # If mode == 'keep', either target_width or target_height can be None
    factors = target_width / source_width if target_width else 1, \
              target_height / source_height if target_height else 1

    factor = max(factors) if mode == 'crop' else min(factors)
    width = to_int(source_width * factor)
    height = to_int(source_height * factor)

    if factor < 1:
        target_image.resize(width, height)

        if mode == 'crop':
            target_image.crop_to_center(target_width, target_height)

    return target_image.finalize()
