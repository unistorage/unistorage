# -*- coding: utf-8 -*-
from flask import _app_ctx_stack

import settings
from app import db
from app.models import User
from app.admin.forms import get_random_token
from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def set_token(self, token):
        self.app.token = token

    def test(self):
        user1_token = get_random_token()
        user1_id = User({'name': 'User1', 'token': user1_token}).save(db)
        
        user2_token = get_random_token()
        user2_id = User({'name': 'User2', 'token': user2_token}).save(db)
        
        # user1
        self.set_token(user1_token)
        # ...загружает файл
        user1_file_uri = self.put_file('images/some.jpeg')
        # ...и имеет доступ к нему
        self.assertEquals(self.app.get(user1_file_uri).status_code, 200)
        
        # user2
        self.set_token(user2_token)
        # ...не имеет доступа к файлу пользователя user1
        r = self.app.get(user1_file_uri, status='*')
        self.assertEquals(r.status_code, 403)

        # Но как только пользователь user2 получает "роль" user1
        user2 = User.get_one(db, {'_id': user2_id})
        user2.update({'needs': [('role', user1_id)]})
        user2.save(db)
        
        # ...он получает доступ к файлам пользователя user1
        self.assertEquals(self.app.get(user1_file_uri).status_code, 200)

        # ...блокируем доступ пользователю user1
        user1 = User.get_one(db, {'_id': user1_id})
        user1.update({'blocked': True})
        user1.save(db)

        # ...у него больше нет доступа
        self.set_token(user1_token)
        r = self.app.get(user1_file_uri, status='*')
        self.assertEquals(r.status_code, 401)

        # ...но у user2 есть
        self.set_token(user2_token)
        self.assertEquals(self.app.get(user1_file_uri).status_code, 200)
