# coding: utf-8
"""
Валидация шаблонов
==================
"""
from werkzeug.urls import url_decode

import actions
from utils import ValidationError


def validate_and_get_template_actions(source_unistorage_type, action_args_list):
    """Рассматривая `source_unistorage_type` как семейство типов исходных
    файлов, проверяет применимость каждой последующей операции к результату
    предыдущей. Возвращает "очищенный" список операций и их параметров.

    :param source_unistorage_type: :term:`семейство типов`
    :param action_args_list: список аргументов операций
    :type action_args_list: list(dict(action=action_name, **kwargs))
    :raises: ValidationError
    :rtype: `list(tuple(action_name, action_cleaned_args))`
    """
    result = []
    current_unistorage_type = source_unistorage_type

    for index, action_args in enumerate(action_args_list, 1):
        action_name = action_args.get('action')
        if not action_name:
            raise ValidationError(
                'Error on step %d: action is not specified.' % index)
        
        action = actions.get_action(current_unistorage_type, action_name)
        if not action:
            raise ValidationError(
                'Error on step %(index)s: action %(action_name)s '
                'is not supported for %(unistorage_type)s.' % {
                    'action_name': action_name,
                    'index': index,
                    'unistorage_type': current_unistorage_type
                })

        action_cleaned_args = action.validate_and_get_args(action_args)
        result.append((action_name, action_cleaned_args))
        current_unistorage_type = action.result_unistorage_type

    return result
    
        
def validate_and_get_template(args):
    """Проверяет, что `applicable_for` и `actions` присутствуют в `args`;
    проверяет совместимость операций, указанных в `actions`. Возвращает
    "очищенные" данные для создания шаблона.

    :param args: аргументы
    :type args: `dict(applicable_for=..., actions=list(...))`
    :raises: ValidationError
    :rtype: `dict(applicable_for=unistorage_type,
                  action_list=list(dict),
                  cleaned_action_list=list(dict))`
    """
    applicable_for = args.get('applicable_for')
    if not applicable_for:
        raise ValidationError('`applicable_for` is not specified.')

    action_strings = args.get('actions')
    if not action_strings:
        raise ValidationError('`actions` must contain at least one action.')
    
    action_args_list = [url_decode(url) for url in action_strings]
    action_list = [action.to_dict() for action in action_args_list]
    cleaned_action_list = validate_and_get_template_actions(
        applicable_for, action_args_list)

    return {
        'applicable_for': applicable_for,
        'cleaned_action_list': cleaned_action_list,
        'action_list': action_list
    }
