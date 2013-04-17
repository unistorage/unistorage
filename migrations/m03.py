# coding: utf-8
"""Миграция удаляет потерянные файлы.
Потерянными считаются файлы, которые имеют ссылку original,
но оригинал о них ничего не знает (запись в modifications отсутствует).
"""
from app import db, fs


def callback(id_, file_, log=None):
    original_id = file_.get('original')
    if not original_id:
        return

    label = file_.get('label')
    original = db.fs.files.find_one({'_id': original_id})
    modifications = original.get('modifications', {})
    if modifications.get(label) != id_:
        print 'Deleting %s...' % id_
        fs.delete(id_)
