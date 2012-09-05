import sys
import time
import unittest
import os
from pprint import pprint
from bson.objectid import ObjectId

import redis
from webtest import TestApp
from rq import Queue, Worker, use_connection

import settings
import app
from actions.utils import ValidationError
from actions.handler import validate_and_get_template


class FunctionalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = TestApp(app.app)
        cls.headers = {'Token': settings.TOKENS[0]}
        cls.db = app.get_mongodb_connection()[settings.MONGO_DB_NAME]

    def test_create_template(self):
        r = self.app.post('/create_template', {
            'action[]': ['action=resize&mode=keep&w=50&h=50', 'action=make_grayscale'],
            'applicable_for[]': ['image']
        }, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assertTrue('id' in r.json)

    def test_create_template_validation(self):
        r = self.app.post('/create_template', {
            'action[]': [],
            'applicable_for[]': ['image']
        }, headers=self.headers, status='*')
        self.assertEquals(r.status_code, 400)
        self.assertEquals(r.json['status'], 'error')

        r = self.app.post('/create_template', {
            'action[]': ['action=convert&to=webm', 'action=resize&mode=keep&w=100&h=100'],
            'applicable_for[]': ['video']
        }, headers=self.headers, status='*')
        self.assertEquals(r.json['status'], 'error')


class UnitTest(unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)

    def test_presence_validation(self):
        with self.expect_validation_error('`applicable_for` must contain at least one type'):
            validate_and_get_template([], [])

        with self.expect_validation_error('`actions` must contain at least one action'):
            validate_and_get_template(['image'], [])

    def test_actions_validation(self):
        applicable_for = ['image']
        with self.expect_validation_error('Error on step 1: action is not specified'):
            validate_and_get_template(applicable_for, [''])

        with self.expect_validation_error('`mode` must be specified'):
            validate_and_get_template(applicable_for, ['action=resize'])

    def test_actions_compatibility(self):
        # First action (`convert` with `to` argument) applicable for both images and videos.
        # Since it preserves type family (converts video to video), second action must fail.
        with self.expect_validation_error('Error on step 2: action resize is not supported for video.'):
            validate_and_get_template(['video'],
                    ['action=convert&to=webm', 'action=resize&mode=keep&w=100&h=100'])
