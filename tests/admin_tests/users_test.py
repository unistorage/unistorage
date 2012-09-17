# -*- coding: utf-8 -*-
from flask import url_for, g

from app.models import User
from tests.utils import FunctionalTest, ContextMixin
from tests.admin_tests.utils import AuthMixin


class FunctionalTest(ContextMixin, FunctionalTest, AuthMixin):
    def setUp(self):
        super(FunctionalTest, self).setUp();
        g.db[User.collection].drop()
        self.login()

    def test_create(self):
        users = self.app.get(url_for('admin.users'))

        self.assertTemplateUsed('users.html')
        self.assertEquals(self.get_context_variable('users').count(), 0)
        form = users.click(u'Добавить пользователя').form
        response = form.submit()

        ctx_form = self.get_context_variable('form')
        self.assertFalse(ctx_form.validate())

        form = response.form
        form.set('name', 'John Doe')
        users = form.submit()
        self.assertTemplateUsed('users.html')
        self.assertEquals(self.get_context_variable('users').count(), 1)

    def test_remove(self):
        form = self.app.get(url_for('admin.user_create')).form
        form.set('name', 'Test')
        users = form.submit().follow()

        u = self.get_context_variable('users')
        self.assertEquals(u.count(), 1)
        u._cursor.rewind()
        user = u[0]
        user_remove_url = url_for('admin.user_remove', _id=user.get_id())
        
        response = users.click(href=user_remove_url)
        self.assertEquals(response.status_code, 302)
        users = response.follow()
        u = self.get_context_variable('users')
        self.assertEquals(u.count(), 0)
