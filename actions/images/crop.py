from actions.utils import ValidationError
from actions.common import validate_presence
from . import ImageMagickWrapper


name = 'crop'
applicable_for = 'image'


def get_result_unistorage_type(*args):
    return 'image'


def validate_and_get_args(args, source_file=None):
    arg_names = ('x', 'y', 'w', 'h')
    for arg_name in arg_names:
        validate_presence(args, arg_name)

    try:
        x, y, w, h = map(int, map(args.get, arg_names))
    except ValueError:
        raise ValidationError('`x`, `y`, `w`, `h` must be integer values.')

    if x < 0 or y < 0 or w < 0 or h < 0:
        raise ValidationError('`x`, `y`, `w`, `h` must be positive integer values.')

    if source_file:
        assert source_file.unistorage_type == 'image'
        width = source_file.extra['width']
        height = source_file.extra['height']
        if x + w > width or y + h > height:
            raise ValidationError('The crop region is out of the image boundaries.')

    return [x, y, w, h]


def perform(source_file, x, y, w, h):
    return ImageMagickWrapper(source_file).crop(x, y, w, h).finalize()
