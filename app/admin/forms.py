import random

import wtforms as wtf


class LoginForm(wtf.Form):
    login = wtf.TextField(u'Login', [wtf.validators.Required()])
    password = wtf.PasswordField(u'Password', [wtf.validators.Required()])
    came_from = wtf.HiddenField()


def random_token():
    return '%032x' % random.getrandbits(128)


class UserForm(wtf.Form):
    name = wtf.TextField(u'Name', [wtf.validators.Required()])
    token = wtf.TextField(u'Token', [wtf.validators.Regexp(r'\w{32}')],
            default=random_token)
