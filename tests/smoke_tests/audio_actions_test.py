import os

from actions.audios.convert import perform as convert
from tests.utils import fixture_path
from tests.smoke_tests import SmokeTest


TEST_SOURCE_DIR = fixture_path('./audios')
TEST_TARGET_DIR = './tests/smoke_tests/results/result_audios'


class Test(SmokeTest):
    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass(TEST_SOURCE_DIR, TEST_TARGET_DIR)

    def test_convert(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'convert')
        os.makedirs(results_dir)

        for codec in ('alac', 'aac', 'vorbis', 'ac3', 'mp3', 'flac'):
            for source_name, source_file in self.source_files():
                result, ext = convert(source_file, codec)

                target_name = '%s.%s' % (source_name, ext)
                target_path = os.path.join(results_dir, target_name)
                with open(target_path, 'w') as target_file:
                    target_file.write(result.read())
