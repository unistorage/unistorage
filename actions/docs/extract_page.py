# coding: utf-8
from subprocess import Popen, PIPE
from cStringIO import StringIO

import settings
from actions.common import validate_presence
from actions.utils import ValidationError, ActionError


name = 'extract_page'
applicable_for = 'doc'


def get_result_unistorage_type(*args):
    return 'image'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'to')
    format = args['to']

    validate_presence(args, 'page')
    try:
        page = int(args['page'])
    except ValueError:
        raise ValidationError('`page` must be integer value.')

    supported_formats = ('bmp', 'gif', 'jpeg', 'png')
    if format not in supported_formats:
        raise ValidationError('Source file can be only converted to the one of '
                              'following formats: %s.' % ', '.join(supported_formats))

    if source_file:
        data = source_file.extra
        pages = data.get('pages')
        if pages is None:
            raise ValidationError('Page can not be extracted from that type of document.')
        if page > pages:
            raise ValidationError('`page` must be less that number of pages in the document.')
        if page < 0:
            raise ValidationError('`page` must be positive.')

    return [page, format]


def perform(source_file, page, format):
    # -density 288 -resize 25% для «антиалиасинга» при растеризации
    args = (settings.CONVERT_BIN, '-density', '288', '-colorspace', 'RGB',
            'PDF:-[2]', '-background', 'white', '-flatten',
            '-resize', '25%', '%s:-' % format.upper())
    imagemagick = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = imagemagick.communicate(input=source_file.read())
    if imagemagick.wait() != 0:
        raise ActionError('`convert` failed: %s' % stderr_data)
    return StringIO(stdout_data), format
