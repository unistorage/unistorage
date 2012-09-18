# -*- coding: utf-8 -*-
from flask import url_for, g

from tests.utils import AdminFunctionalTest


class Test(AdminFunctionalTest):
    def test_create(self):
        self.login()
        users_url = url_for('admin.users')
        response = self.app.get(users_url)
        self.assertTemplateUsed(response, 'users.html')
        self.assertEquals(response.context['users'].count(), 0)
        form = response.click(u'Добавить пользователя').form
        
        response = form.submit()
        self.assertTemplateUsed(response, 'user_create.html')
        self.assertFalse(response.context['form'].validate())

        form = response.form
        form.set('name', 'John Doe')
        response = form.submit().follow()

        self.assertTemplateUsed(response, 'users.html')
        self.assertEquals(response.context['users'].count(), 1)

    def test_remove(self):
        self.login()
        form = self.app.get(url_for('admin.user_create')).form
        form.set('name', 'Test')
        response = form.submit().follow()

        ctx_users = response.context['users']
        self.assertEquals(ctx_users.count(), 1)

        ctx_users._cursor.rewind()
        user = ctx_users[0]
        user_remove_url = url_for('admin.user_remove', _id=user.get_id())
        
        response = response.click(href=user_remove_url)
        self.assertEquals(response.status_code, 302)

        response = response.follow()
        ctx_users = response.context['users']
        self.assertEquals(ctx_users.count(), 0)
