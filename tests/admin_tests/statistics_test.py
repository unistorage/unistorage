# -*- coding: utf-8 -*-
from functools import partial
from datetime import datetime, timedelta

from flask import url_for, g

from app.models import User, Statistics
from app.admin.forms import get_random_token
from tests.utils import AdminFunctionalTest


class FunctionalTest(AdminFunctionalTest):
    FILE_SIZE_BYTES = 5.5 * 1024 * 1024

    def setUp(self):
        super(FunctionalTest, self).setUp();
        self.login()

    def put_statistics(self, user_id, timestamp, type_id=None):
        g.db[Statistics.collection].insert({
            'user_id': user_id,
            'type_id': type_id,
            'timestamp': timestamp,
            'files_count': 1,
            'files_size': self.FILE_SIZE_BYTES
        })

    def create_user(self):
        user = User({
            'name': 'test',
            'token': get_random_token()
        })
        return user.save(g.db)

    def fill_db(self):
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        self.user1_id = self.create_user()
        put_statistics = partial(self.put_statistics, self.user1_id)
        put_statistics(today)
        put_statistics(today, type_id='bubu')
        put_statistics(today, type_id='lala')
        put_statistics(today - timedelta(days=1), type_id='lala')
        put_statistics(today - timedelta(days=2), type_id='lala')
        put_statistics(today - timedelta(days=3), type_id='lala')
        put_statistics(today - timedelta(days=10), type_id='lala')

        self.user2_id = self.create_user()
        put_statistics = partial(self.put_statistics, self.user2_id)
        put_statistics(today)
        put_statistics(today, type_id='lala')

    def assert_statistics(self, response, files_number, statistics_len):
        to_mb = lambda n: n / (1024. * 1024)
        summary = response.context['summary']
        statistics = response.context['statistics']

        summary_size = summary['files_size']
        expected_summary_size = to_mb(files_number * self.FILE_SIZE_BYTES)
        self.assertAlmostEqual(summary_size, expected_summary_size)

        summary_count = summary['files_count']
        self.assertEquals(summary_count, files_number)
        self.assertEquals(len(statistics), statistics_len)
    
    def test_empty(self):
        user_id = self.create_user()
        user_statistics_url = url_for('admin.user_statistics', user_id=user_id)
        response = self.app.get(user_statistics_url)
        self.assertTrue(u'Статистика отсутствует' in unicode(response))

    def test(self):
        user_id = self.fill_db()
        user1_statistics_url = url_for('admin.user_statistics', user_id=self.user1_id)
        response = self.app.get(user1_statistics_url)
        self.assert_statistics(response, 7, 5)
        self.assertEquals(len(response.context['type_ids']), 2)

        response = self.app.get(user1_statistics_url + '?type_id=lala')
        self.assert_statistics(response, 5, 5)

        response = self.app.get(user1_statistics_url + '?type_id=bubu')
        self.assert_statistics(response, 1, 1)
        
        user2_statistics_url = url_for('admin.user_statistics', user_id=self.user2_id)
        response = self.app.get(user2_statistics_url)
        self.assertEquals(len(response.context['type_ids']), 1)
        self.assert_statistics(response, 2, 1)
