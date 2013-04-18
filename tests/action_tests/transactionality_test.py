# coding: utf-8
import mock

import settings
from app import db
from app.models import PendingFile, RegularFile
from tests.utils import StorageFunctionalTest


class TransactionalityTest(StorageFunctionalTest):
    """Тестирует транзакционность операции «создать времеменный файл
    и послать сообщение брокеру».
    """
    def test(self):
        original_uri = self.put_file('images/some.jpeg')

        self.assertEqual(PendingFile.find(db).count(), 0)

        with mock.patch('actions.tasks.perform_actions.delay',
                        side_effect=Exception()) as delay:
            resize_action_url = '%s?action=grayscale' % original_uri
            r = self.app.get(resize_action_url, status='*')
            self.assertEqual(r.status_code, 503)

            self.assertEqual(PendingFile.find(db).count(), 0)
            self.assertFalse(RegularFile.get_one(db).modifications)
