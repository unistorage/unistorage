# -*- coding: utf-8 -*-
import importlib
from collections import defaultdict


actions_table = defaultdict(dict)


def register_action(action):
    """Валидирует и регистрирует `action` в качестве операции."""
    for required_attr in ('name', 'result_unistorage_type', 'applicable_for',
            'validate_and_get_args', 'perform'):
        assert hasattr(action, required_attr), \
            'Action %s validation failed: missing `%s`.' % (action, required_attr)
    actions_table[action.applicable_for][action.name] = action


def get_action(type_family, name):
    """Возвращает операцию с именем `name`, применимую к семейству типов `type_family`."""
    applicable_actions = actions_table.get(type_family, {})
    return applicable_actions.get(name)


class ActionException(Exception):
    pass


actions_to_register = (
    'images.convert',
    'images.resize',
    'images.grayscale',
    'images.watermark',
    'images.rotate',
    'videos.convert',
    'videos.watermark',
    'docs.convert',
)

for action in actions_to_register:
    action_module = importlib.import_module('.%s' % action, package='actions')
    register_action(action_module)


