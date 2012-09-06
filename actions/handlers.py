from flask import request, g, jsonify
from bson.objectid import ObjectId

import settings
import actions
from actions import templates
from utils import ValidationError, get_type_family


def handle_apply_template(_id):
    source_file = g.fs.get(_id)
    try:
        target_id = apply_template(source_file, request.args.to_dict())
        return jsonify({'status': 'ok', 'id': str(target_id)})
    except ValidationError as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 400


def handle_apply_action(_id):
    source_file = g.fs.get(_id)
    try:
        target_id = apply_action(source_file, request.args.to_dict())
        return jsonify({'status': 'ok', 'id': str(target_id)})
    except ValidationError as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 400


def handle_create_template():
    try:
        template_data = templates.validate_and_get_template(
                request.form.get('applicable_for'),
                request.form.getlist('action[]'))
    except ValidationError as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 400
    
    template_collection = g.db[settings.MONGO_TEMPLATES_COLLECTION_NAME]
    template_data.update({
        'user_id': request.user['_id']
    })
    template_id = template_collection.insert(template_data)
    return jsonify({'status': 'ok', 'id': str(template_id)})


def apply_action_list(source_file, action_list, label):
    source_id = source_file._id
    if g.fs.exists(original=source_id, label=label):
        target_file = g.fs.get_last_version(original=source_id, label=label)
        target_id = target_file._id
    else:
        ttl_timedelta = settings.AVERAGE_TASK_TIME * (g.q.count + len(action_list))
        ttl = int(ttl_timedelta.total_seconds())
        target_kwargs = {
            'user_id': request.user['_id'],
            'original': source_id,
            'label': label
        }

        target_file = g.fs.new_file(pending=True, ttl=ttl, actions=action_list,
                original_content_type=source_file.content_type, **target_kwargs)
        target_file.close()
        target_id = target_file._id

        g.q.enqueue('tasks.perform_action_list', source_id, target_id, target_kwargs, action_list)
        g.db.fs.files.update({'_id': source_id},
                {'$set': {'modifications.%s' % label: target_id}})
    return target_id


def apply_template(source_file, args):
    template_id = ObjectId(args['template'])
    templates = g.db[settings.MONGO_TEMPLATES_COLLECTION_NAME]
    template = templates.find_one({'_id': template_id})

    source_type_family = get_type_family(source_file.content_type)
    if source_type_family != template['applicable_for']:
        raise ValidationError('Specified template is not applicable for the source file.')

    label = str(template['_id'])
    action_list = template['action_list']
    return apply_action_list(source_file, action_list, label)


def apply_action(source_file, args):
    action_name = args['action']
    type_family = actions.utils.get_type_family(source_file.content_type)
    action = actions.get_action(type_family, action_name)

    if not action:
        raise ValidationError('Action %s is not supported for %s (%s).' % \
                (action_name, type_family, source_file.content_type))

    cleaned_args = action.validate_and_get_args(args)
    label = '_'.join(map(str, [action.name] + cleaned_args))
    action_list = [(action.name, cleaned_args)]
    return apply_action_list(source_file, action_list, label)
