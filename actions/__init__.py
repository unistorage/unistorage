# -*- coding: utf-8 -*-
import importlib
from collections import defaultdict


class ActionException(Exception):
    pass


actions = defaultdict(dict)


def register_action(action):
    """Валидирует и регистрирует `action` в качестве операции."""
    for required_attr in ('name', 'result_type_family', 'applicable_for',
            'validate_and_get_args', 'perform'):
        assert hasattr(action, required_attr)
    actions[action.applicable_for][action.name] = action


def get_action(type_family, name):
    """Возвращает операцию с именем `name`, применимую к семейству типов `type_family`."""
    applicable_actions = actions.get(type_family, {})
    return applicable_actions.get(name)


actions_to_register = (
    'images.convert',
    'images.resize',
    'images.grayscale',
    'images.watermark',
    'videos.convert',
    'videos.watermark',
    'docs.convert',
)

for action in actions_to_register:
    action_module = importlib.import_module('.%s' % action, package='actions')
    register_action(action_module)
