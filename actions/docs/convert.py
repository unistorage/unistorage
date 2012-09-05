import subprocess
from StringIO import StringIO

import settings
from tasks import ActionException
from ..utils import ValidationError


name = 'convert'
type_families_applicable_for = ['doc']
result_type_family = 'doc'


def validate_and_get_args(source_file, args):
    if 'to' not in args:
        raise ValidationError('`to` must be specified.')
    format = args['to']

    supported_formats = ('doc', 'docx', 'odt', 'pdf', 'rtf', 'txt', 'html')
    if format not in supported_formats:
        raise ValidationError('Source file is %s and can be only converted to the one of '
            'following formats: %s.' % (source_file.content_type, ', '.join(supported_formats)))

    return [format]


def perform(source_file, format):
    args = [settings.OO_WRAPPER_BIN, '--format', format, '--source', '-', '--target', '-']
    try:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        raise ActionException('Failed to start oo-wrapper: %s' % settings.OO_WRAPPER_BIN)

    stdout, stderr = proc.communicate(input=source_file.read())
    return_code = proc.wait()
    if return_code != 0:
        raise ActionException('oo-wrapper (%s) failed: %s' % (settings.OO_WRAPPER_BIN, stderr))

    return StringIO(stdout), format.lower()