from actions.utils import ValidationError
from actions.common import validate_presence


name = 'convert'
applicable_for = 'image'
result_type_family = 'image'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'to')
    format = args['to']

    supported_formats = ('bmp', 'gif', 'jpeg', 'png', 'tiff')
    if format not in supported_formats:
        raise ValidationError('Source file can be only converted to the one of '
                              'following formats: %s.' % ', '.join(supported_formats))

    return [format]


def perform(source_file, to):
    from PIL import Image
    from utils import wrap

    source_image = Image.open(source_file)
    target_image = wrap(source_image)
    return target_image.finalize(format=to)
