# -*- coding: utf-8 -*-
import random
import re

import wtforms as wtf
from bson.objectid import ObjectId

from app import db
from app.models import User


class LoginForm(wtf.Form):
    login = wtf.TextField(u'Login', [wtf.validators.Required()])
    password = wtf.PasswordField(u'Password', [wtf.validators.Required()])
    came_from = wtf.HiddenField()


def get_random_token():
    return '%032x' % random.getrandbits(128)


def get_user_choices(excepted_user=None):
    spec = {}
    if excepted_user:
        spec = {'_id': {'$ne': excepted_user.get_id()}}
    return [(user.get_id(), user.name) for user in User.find(db, spec)]


class DomainListWidget(object):
    def __call__(self, field, **kwargs):
        html = ['<ul>']
        for subfield in field:
            additional_classes = subfield.errors and 'error' or ''
            html.append('<li class="control-group %s">' % additional_classes)
            html.append(subfield())
            html.append('</li>')
        html.append('</ul>')
        return wtf.widgets.HTMLString(''.join(html))


class DomainList(wtf.fields.FieldList):
    widget = DomainListWidget()

    def _extract_indices(self, prefix, formdata):
        offset = len(prefix) + 1
        for k, v in formdata.iteritems():
            if k.startswith(prefix):
                k = k[offset:].split('-', 1)[0]
                if k.isdigit() and v:
                    yield int(k)


class UserForm(wtf.Form):
    id = wtf.HiddenField()
    name = wtf.TextField(u'Имя пользователя', [wtf.validators.Required()])
    token = wtf.TextField(u'Токен доступа', [wtf.validators.Regexp(r'\w{32}')],
                          default=get_random_token)
    is_aware_of_api_changes = wtf.BooleanField(u'Готов к миграции на изменённый API')
    has_access_to = wtf.SelectMultipleField(
        u'Другие пользователи, к файлам которых разрешён доступ', coerce=ObjectId)
    domains = DomainList(wtf.TextField(u'', [wtf.validators.URL()]), label=u'Домены')
    blocked = wtf.BooleanField(u'Заблокирован')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        user = kwargs.get('obj')
        self.has_access_to.choices = get_user_choices(excepted_user=user)

    def process(self, formdata, obj, **kwargs):
        super(UserForm, self).process(formdata, obj, **kwargs)
        if obj:
            self.id.process(formdata, obj.get_id())
            users = [user_id for _, user_id in obj.needs]
            self.has_access_to.process(formdata, users)


class DeleteForm(wtf.Form):
    """Форма для удаления файла"""
    id = wtf.TextField(u'ID файла', [
        wtf.validators.Required(),
        wtf.validators.Regexp(
            '^[a-f\d]{24}$', re.IGNORECASE,
            message=u"ID файла должен стостоять из 24 символов (цифры и буквы a-f)")])
    recursive = wtf.BooleanField(u'Удалить все модификации файла', default=False)
