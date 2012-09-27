# -*- coding: utf-8 -*-
from flask import url_for, g

from tests.utils import AdminFunctionalTest
from app.models import User


class Test(AdminFunctionalTest):
    def test_create(self):
        self.login()
        users_url = url_for('admin.users')
        response = self.app.get(users_url)
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

    def test_edit(self):
        self.login()

        # Создаём пользователя
        form = self.app.get(url_for('admin.user_create')).form
        form.set('name', 'Test')
        response = form.submit().follow()

        # Открываем форму редактирования нашего единственного пользователя
        form = response.click(href='edit').form
        form.set('name', 'John Doe')
        
        # Проверяем, что имя изменилось
        self.assertTrue('John Doe' in form.submit().follow())

    def test_permissions(self):
        self.login()

        # Создаём первого пользователя
        form = self.app.get(url_for('admin.user_create')).form
        form.set('name', 'Test1')
        response = form.submit().follow()

        # Создаём второго пользователя
        form = self.app.get(url_for('admin.user_create')).form
        form.set('name', 'Test2')
        response = form.submit().follow()

        user1, user2 = User.find(g.db, {})
        self.assertEquals(user1.needs, [])

        # Открываем форму редактирования первого пользователя
        response = response.click(href='%s/edit' % user1.get_id())
        form = response.form
       
        # Проверяем, что поле в выбора других пользователей только один элемент
        self.assertEquals(len(form.get('has_access_to').options), 1)
        opt_value, opt_selected = form.get('has_access_to').options[0]
        # И что он не выбран
        self.assertFalse(opt_selected)
        # Выбираем его
        form.select('has_access_to', opt_value)
        response = form.submit().follow()

        # Проверяем, что измемения сохранились
        form = response.click(href='%s/edit' % user1.get_id()).form
        self.assertEquals(len(form.get('has_access_to').options), 1)
        opt_value, opt_selected = form.get('has_access_to').options[0]
        self.assertTrue(opt_selected)
        
        # И отражены в поле needs первого пользователя
        user1_needs = User.get_one(g.db, {'_id': user1.get_id()}).needs
        self.assertEquals(user1_needs, [('role', user2.get_id())])

    def test_remove(self):
        self.login()
        
        # Создаём пользователя
        form = self.app.get(url_for('admin.user_create')).form
        form.set('name', 'Test')
        response = form.submit().follow()
        
        # Жмём "удалить"
        response = response.click(href='remove')
        self.assertEquals(response.status_code, 302)

        # Проверяем, что пользователей не осталось
        response = response.follow()
        ctx_users = response.context['users']
        self.assertEquals(ctx_users.count(), 0)
