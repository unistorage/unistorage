from flask import request, g, jsonify
from werkzeug.urls import url_decode

import settings
import actions
from utils import ValidationError, TYPE_FAMILIES


def create_label(action_name, args):
    return '_'.join(map(str, [action_name] + args))


def validate_and_get_action(source_file, args):
    action_name = args['action']
    
    # Type family is either `video`, `image` of `doc`
    type_family = actions.utils.get_type_family(source_file.content_type)
    # Get actions that applicable for given type family
    applicable_actions = actions.actions.get(type_family, {})
    # Try to get applicable action by name
    action = applicable_actions.get(action_name)

    if not action:
        raise ValidationError('Action %s is not supported for %s (%s).' % \
                (action_name, type_family, source_file.content_type))

    cleaned_args = action.validate_and_get_args(args)
    label = create_label(action.name, cleaned_args)

    return (action.perform, action.name, cleaned_args, label)


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



def validate_actions_compatibility(source_type_family, action_args_list):
    current_type_family = source_type_family

    for index, action_args in enumerate(action_args_list, 1):
        action_name = action_args.get('action')
        if not action_name:
            raise ValidationError(
                    'Error on step %d: action is not specified.' % index)
        # Get actions that applicable for current result
        applicable_actions = actions.actions.get(current_type_family, {})
        # Try to get applicable action by name
        action = applicable_actions.get(action_name)
        if not action:
            raise ValidationError(
                    'Error on step %(index)s: action %(action_name)s '
                    'is not supported for %(type_family)s.' % {
                        'action_name': action_name,
                        'index': index,
                        'type_family': current_type_family
                    })

        action.validate_and_get_args(action_args)
        current_type_family = action.result_type_family
    
        
def validate_and_get_template(source_type_families, action_strings):
    # Type families for which template is applicable
    if not source_type_families:
        raise ValidationError('`applicable_for` must contain at least one type.')

    if not action_strings:
        raise ValidationError('`actions` must contain at least one action.')
    
    # List of arguments dictionaries
    action_args_list = [url_decode(url) for url in action_strings]
    
    # Validate template against all specified `applicable_for` type families
    for type_family in source_type_families:
        validate_actions_compatibility(type_family, action_args_list)

    return {
        'applicable_for': source_type_families,
        'action_args_list': action_args_list
    }


def handle_create_template():
    try:
        templates_db = g.db[settings.MONGO_TEMPLATES_DB]
        template_data = validate_and_get_template(
                request.form.getlist('applicable_for[]'),
                request.form.getlist('action[]'))
        template_data.update({
            'user_id': request.user['_id']
        })
        template_id = templates_db.insert(template_data)
        return jsonify({'status': 'ok', 'id': str(template_id)})
    except ValidationError as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 400
