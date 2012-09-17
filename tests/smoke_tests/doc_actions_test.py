import os
import glob
import shutil
import unittest

from actions.docs.convert import perform as convert
from tests.utils import fixture_path


class SmokeTest(unittest.TestCase):
    TEST_DOCS_DIR = fixture_path('docs')
    TEST_RESULTS_DIR = './tests/smoke_tests/results/result_docs'

    @classmethod
    def setUpClass(cls):
        cls.CONVERT_RESULTS_DIR = os.path.join(cls.TEST_RESULTS_DIR, 'convert')

        if os.path.exists(cls.TEST_RESULTS_DIR):
            shutil.rmtree(cls.TEST_RESULTS_DIR)
        os.mkdir(cls.TEST_RESULTS_DIR)
        os.mkdir(cls.CONVERT_RESULTS_DIR)

    def test_convert(self):
        """Test convert"""
        for source_file_name in os.listdir(self.TEST_DOCS_DIR):
            source_file_path = os.path.join(self.TEST_DOCS_DIR, source_file_name)
            
            for format in ('html', 'doc', 'odt', 'pdf', 'rtf', 'html', 'txt'):
                with open(source_file_path) as source_file:
                    if __name__ == 'main':
                        print 'Converting %s to %s...' % (source_file_name, format)
                    result, _ = convert(source_file, format)
                    target_file_path = os.path.join(self.CONVERT_RESULTS_DIR,
                            '%s.%s' % (source_file_name, format))

                    with open(target_file_path, 'w') as target_file:
                        target_file.write(result.getvalue())


if __name__ == '__main__':
    unittest.main() 
    print 'Done\n!See results in %s' % SmokeTest.TEST_RESULTS_DIR
