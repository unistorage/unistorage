# coding: utf-8

import mock

from commands.migrate_user_data import migrate_user_data
from app.models import RegularFile, User
from app import db, fs
from app.aws import AWSRegularFile, get_aws_credentials

import StringIO
from tests.utils import StorageFunctionalTest


class Test(StorageFunctionalTest):

    def test_gridfs_to_s3(self):
        file_handler = StringIO.StringIO('File content here')
        user = User.get_one(db, {})
        file_id = RegularFile.put_to_fs(db, fs, 'asdfasdf', file_handler, user_id=user.get_id())

        user.s3 = True
        user.save(db)

        print dir(RegularFile.get_from_fs(db, fs, _id=file_id))

        with mock.patch('app.aws.put_file', return_value=len('File content here')) as put_file_mock:
            migrate_user_data(user.token)

        self.assertTrue(put_file_mock.called)

        aws_file = AWSRegularFile.get_from_fs(db, fs, _id=file_id)

        self.assertEqual(aws_file.length, 0)
        self.assertEqual(aws_file.aws_size, len('File content here'))

    def test_s3_to_gridfs(self):
        f = StringIO.StringIO('File content here')
        user = User.get_one(db, {})
        user.s3 = True
        user.save(db)

        with mock.patch('app.aws.put_file', return_value=len('File content here')):
            file_id = AWSRegularFile.put_to_fs(db, fs, 'asdfasdf', f, aws_credentials=get_aws_credentials(user), user_id=user.get_id())

        user.s3 = False
        user.save(db)

        with mock.patch('app.aws.get_file', return_value=f) as get_file_mock:
            migrate_user_data(user.token)

        self.assertTrue(get_file_mock.called)

        reg_file = RegularFile.get_from_fs(db, fs, _id=file_id)

        reg_file_handler = fs.get(file_id)

        self.assertEqual(reg_file_handler.read(), 'File content here')
        self.assertEqual(reg_file.length, len('File content here'))
