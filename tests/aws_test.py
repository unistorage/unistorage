# coding: utf-8
import mock

from moto import mock_s3
import boto
import httpretty

from tests.utils import StorageFunctionalTest
from app.aws import get_aws_credentials, put_file, get_file


ac = {'aws_access_key_id': 'AKIAAAAAAAAAAAAAAUYA',
      'aws_secret_access_key': 'RVddd+asdfDFDSdfsSDFSDFdfDFDSFdfsdfdUwJp',
      'aws_bucket_name': 'unistorage1'}


class FunctionalTest(StorageFunctionalTest):

    def test_api_aws_url(self):
        # Заливаем файл в GridFS
        gridfs_uri = self.put_file('asdf.txt')

        # В урле файла нет префикса s3
        rg = self.check(gridfs_uri)
        self.assertNotIn('/s3/', rg.json['data']['url'])

        # Меняем настройки пользователя на s3
        self.patch_user({'s3': True})

        with mock.patch('app.aws.put_file') as put_file_mock:
            s3_uri = self.put_file('asdf.txt')

        self.assertTrue(put_file_mock.is_called)

        rs = self.check(s3_uri)

        # В урле есть префикс s3
        self.assertIn('/s3/test_unistorage/', rs.json['data']['url'])

        # У старого файла по прежнему нет
        rg = self.check(gridfs_uri)
        self.assertNotIn('/s3/', rg.json['data']['url'])

    def test_tasks(self):
        self.patch_user({'s3': True})
        self.patch_user(ac)

        with mock.patch('app.aws.put_file') as put_file_mock:
            s3_uri = self.put_file('audios/god-save-the-queen.mp3')

        self.assertTrue(put_file_mock.calles_with(ac, mock.ANY, mock.ANY))

        _, _, f = put_file_mock.call_args[0]

        with mock.patch('app.aws.get_file') as get_file_mock:
            get_file_mock.return_value = f
            convert_action_url = '%s?action=convert&to=vorbis' % s3_uri
            r = self.app.get(convert_action_url)

            get_file_mock.assert_called()
            self.assertEquals(r.json['status'], 'ok')

            with mock.patch('app.aws.put_file') as put_file_mock:
                self.run_worker()

            put_file_mock.assert_called()

    def test_get_aws_credentials(self):
        self.patch_user({'s3': True})

        self.assertEqual(get_aws_credentials(self.u), {
            'aws_access_key_id': 'test_id',
            'aws_secret_access_key': 'test_access_key',
            'aws_bucket_name': 'test_unistorage'})

        self.patch_user(ac)

        self.assertEqual(get_aws_credentials(self.u), ac)

    @mock_s3
    def test_put_file(self):
        conn = boto.connect_s3(ac['aws_access_key_id'], ac['aws_secret_access_key'])
        conn.create_bucket('unistorage1')

        with open('tests/fixtures/asdf.txt', 'r') as f:
            put_file(ac, 'asdf', f)

        assert conn.get_bucket('unistorage1').get_key('asdf').get_contents_as_string() == 'asdfasdf'

    @httpretty.httprettified
    def test_get_file(self):
        httpretty.register_uri(
            httpretty.GET, 'http://unistorage1.s3.amazonaws.com/asdf', body='asdfasdf')
        f = get_file('unistorage1', 'asdf')
        assert f.read() == 'asdfasdf'
