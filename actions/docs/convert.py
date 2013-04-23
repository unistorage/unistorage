from subprocess import Popen, PIPE
from cStringIO import StringIO

import settings
from actions.common import validate_presence
from actions.utils import ValidationError, ActionError


name = 'convert'
applicable_for = 'doc'


def get_result_unistorage_type(*args):
    return 'doc'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'to')
    format = args['to']

    supported_formats = ('doc', 'docx', 'odt', 'pdf', 'rtf', 'txt', 'html')
    if format not in supported_formats:
        raise ValidationError('Source file can be only converted to the one of '
                              'following formats: %s.' % ', '.join(supported_formats))

    return [format]


def perform(source_file, format):
    args = (settings.OO_WRAPPER_BIN, '-', '-', '--format', format)
    oowrapper = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = oowrapper.communicate(input=source_file.read())
    if oowrapper.wait() != 0:
        raise ActionError('oowrapper error: %s' % stderr)
    return StringIO(stdout), format.lower()
