# coding: utf-8
"""Пересчитывает метаданные постоянных файлов
(`unistorage_type`, `contentType`, `extra`).

По умолчанию перечитывает только те файлы, данные которых
не удовлетворяют объявленным JSON-схемам.
"""
import json

import jsonschema

import file_utils
from app import db, fs


def _validate_extra(unistorage_type, extra):
    if unistorage_type in ('video', 'audio', 'image'):
        with open('schemas/%s.json' % unistorage_type) as schema_file:
            schema = json.load(schema_file)
            extra_schema = schema['properties']['data']['properties']['extra']
            jsonschema.validate(extra, extra_schema)


def _validate(file_):
    unistorage_type = file_.get('unistorage_type')
    if not unistorage_type:
        raise Exception('File doesn\'t have `unistorage_type`')
    extra = file_.get('extra', {})
    _validate_extra(unistorage_type, extra)


def _update_extra(id_, file_):
    gridout = fs.get(id_)
    new_file_data = file_utils.get_file_data(gridout, file_['filename'])
    new_unistorage_type = new_file_data['unistorage_type']
    new_extra = new_file_data['extra']
    
    _validate_extra(new_unistorage_type, new_extra)

    db.fs.files.update({'_id': id_}, {
       '$set': {
            'unistorage_type': new_unistorage_type,
            'contentType': new_file_data['content_type'],
            'extra': new_extra,
        }
    })


def get_callback(force):
    """Если `force` установлено в True, миграция будет перечитывать файлы
    и с валидными данными.
    """
    def callback(id_, file_, log=None):
        if file_['pending']:
            return

        update_needed = False

        try:
            _validate(file_)
        except Exception as e:
            print u'  Данные не удовлетворяют схеме:'
            print u'  %s: %s' % (e, getattr(e, 'path', ''))

        if update_needed or force:
            try:
                _update_extra(id_, file_)
            except Exception as e:
                print u'  Данные по-прежнему не удовлетворяют схеме!'
                message = '  %s: %s' % (e, getattr(e, 'path', ''))
                print message
                if log:
                    log.write('%s %s\n' % (id_, message))
            else:
                print u'  Данные исправлены.'
        else:
            print u'OK'
    return callback
