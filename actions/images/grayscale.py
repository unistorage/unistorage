from . import ImageMagickWrapper


name = 'grayscale'
applicable_for = 'image'


def get_result_unistorage_type(*args):
    return 'image'


def validate_and_get_args(args, source_file=None):
    return []


def perform(source_file):
    return ImageMagickWrapper(source_file).make_grayscale().finalize()
