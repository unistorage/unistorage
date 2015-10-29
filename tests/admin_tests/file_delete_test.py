# coding: utf-8
from flask import url_for
import mock

from tests.utils import AdminFunctionalTest


class Test(AdminFunctionalTest):
    def test_create(self):
        self.login()
        file_delete_url = url_for('admin.file_delete')
        response = self.app.get(file_delete_url)
        form = response.form
        form['id'] = 'asdfasdf'

        response = form.submit()
        self.assertFalse(response.context['form'].validate())

        form = response.form
        form['id'] = '55a67e7d35f9d202523084dd'

        response = form.submit()
        self.assertTrue(response.context['form'].validate())
        self.assertIn('not found', response)

        form = response.form
        form['id'] = '0123456789abcdefabcdefab'

        with mock.patch('app.models.File.get_one'):
            with mock.patch('app.models.File.delete') as delete:
                response = form.submit()
                self.assertTrue(delete.is_called())
