from flask import request, g, jsonify

import settings
import actions
from utils import ValidationError


def create_label(action_name, args):
    return '_'.join(map(str, [action_name] + args))


def validate_and_get_action(source_file, args_dict):
    action_name = args_dict['action']
    
    type_family = actions.utils.get_type_family(source_file.content_type)
    applicable_actions = actions.actions.get(type_family, {})
    action = applicable_actions.get(action_name)
    if not action:
        raise ValidationError('Action %s is not supported for %s (%s).' % \
                (action_name, type_family, source_file.content_type))
    args_list = action.validate_and_get_args(source_file, args_dict)
    label = create_label(action.name, args_list)
    return (action.perform, action.name, args_list, label)


def process_action_request(source_file, args):
    source_id = source_file._id
    action, action_name, args, label = validate_and_get_action(source_file, args)
    if g.fs.exists(original=source_id, label=label):
        target_file = g.fs.get_last_version(original=source_id, label=label)
        target_id = target_file._id
    else:
        ttl_timedelta = settings.AVERAGE_TASK_TIME * (g.q.count + 1)
        ttl = int(ttl_timedelta.total_seconds())
        target_kwargs = {
            'user_id': request.user['_id'],
            'original': source_id,
            'label': label
        }
        action_data = {
            'name': action_name,
            'args': args,
            'source_content_type': source_file.content_type
        }

        target_file = g.fs.new_file(pending=True, action=action_data, ttl=ttl, **target_kwargs)
        target_file.close()
        target_id = target_file._id

        g.q.enqueue('tasks.perform_action', source_id, target_id, target_kwargs,
                action, args)
        g.db.fs.files.update({'_id': source_id},
                {'$set': {'modifications.%s' % label: target_id}})
    return target_id


def handle_get_action(_id):
    source_file = g.fs.get(_id)
    try:
        target_id = process_action_request(source_file, request.args.to_dict())
        return jsonify({'status': 'ok', 'id': str(target_id)})
    except ValidationError as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 400
