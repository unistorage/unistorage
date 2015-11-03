#!/usr/bin/env python
import logging

from flask.ext.script import Manager
from flask.ext.assets import ManageAssets

logging.getLogger('webassets.script').setLevel(logging.WARNING)

from app import create_app


app = create_app()
manager = Manager(app)

from commands import *
manager.command(compile_avconv_db)
manager.command(compile_libmagic_db)
manager.command(test_quick)
manager.command(test_cov)
manager.command(test)
manager.command(make_docs)
manager.command(check_avconv_codecs)
manager.command(expire_zip_collections)
manager.command(delete_user_files)
manager.add_command('assets', ManageAssets())

if __name__ == '__main__':
    manager.run()
