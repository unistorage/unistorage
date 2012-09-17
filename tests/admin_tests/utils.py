from flask import url_for

import settings


class AuthMixin(object):
    def login(self):
        form = self.app.get(url_for('admin.login')).form
        form.set('login', settings.ADMIN_USERNAME)
        form.set('password', settings.ADMIN_PASSWORD)
        form.submit()
