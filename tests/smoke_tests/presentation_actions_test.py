import os

from actions.presentations.convert import perform as convert
from tests.utils import fixture_path
from tests.smoke_tests import SmokeTest


TEST_SOURCE_DIR = fixture_path('presentations')
TEST_TARGET_DIR = './tests/smoke_tests/results/result_presentations'


class Test(SmokeTest):
    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass(TEST_SOURCE_DIR, TEST_TARGET_DIR)

    def test_convert(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'convert')
        os.makedirs(results_dir)

        for format in ('pdf', 'ppt', 'odp'):
            for source_name, source_file in self.source_files():
                result, ext = convert(source_file, format)

                target_name = '%s.%s' % (source_name, ext)
                target_path = os.path.join(results_dir, target_name)
                with open(target_path, 'w') as target_file:
                    target_file.write(result.getvalue())
