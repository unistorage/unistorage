import os
import unittest

from flask import g

import file_utils
from app.models import User, Statistics, File
from tests.utils import ContextMixin, GridFSMixin


class Test(GridFSMixin, ContextMixin, unittest.TestCase):
    def create_user(self, token):
        user = User({
            'name': u'test_user',
            'token': token
        })
        return user.save(g.db)

    def test(self):
        user_id = self.create_user('1b908be28e2b869f90e44276304b656a')
        self.assertEquals(Statistics.find(g.db).count(), 0)
        
        some_jpeg_id = self.put_file('./tests/images/some.jpeg',
                type_id='lalala',
                user_id=user_id)
        some_jpeg_size = File.get_one(g.db, {'_id': some_jpeg_id}).length
        self.assertEquals(Statistics.find(g.db).count(), 1)

        statistics = Statistics.find(g.db)[0]
        self.assertEquals(statistics.files_count, 1)
        self.assertEquals(statistics.files_size, some_jpeg_size)

        some_png_id = self.put_file('./tests/images/some.png',
                type_id='lalala',
                user_id=user_id)
        some_png_size = File.get_one(g.db, {'_id': some_png_id}).length
        self.assertEquals(Statistics.find(g.db).count(), 1)
        statistics = Statistics.find(g.db)[0]
        self.assertEquals(statistics.files_count, 2)
        self.assertEquals(statistics.files_size, some_jpeg_size + some_png_size)

        self.put_file('./tests/images/some.gif',
                type_id='bububu',
                user_id=user_id)
        self.assertEquals(Statistics.find(g.db).count(), 2)

        self.put_file('./tests/images/some.gif',
                type_id='bububu',
                user_id=user_id)
        self.assertEquals(Statistics.find(g.db).count(), 2)

        user_id = self.create_user('1b908beabcb869f90e44276304b656a')
        self.put_file('./tests/images/some.gif',
                type_id='bububu',
                user_id=user_id)
        self.assertEquals(Statistics.find(g.db).count(), 3)
