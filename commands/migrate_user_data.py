# coding: utf-8
from app import db, fs, aws
from app.models import User, File


def migrate_file_s3_to_gridfs(user, f):
    """Migrates file"""
    aws_credentials = aws.get_aws_credentials(user)
    db['fs.files'].remove(f['_id'])

    file_handler = aws.get_file(aws_credentials['aws_bucket_name'], f['_id'])
    del f['aws_bucket_name']

    fs.put(file_handler.read(), **f)


def migrate_file_gridfs_to_s3(user, f):
    """Migrates file"""
    aws_credentials = aws.get_aws_credentials(user)
    # Кладем данные в амазон
    f.aws_size = aws.put_file(
        aws_credentials=aws_credentials,
        file_id=f.get_id(),
        file=fs.get(f.get_id()),
        content_type=f.content_type,
        filename=f.filename)
    f.aws_bucket_name = aws_credentials['aws_bucket_name']

    # remove chunks from gridfs
    db['fs.chunks'].remove({'files_id': f.get_id()})
    f.length = 0

    f.save(db)


def migrate_user_data(user_token):
    """Migrates user data"""

    try:
        user = User.find(db, {'token': user_token})[0]
    except Exception:
        return "user with token {} not found".format(user_token)
    while True:
        if user.s3:
            # gridfs -> S3
            f = File.get_one(db, {'user_id': user.get_id(), 'aws_bucket_name': {'$exists': False}})
            if not f:
                break
            migrate_file_gridfs_to_s3(user, f)

        else:
            #S3 -> gridfs
            f = File.get_one(db, {'user_id': user.get_id(), 'aws_bucket_name': {'$exists': True}})
            if not f:
                break
            migrate_file_s3_to_gridfs(user, f)

        print f.get_id()

    print "migration accomplished"
