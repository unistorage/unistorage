# coding: utf-8
from app import db
from app.models import RegularFile, PendingFile
from tests.utils import StorageFunctionalTest


class DeletionTest(StorageFunctionalTest):
    """Тестирует удаление файла.
    """
    def test(self):
        original_uri = self.put_file('images/some.jpeg')

        delete_action_url = '%s?action=delete' % original_uri
        r = self.app.get(delete_action_url, status='*')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, {u'status': u'ok', u'deleted': [original_uri, ]})

        self.assertTrue(PendingFile.get_one(db).deleted)

    def test_recursive(self):
        original_uri = self.put_file('images/some.jpeg')

        r = self.app.get('%s?action=convert&to=gif' % original_uri)
        self.assertEquals(r.json['status'], 'ok')
        modification_url = r.json['resource_uri']

        delete_action_url = '%s?action=delete&recursive=yes' % original_uri
        r = self.app.get(delete_action_url, status='*')
        self.assertEqual(r.status_code, 200)

        self.assertEqual(r.json, {u'status': u'ok', u'deleted': [original_uri, modification_url]})

    def test_no_actions_for_deleted_file(self):
        original_uri = self.put_file('images/some.jpeg')

        delete_action_url = '%s?action=delete' % original_uri
        r = self.app.get(delete_action_url, status='*')

        r = self.app.get('%s?action=convert&to=gif' % original_uri, status='*')
        self.assertEqual(r.status_code, 400)
