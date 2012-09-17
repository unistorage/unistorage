# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from flask import url_for, g

from app.models import User, Statistics
from app.admin.forms import get_random_token
from tests.utils import FunctionalTest, ContextMixin
from tests.admin_tests.utils import AuthMixin

class FunctionalTest(ContextMixin, FunctionalTest, AuthMixin):
    TEST_FILE_SIZE = 10 * 1024 * 1024

    def setUp(self):
        super(FunctionalTest, self).setUp();
        g.db[User.collection].drop()
        g.db[Statistics.collection].drop()
        self.login()

    def put_statistics(self, user_id, timestamp, type_id=None):
        g.db[Statistics.collection].insert({
            'user_id': user_id,
            'type_id': type_id,
            'timestamp': timestamp,
            'files_count': 1,
            'files_size': self.TEST_FILE_SIZE
        })

    def get_today(self):
        return datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0)

    def create_user(self):
        user = User({
            'name': 'test',
            'token': get_random_token()
        })
        return user.save(g.db)

    def fill_db(self):
        user_id = self.create_user()
        today = self.get_today()
        self.put_statistics(user_id, today, type_id='lala')
        self.put_statistics(user_id, today - timedelta(days=1), type_id='lala')
        self.put_statistics(user_id, today - timedelta(days=2), type_id='lala')
        self.put_statistics(user_id, today - timedelta(days=3), type_id='lala')
        self.put_statistics(user_id, today - timedelta(days=10), type_id='lala')
        self.put_statistics(user_id, today, type_id='bubu')
        self.put_statistics(user_id, today)

        another_user_id = self.create_user()
        self.put_statistics(another_user_id, today, type_id='lala')
        self.put_statistics(another_user_id, today)
        return user_id
    
    def test_empty(self):
        user_id = self.create_user()
        user_statistics_url = url_for('admin.user_statistics', user_id=user_id)
        response = self.app.get(user_statistics_url)
        self.assertTrue(u'Статистика отсутствует' in unicode(response))

    def test(self):
        user_id = self.fill_db()
        user_statistics_url = url_for('admin.user_statistics', user_id=user_id)
        response = self.app.get(user_statistics_url)
        ctx_summary = self.get_context_variable('summary')
        ctx_statistics = self.get_context_variable('statistics')
        self.assertEquals(ctx_summary['files_size'], 70)
        self.assertEquals(ctx_summary['files_count'], 7)
        self.assertEquals(len(ctx_statistics), 5)

    def test2(self):
        user_id = self.fill_db()
        user_statistics_url = url_for('admin.user_statistics', user_id=user_id)
        response = self.app.get(user_statistics_url + '?type_id=lala')
        ctx_summary = self.get_context_variable('summary')
        ctx_statistics = self.get_context_variable('statistics')
        self.assertEquals(ctx_summary['files_size'], 50)
        self.assertEquals(ctx_summary['files_count'], 5)
        self.assertEquals(len(ctx_statistics), 5)

    def test3(self):
        user_id = self.fill_db()
        user_statistics_url = url_for('admin.user_statistics', user_id=user_id)
        response = self.app.get(user_statistics_url + '?type_id=bubu')
        ctx_summary = self.get_context_variable('summary')
        ctx_statistics = self.get_context_variable('statistics')
        self.assertEquals(ctx_summary['files_size'], 10)
        self.assertEquals(ctx_summary['files_count'], 1)
        self.assertEquals(len(ctx_statistics), 1)
