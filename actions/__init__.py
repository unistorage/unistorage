from collections import defaultdict


class ActionException(Exception):
    pass


actions = defaultdict(dict) # Map family types to lists of applicable actions

def register_action(action):
    for required_attr in ('name', 'result_type_family', 'applicable_for',
            'validate_and_get_args', 'perform'):
        assert hasattr(action, required_attr)
    actions[action.applicable_for][action.name] = action

def get_action(type_family, name):
    # Get actions that applicable for given type family
    applicable_actions = actions.get(type_family, {})
    # Try to get applicable action by name
    action = applicable_actions.get(name)
    return action


import images.convert
register_action(images.convert)

import images.resize
register_action(images.resize)

import images.grayscale
register_action(images.grayscale)

import images.watermark
register_action(images.watermark)

import videos.convert
register_action(videos.convert)

import videos.watermark
register_action(videos.watermark)

import docs.convert
register_action(docs.convert)
