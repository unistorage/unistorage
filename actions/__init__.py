from collections import defaultdict


actions = defaultdict(dict) # Map family types to lists of applicable actions

def register_action(action):
    for type_family in action.type_families_applicable_for:
        actions[type_family][action.name] = action


import images.convert
register_action(images.convert)

import images.resize
register_action(images.resize)

import images.make_grayscale
register_action(images.make_grayscale)

import videos.convert
register_action(videos.convert)

import docs.convert
register_action(docs.convert)