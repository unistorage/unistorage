import sys

import nose
import sh

from compile_avconv_db import compile_avconv_db
from compile_libmagic_db import compile_libmagic_db
from check_avconv_codecs import check_avconv_codecs
from expire_zip_collections import expire_zip_collections


def test_quick():
    """Test quickly"""
    success = nose.run(argv=['tests', '--exclude-dir=./tests/smoke_tests/', '--verbosity=2'])
    exit(0 if success else 1)


def test_cov():
    """Test and report coverage"""
    success = nose.run(argv=['tests', '--with-coverage', '--cover-package=app,storage,actions',
        '--cover-html', '--verbosity=2'])
    exit(0 if success else 1)


def test():
    """Test"""
    success = nose.run(argv=['tests'])
    exit(0 if success else 1)


def make_docs():
    """Make documentation"""
    p = sh.Command('sphinx-build')('docs/', 'docs/_build/',
                                   _out=sys.stdout, _err=sys.stderr)
    p.wait()

