name = 'grayscale'
applicable_for = 'image'
result_unistorage_type = 'image'


def validate_and_get_args(args, source_file=None):
    return []


def perform(source_file):
    from PIL import Image
    from utils import wrap

    source_image = Image.open(source_file)
    target_image = wrap(source_image)
    return target_image.make_grayscale().finalize()
