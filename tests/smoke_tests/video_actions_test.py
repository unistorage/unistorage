import os
import glob
import shutil
import unittest

from actions.videos.convert import perform as convert
from tests.utils import fixture_path


class SmokeTest(unittest.TestCase):
    TEST_VIDEOS_DIR = fixture_path('videos')
    TEST_RESULTS_DIR = './tests/smoke_tests/results/result_videos'

    CONVERT_TARGETS = {
        'ogg': {'vcodec': ['theora'], 'acodec': 'vorbis'},
        'webm': {'vcodec': ['vp8'], 'acodec': 'vorbis'},
        'flv': {'vcodec': ['h264', 'flv'], 'acodec': 'mp3'},
        'mp4': {'vcodec': ['h264', 'divx'], 'acodec': 'mp3'},
        'mkv': {'vcodec': ['h263', 'mpeg1', 'mpeg2'], 'acodec': 'mp3'},
    }

    @classmethod
    def setUpClass(cls):
        cls.CONVERT_RESULTS_DIR = os.path.join(cls.TEST_RESULTS_DIR, 'convert')

        if os.path.exists(cls.TEST_RESULTS_DIR):
            shutil.rmtree(cls.TEST_RESULTS_DIR)
        os.mkdir(cls.TEST_RESULTS_DIR)
        os.mkdir(cls.CONVERT_RESULTS_DIR)

    def test_convert(self):
        for source_file_name in os.listdir(self.TEST_VIDEOS_DIR):
            source_file_path = os.path.join(self.TEST_VIDEOS_DIR, source_file_name)
            
            for format in self.CONVERT_TARGETS:
                acodec = self.CONVERT_TARGETS[format]['acodec']
                for vcodec in self.CONVERT_TARGETS[format]['vcodec']:
                    with open(source_file_path) as source_file:
                        if __name__ == 'main':
                            print 'Converting %s to %s using %s...' % (source_file_name, format, vcodec)
                        result, _ = convert(source_file, format, vcodec, acodec, only_try=True)
                        target_file_path = os.path.join(self.CONVERT_RESULTS_DIR,
                                '%s_using_%s.%s' % (source_file_name, vcodec, format))

                        with open(target_file_path, 'w') as target_file:
                            target_file.write(result.read())

if __name__ == '__main__':
    unittest.main() 
    print 'Done\n!See results in %s' % SmokeTest.TEST_RESULTS_DIR
