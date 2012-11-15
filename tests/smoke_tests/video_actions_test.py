import os

from actions.videos.convert import perform as convert
from actions.videos.watermark import perform as watermark
from actions.videos.extract_audio import perform as extract_audio
from tests.utils import fixture_path
from tests.smoke_tests import SmokeTest


TEST_SOURCE_DIR = fixture_path('./videos')
TEST_TARGET_DIR = './tests/smoke_tests/results/result_videos'


class Test(SmokeTest):
    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass(TEST_SOURCE_DIR, TEST_TARGET_DIR)

   #def test_convert(self):
        #results_dir = os.path.join(TEST_TARGET_DIR, 'convert')
        #os.makedirs(results_dir)

        #convert_targets = {
            #'ogg': {'vcodec': ['theora'], 'acodec': 'vorbis'},
            #'webm': {'vcodec': ['vp8'], 'acodec': 'vorbis'},
            #'flv': {'vcodec': ['h264', 'flv'], 'acodec': 'mp3'},
            #'mp4': {'vcodec': ['h264', 'divx'], 'acodec': 'mp3'},
            #'mkv': {'vcodec': ['h263', 'mpeg1', 'mpeg2'], 'acodec': 'mp3'},
        #}

        #for format in convert_targets:
            #acodec = convert_targets[format]['acodec']
            #for vcodec in convert_targets[format]['vcodec']:
                #for source_name, source_file in self.source_files():
                    #print '.', source_name
                    #result, ext = convert(source_file, format, vcodec, acodec, only_try=True)

                    #target_name = '%s_using_vcodec_%s_acodec_%s.%s' % \
                        #(source_name, vcodec, acodec, ext)
                    #target_path = os.path.join(results_dir, target_name)
                    #with open(target_path, 'w') as target_file:
                        #target_file.write(result.read())

    #def test_watermark(self):
        #results_dir = os.path.join(TEST_TARGET_DIR, 'watermark')
        #os.makedirs(results_dir)

        #for source_name, source_file in self.source_files():
            #watermark_file = open(os.path.join(fixture_path('watermarks'), 'watermark.png'))
            #result, ext = watermark(source_file, watermark_file, 100, 100, 10, 10, 'ne')

            #target_name = '%s_w_watermark.%s' % (source_name, ext)
            #target_path = os.path.join(results_dir, target_name)
            #with open(target_path, 'w') as target_file:
                #target_file.write(result.read())

    def test_extract_audio(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'watermark')
        os.makedirs(results_dir)

        for codec in ('alac', 'aac', 'vorbis', 'ac3', 'mp3', 'flac'):
            for source_name, source_file in self.source_files():
                print '.', source_name
                result, ext = extract_audio(source_file, codec)

                target_name = 'audio_from_%s.%s' % (source_name, ext)
                target_path = os.path.join(results_dir, target_name)
                with open(target_path, 'w') as target_file:
                    target_file.write(result.read())

