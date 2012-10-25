# -*- coding: utf-8 -*-
from flask import g

import settings
from app.models import User
from app.admin.forms import get_random_token
from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def set_token(self, token):
        self.app.token = token

    def test(self):
        g.db_connection.drop_database(settings.MONGO_DB_NAME)

        user1_token = get_random_token()
        user1_id = User({'name': 'User1', 'token': user1_token}).save(g.db)
        
        user2_token = get_random_token()
        user2_id = User({'name': 'User2', 'token': user2_token}).save(g.db)
        
        self.assertEquals(len(list(User.find(g.db))), 2)
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
        user2 = User.get_one(g.db, {'_id': user2_id})
        user2.update({'needs': [('role', user1_id)]})
        user2.save(g.db)
        
        # ...он получает доступ к файлам пользователя user1
        self.assertEquals(self.app.get(user1_file_uri).status_code, 200)
