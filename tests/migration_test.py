# encoding: utf-8
import unittest

import mock

from app import db
from app.models import RegularFile
from tests.utils import ContextMixin, GridFSMixin
from migrations.m00 import get_callback


class Test(GridFSMixin, ContextMixin, unittest.TestCase):
    @mock.patch('sys.stdin')
    @mock.patch('sys.stdout')
    @mock.patch('sys.stderr')
    def test(self, stdin, stdout, stderr):
        stdin.fileno.return_value = 0
        stdout.fileno.return_value = 1
        stderr.fileno.return_value = 2
        # run-time импорт, чтобы mock возымел силу:
        from migrate import migrate
        f1_id = self.put_file('images/some.jpeg')
        f2_id = self.put_file('images/some.png')
        f1 = RegularFile.get_one(db, {'_id': f1_id})
        f2 = RegularFile.get_one(db, {'_id': f2_id})

        # Миграция всех файлов с force=True
        with mock.patch('migrations.m00._update_extra') as _update_extra:
            migrate({}, get_callback(force=True), no_input=True)
            self.assertEqual(_update_extra.call_count, 2)

        # Миграция всех файлов с force=False (все файлы корректны)
        with mock.patch('migrations.m00._validate'):
            with mock.patch('migrations.m00._update_extra') as _update_extra:
                migrate({}, get_callback(), no_input=True)
                self.assertEqual(_update_extra.call_count, 0)

        f1.extra['format'] = None
        f1.save(db)
        f2.extra['width'] = None
        f2.save(db)

        # Миграция выборки файлов с force=False (все файлы испорчены)
        with mock.patch('migrations.m00._update_extra') as _update_extra:
            migrate({'filename': f1.filename}, get_callback(), no_input=True)
            self.assertEqual(_update_extra.call_count, 1)

        # Настоящая миграция:
        f1 = RegularFile.get_one(db, {'_id': f1_id})
        self.assertIsNone(f1.extra['format'])

        migrate({'filename': f1.filename}, get_callback(), no_input=True)

        f1 = RegularFile.get_one(db, {'_id': f1_id})
        self.assertTrue(f1.extra['format'])
