import sys

import sh

from compile_avconv_db import compile_avconv_db
from compile_libmagic_db import compile_libmagic_db
from check_avconv_codecs import check_avconv_codecs


def test_quick():
    """Test quickly"""
    p = sh.nosetests('--exclude-dir=./tests/smoke_tests/', '--verbosity=2',
                     _out=sys.stdout, _err=sys.stderr)
    p.wait()


def test_cov():
    """Test and report coverage"""
    p = sh.nosetests('--with-coverage', '--cover-package=app,storage,actions',
                     '--cover-html', '--verbosity=2',
                     _out=sys.stdout, _err=sys.stderr)
    p.wait()


def test():
    """Test"""
    p = sh.nosetests('--verbosity=2', _out=sys.stdout, _err=sys.stderr)
    p.wait()


def make_docs():
    """Make documentation"""
    p = sh.Command('sphinx-build')('docs/', 'docs/_build/',
                                   _out=sys.stdout, _err=sys.stderr)
    p.wait()

