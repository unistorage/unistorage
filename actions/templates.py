from werkzeug.urls import url_decode

import actions
from utils import ValidationError


def validate_and_get_template_actions(source_type_family, action_args_list):
    result = []
    current_type_family = source_type_family

    for index, action_args in enumerate(action_args_list, 1):
        action_name = action_args.get('action')
        if not action_name:
            raise ValidationError(
                    'Error on step %d: action is not specified.' % index)
        
        action = actions.get_action(source_type_family, action_name)
        if not action:
            raise ValidationError(
                    'Error on step %(index)s: action %(action_name)s '
                    'is not supported for %(type_family)s.' % {
                        'action_name': action_name,
                        'index': index,
                        'type_family': current_type_family
                    })

        action_cleaned_args = action.validate_and_get_args(action_args)
        result.append((action_name, action_cleaned_args))
        current_type_family = action.result_type_family

    return result
    
        
def validate_and_get_template(source_type_family, action_strings):
    if not source_type_family:
        raise ValidationError('`applicable_for` is not specified.')

    if not action_strings:
        raise ValidationError('`actions` must contain at least one action.')
    
    action_args_list = [url_decode(url) for url in action_strings]
    action_list = validate_and_get_template_actions(source_type_family, action_args_list)

    return {
        'applicable_for': source_type_family,
        'action_list': action_list
    }