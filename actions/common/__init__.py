from actions.utils import ValidationError


def validate_presence(args, arg_name):
    if arg_name not in args:
        raise ValidationError('`%s` must be specified.' % arg_name)
