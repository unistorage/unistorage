# encoding: utf-8
import unittest

import mock

from app import db
from app.models import RegularFile
from tests.utils import ContextMixin, GridFSMixin
from migrate import migrate


class Test(GridFSMixin, ContextMixin, unittest.TestCase):
    def test(self):
        f1_id = self.put_file('images/some.jpeg')
        f2_id = self.put_file('images/some.png')
        f1 = RegularFile.get_one(db, {'_id': f1_id})
        f2 = RegularFile.get_one(db, {'_id': f2_id})
        
        # Миграция всех файлов с force=True
        with mock.patch('migrate._update_extra') as _update_extra:
            migrate({}, no_input=True, force=True)
            self.assertEqual(_update_extra.call_count, 2)
        
        # Миграция всех файлов с force=False (все файлы корректны)
        with mock.patch('migrate._validate') as _validate:
            with mock.patch('migrate._update_extra') as _update_extra:
                migrate({}, no_input=True)
                self.assertEqual(_update_extra.call_count, 0)

        f1.extra['format'] = None
        f1.save(db)
        f2.extra['width'] = None
        f2.save(db)

        # Миграция выборки файлов с force=False (все файлы испорчены)
        with mock.patch('migrate._update_extra') as _update_extra:
            migrate({'filename': f1.filename}, no_input=True)
            self.assertEqual(_update_extra.call_count, 1)
        
        # Настоящая миграция:
        f1 = RegularFile.get_one(db, {'_id': f1_id})
        self.assertIsNone(f1.extra['format'])
        
        migrate({'filename': f1.filename}, no_input=True)

        f1 = RegularFile.get_one(db, {'_id': f1_id})
        self.assertTrue(f1.extra['format'])
