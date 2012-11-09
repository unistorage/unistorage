import os.path

import sh

import settings


def compile_libmagic_db():
    "Compile libmagic database"
    assert sh.which('file')
    file_ = sh.Command('file')
    libmagic_db_source = os.path.join(settings.PROJECT_PATH, 'magic')
    file_('-C', '-m', libmagic_db_source)
    assert os.path.exists(settings.MAGIC_DB_PATH)
