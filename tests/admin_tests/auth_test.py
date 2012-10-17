# -*- coding: utf-8 -*-
from flask import url_for

import settings
from tests.utils import AdminFunctionalTest


class FunctionalTest(AdminFunctionalTest):
    def setUp(self):
        super(FunctionalTest, self).setUp()
        self.index_url = url_for('admin.index')
        self.login_url = url_for('admin.login')
        self.logout_url = url_for('admin.logout')

    def test(self):
        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 302)
        self.assertTrue(self.login_url in r.headers['Location'])
        
        form = self.app.get(self.login_url).form
        form.set('login', 'lala')
        response = form.submit()
        self.assertFalse(response.context['form'].validate())

        form = self.app.get(self.login_url).form
        form.set('login', 'lala')
        form.set('password', 'bubu')
        response = form.submit()

        self.assertTrue(u'Неверный логин или пароль' in unicode(response))

        form = self.app.get(self.login_url).form
        form.set('login', settings.ADMIN_USERNAME)
        form.set('password', settings.ADMIN_PASSWORD)
        response = form.submit()

        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 200)

        self.app.get(self.logout_url)
        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 302)
        self.assertTrue(self.login_url in r.headers['Location'])
