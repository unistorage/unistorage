import wtforms


class LoginForm(wtforms.Form):
    login = wtforms.TextField(u'Login', [wtforms.validators.Required()])
    password = wtforms.PasswordField(u'Password', [wtforms.validators.Required()])
    came_from = wtforms.HiddenField()
