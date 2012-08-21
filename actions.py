from datetime import datetime

from flask import g

import settings
import image_actions


class ValidationError(Exception):
    pass

def validate_and_get_resize_args(source_file, args):
    if 'mode' not in args or args['mode'] not in ('keep', 'crop', 'resize'):
        raise ValidationError('Unknown mode. Available options: "keep", "crop" and "resize".')
    mode = args['mode']
    
    w = args.get('w', None)
    h = args.get('h', None)
    try:
        w = w and int(w) or None
        h = h and int(h) or None
    except ValueError:
        raise ValidationError('w and h must be integer values.')

    if mode in ('crop', 'resize') and not (w and h):
        raise ValidationError('Both w and h must be specified.')
    elif not (w or h):
        raise ValidationError('Either w or h must be specified.')

    return [mode, w, h]

def validate_and_get_convert_args(source_file, args):
    if 'to' not in args:
        raise ValidationError('"to" must be specified.')
    to = args['to']

    try:
        type, subtype = to.split('/', 1)
    except ValueError:
        raise ValidationError('"to" must be a mime type.')

    supported_subtypes = ('bmp', 'gif', 'jpeg', 'png', 'tiff')
    if type != 'image' or subtype not in supported_subtypes:
        raise ValidationError('Source file is %s and can be only converted to the image of the one of '
            'following subtypes: %s.' % (source_file.content_type, ', '.join(supported_subtypes)))

    return [subtype]

def create_label(action_name, args):
    return '_'.join(map(str, [action_name] + args))

def validate_and_get_action(source_file, args):
    action_name = args['action']
    
    if action_name == 'resize':
        action = image_actions.resize
        args = validate_and_get_resize_args(source_file, args)
    elif action_name == 'make_grayscale':
        action = image_actions.make_grayscale
        args = []
    elif action_name == 'convert':
        if source_file.content_type.startswith('image'):
            action = image_actions.convert
            args = validate_and_get_convert_args(source_file, args)
        else:
            raise ValidationError('Currently convert is only supported for images.')
    else:
        raise ValidationError('Unknown action.')

    label = create_label(action_name, args)
    return (action, args, label)

def handle_action_request(source_file, request):
    source_id = source_file._id
    action, args, label = validate_and_get_action(source_file, request.args.to_dict())

    if g.fs.exists(original=source_id, label=label):
        target_file = g.fs.get_last_version(original=source_id, label=label)
        target_id = target_file._id
    else:
        finish_time = datetime.now().replace(microsecond=0) + \
                        settings.AVERAGE_TASK_TIME * (g.q.count + 1)
        target_kwargs = {
            'user_id': request.user['_id'],
            'original': source_id,
            'label': label
        }

        target_file = g.fs.new_file(finish_time=finish_time, **target_kwargs)
        target_file.close()
        target_id = target_file._id

        g.q.enqueue('tasks.perform_action', source_id, target_id, target_kwargs,
                action, args)
        g.db.fs.files.update({'_id': source_id},
                {'$set': {'modifications.%s' % label: target_id}})
    return target_id
