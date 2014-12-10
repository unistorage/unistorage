# coding: utf-8
import mock
from bson import ObjectId

from moto import mock_s3
import boto
import httpretty

from tests.utils import StorageFunctionalTest
from app.aws import get_aws_credentials, put_file, get_file, AWSRegularFile
from app.models import User


ac = {'aws_access_key_id': 'AKIAAAAAAAAAAAAAAUYA',
      'aws_secret_access_key': 'RVddd+asdfDFDSdfsSDFSDFdfDFDSFdfsdfdUwJp',
      'aws_bucket_name': 'unistorage'}


class FunctionalTest(StorageFunctionalTest):
    @mock_s3
    def test_AWSRegularFile(self):
        conn = boto.connect_s3(ac['aws_access_key_id'], ac['aws_secret_access_key'])
        conn.create_bucket(ac['aws_bucket_name'])

        f = open('tests/fixtures/audios/god-save-the-queen.mp3', 'r')
        from app import db, fs
        user_id = User.get_one(db, {}).get_id()
        file_id = AWSRegularFile.put_to_fs(db, fs, 'asdf', f, ac, user_id=user_id)

        grid_out_file = AWSRegularFile.get_from_fs(db, fs, _id=file_id)
        self.assertEqual(grid_out_file.length, 0)
        self.assertEqual(grid_out_file.aws_bucket_name, ac['aws_bucket_name'])
        self.assertEqual(grid_out_file.aws_size, 1186681)

    def test_api_aws_url(self):
        # Заливаем файл в GridFS
        gridfs_uri = self.put_file('asdf.txt')

        # В урле файла нет префикса s3
        rg = self.check(gridfs_uri)
        self.assertNotIn('/s3/', rg.json['data']['url'])

        # Меняем настройки пользователя на s3
        self.patch_user({'s3': True})

        with mock.patch('app.aws.put_file', return_value=66) as put_file_mock:
            s3_uri = self.put_file('asdf.txt')

        self.assertTrue(put_file_mock.is_called)

        rs = self.check(s3_uri)

        # В урле есть префикс s3
        self.assertIn('/s3/test_unistorage/', rs.json['data']['url'])

        self.assertEqual(8, rs.json['data']['size'])

        # У старого файла по прежнему нет
        rg = self.check(gridfs_uri)
        self.assertNotIn('/s3/', rg.json['data']['url'])

    def test_tasks(self):
        self.patch_user({'s3': True})
        self.patch_user(ac)

        with mock.patch('app.aws.put_file', return_value=1186681) as put_file_mock:
            s3_uri = self.put_file('audios/god-save-the-queen.mp3')

        self.assertTrue(put_file_mock.calles_with(ac, mock.ANY, mock.ANY))

        _, _, f = put_file_mock.call_args[0]

        with mock.patch('app.aws.get_file') as get_file_mock:
            get_file_mock.return_value = f
            convert_action_url = '%s?action=convert&to=vorbis' % s3_uri
            r = self.app.get(convert_action_url)

            get_file_mock.assert_called()
            self.assertEquals(r.json['status'], 'ok')

            with mock.patch('app.aws.put_file', return_value=66) as put_file_mock:
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
        conn.create_bucket(ac['aws_bucket_name'])

        with open('tests/fixtures/asdf.txt', 'r') as f:
            length = put_file(ac, 'asdf', f)

        self.assertEqual(conn.get_bucket('unistorage').get_key('asdf').get_contents_as_string(), 'asdfasdf')
        self.assertEqual(length, 8)

    @httpretty.httprettified
    def test_get_file(self):
        httpretty.register_uri(
            httpretty.GET, 'http://unistorage1.s3.amazonaws.com/asdf', body='asdfasdf')
        f = get_file('unistorage1', 'asdf')
        assert f.read() == 'asdfasdf'
