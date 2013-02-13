# coding: utf-8
"""
Применение операций и шаблонов
==============================
"""
from flask import request

import settings
import actions
from actions.tasks import perform_actions, perform_actions_v2
from app import db, fs
from app.models import Template, File, PendingFile
from app.perms import AccessPermission
from utils import ValidationError


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
    if source_file.modifications:
        target_id = source_file.modifications.get(label)
        if target_id:
            return target_id

    ttl_timedelta = settings.AVERAGE_TASK_TIME
    ttl = int(ttl_timedelta.total_seconds())

    source_id = source_file.get_id()

    target_id = PendingFile.put_to_fs(db, fs, **{
        'user_id': request.user['_id'],
        'type_id': source_file.type_id,
        'original': source_id,
        'label': label,
        'ttl': ttl,
        'actions': action_list,
        'original_content_type': source_file.content_type,
    })

    #perform_actions.delay(source_id, target_id, target_kwargs)
    perform_actions_v2.delay(target_id)

    db[File.collection].update(
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
    template = Template.get_by_resource_uri(db, template_uri)
    
    if not template:
        raise ValidationError('Template %s does not exist.' % template_uri)
    AccessPermission(source_file).test(http_exception=403)

    source_unistorage_type = source_file.unistorage_type
    if source_unistorage_type != template['applicable_for']:
        raise ValidationError('Specified template is not applicable for the source file.')

    # Проверяем, что первая операция в шаблоне действительно применима к исходному файлу,
    # основываясь не только на его формате (а также, например, на кодеках видеофайла).
    first_action_args = template['action_list'][0]
    action_name = first_action_args['action']
    action = actions.get_action(source_unistorage_type, action_name)
    cleaned_args = action.validate_and_get_args(first_action_args, source_file=source_file)

    label = str(template.get_id())
    action_list = template['cleaned_action_list']
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
    source_unistorage_type = source_file.unistorage_type
    action = actions.get_action(source_unistorage_type, action_name)
    if not action:
        raise ValidationError('Action %s is not supported for %s (%s).' %
                              (action_name, source_unistorage_type, source_file.content_type))

    cleaned_args = action.validate_and_get_args(args, source_file=source_file)
    label = '_'.join(map(str, [action.name] + cleaned_args))
    label = label.replace('.', '_')
    action_list = [(action.name, cleaned_args)]
    return apply_actions(source_file, action_list, label)
