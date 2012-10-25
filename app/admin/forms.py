# -*- coding: utf-8 -*-
import random

import wtforms as wtf
from flask import g
from bson.objectid import ObjectId

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
    return [(user.get_id(), user.name) for user in User.find(g.db, spec)]


class UserForm(wtf.Form):
    id = wtf.HiddenField()
    name = wtf.TextField(u'Имя пользователя', [wtf.validators.Required()])
    token = wtf.TextField(u'Токен доступа', [wtf.validators.Regexp(r'\w{32}')],
                          default=get_random_token)
    has_access_to = wtf.SelectMultipleField(
        u'Другие пользователи, к файлам которых разрешён доступ', coerce=ObjectId)

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
