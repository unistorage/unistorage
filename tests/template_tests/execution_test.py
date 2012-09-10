import os
import sys
import time
import unittest
from pprint import pprint

from bson.objectid import ObjectId
from gridfs import GridFS
from flask import request

import app
import settings
import fileutils
from actions.utils import ValidationError
from actions.handlers import apply_template
from tests.utils import WorkerMixin


class UnitTest(unittest.TestCase, WorkerMixin):
    def setUp(self):
        self.db = app.get_mongodb_connection()[settings.MONGO_DB_NAME]
        self.fs = GridFS(self.db)
        self.templates = self.db[settings.MONGO_TEMPLATES_COLLECTION_NAME]
        
        self.ctx = app.app.test_request_context()
        self.ctx.push()
        app.before_request()
        token = settings.TOKENS[0]
        self.user = app.get_or_create_user(token)
        request.user = self.user

    def tearDown(self):
        self.ctx.pop()

    def put_file(self, path):
        f = open(path, 'rb')
        filename = os.path.basename(path)
        return self.fs.put(f.read(), filename=filename, content_type='image/jpg')

    def test(self):
        file_id = self.put_file('./tests/images/some.jpeg')
        template_data = {
            'user_id': self.user['_id'],
            'applicable_for': 'image',
            'action_list': [
                ('resize', ['keep', 400, None]),
                ('make_grayscale', []),
                ('resize', ['keep', 300, None]),
            ]
        }
        template_id = self.templates.insert(template_data)
        target_id = apply_template(self.fs.get(file_id), {
            'template': str(template_id)
        })

        self.run_worker()

        target_file = self.fs.get(ObjectId(target_id))
        file_data = fileutils.get_file_data(target_file)
        self.assertEquals(file_data['fileinfo']['width'], 300)
