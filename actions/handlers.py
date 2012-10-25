# -*- coding: utf-8 -*-
"""
Применение операций и шаблонов
==============================
"""
from flask import request, g

import settings
import actions
from actions.tasks import perform_actions
from app import parse_template_uri
from app.models import Template, File, PendingFile
from app.perms import AccessPermission
from utils import ValidationError, get_type_family


def apply_actions(source_file, action_list, label):
    """Проверяет существование модификации `source_file` с меткой `label`.  Если она существует --
    возвращает её идентификатор; если нет -- ставит в очередь применение операций `action_list` к
    файлу `source_file` и вешает на результирующий файл метку `label`.
    
    :param source_file: исходный файл
    :type source_file: :class:`app.models.File`
    :param label: метка, однозначно идентифицирующая набор операций `action_list`
    :type label: basestring
    :param action_list: список операций
    :type action_list: `list(tuple(action_name, action_cleaned_args))`
    :rtype: :class:`ObjectId`
    """
    source_id = source_file.get_id()
    target_file = File.get_one(g.db, {'original': source_id, 'label': label})

    if target_file:
        return target_file.get_id()

    ttl_timedelta = settings.AVERAGE_TASK_TIME
    ttl = int(ttl_timedelta.total_seconds())

    # Атрибуты, которые должны быть как у временного файла, так и у постоянного (после выполнения
    # операции)
    target_kwargs = {
        'user_id': request.user['_id'],
        'type_id': source_file.type_id,
        'original': source_id,
        'label': label,
    }

    # Атрибуты временного файла
    pending_target_kwargs = {
        'ttl': ttl,
        'actions': action_list,
        'original_content_type': source_file.content_type
    }
    pending_target_kwargs.update(target_kwargs)

    target_id = PendingFile.put_to_fs(g.db, g.fs, **pending_target_kwargs)
    perform_actions.delay(source_id, target_id, target_kwargs)
    g.db[File.collection].update(
        {'_id': source_id},
        {'$set': {'modifications.%s' % label: target_id}})
    return target_id


def apply_template(source_file, args):
    """Проверяет применимость шаблона, указанного в `args`, к `source_file`, ставит применение
    операций из шаблона в очередь (используя в качестве `label` идентификатор шаблона) и возвращает
    идентификатор временного файла.

    :param source_file: исходный файл
    :type source_file: :class:`app.models.File`
    :param args: аргументы (чаще всего -- ``request.args.to_dict()``)
    :type args: `dict(template=<template_id>, **kwargs)`
    :raises: ValidationError
    :rtype: :class:`ObjectId`
    """
    template_uri = args['template']
    try:
        template_id = parse_template_uri(template_uri)
    except ValueError as e:
        raise ValidationError(e.message)

    template = Template.get_one(g.db, {'_id': template_id})
    
    if not template:
        raise ValidationError('Template with id %s does not exist.' % template_id)
    AccessPermission(source_file).test(http_exception=403)

    source_type_family = get_type_family(source_file.content_type)
    if source_type_family != template['applicable_for']:
        raise ValidationError('Specified template is not applicable for the source file.')

    label = str(template_id)
    action_list = template['action_list']
    return apply_actions(source_file, action_list, label)


def apply_action(source_file, args):
    """Проверяет применимость действия, указанного в `args`, к `source_file`, ставит операцию в
    очередь (используя в качестве `label` сконкатенированные имя операции и её аргументы) и
    возвращает идентификатор временного файла.

    :param source_file: исходный файл
    :type source_file: :class:`app.models.File`
    :param args: аргументы (чаще всего -- ``request.args.to_dict()``)
    :type args: `dict(action=<action_name>, **kwargs)`
    :raises: ValidationError
    :rtype: :class:`ObjectId`
    """
    action_name = args['action']
    type_family = actions.utils.get_type_family(source_file.content_type)
    action = actions.get_action(type_family, action_name)

    if not action:
        raise ValidationError('Action %s is not supported for %s (%s).' %
                              (action_name, type_family, source_file.content_type))

    cleaned_args = action.validate_and_get_args(args)
    label = '_'.join(map(str, [action.name] + cleaned_args))
    action_list = [(action.name, cleaned_args)]
    return apply_actions(source_file, action_list, label)
