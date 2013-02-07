from actions.utils import ValidationError
from actions.common import validate_presence
from . import ImageMagickWrapper


name = 'convert'
applicable_for = 'image'
result_unistorage_type = 'image'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'to')
    format = args['to']

    supported_formats = ('bmp', 'gif', 'jpeg', 'png')
    if format not in supported_formats:
        raise ValidationError('Source file can be only converted to the one of '
                              'following formats: %s.' % ', '.join(supported_formats))

    return [format]


def perform(source_file, to):
    return ImageMagickWrapper(source_file).finalize(format=to)
