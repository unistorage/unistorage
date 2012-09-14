from flask import request, g, jsonify
from bson.objectid import ObjectId

import settings
import actions
from actions import templates
from utils import ValidationError, get_type_family
from app.models import File, PendingFile


def apply_actions(source_file, action_list, label):
    source_id = source_file.get_id()
    target_file = File.get_one(g.db, {'original': source_id, 'label': label})

    if target_file:
        return target_file.get_id()

    ttl_timedelta = settings.AVERAGE_TASK_TIME * (g.q.count + len(action_list))
    ttl = int(ttl_timedelta.total_seconds())
    target_kwargs = {
        'user_id': request.user['_id'],
        'type_id': source_file.type_id,
        'original': source_id,
        'label': label,
    }

    target_id = PendingFile.put_to_fs(g.db, g.fs, ttl=ttl, actions=action_list,
            original_content_type=source_file.content_type, **target_kwargs)

    g.q.enqueue('actions.tasks.perform_actions',
            source_id, target_id, target_kwargs, action_list)
    g.db[File.collection].update({'_id': source_id},
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
    return apply_actions(source_file, action_list, label)


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
    return apply_actions(source_file, action_list, label)
