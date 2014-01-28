# coding: utf-8
import os

from actions.videos.convert import perform as convert
from actions.videos.resize import perform as resize
from actions.videos.watermark import perform as watermark
from actions.videos.extract_audio import perform as extract_audio
from actions.videos.capture_frame import perform as capture_frame
from tests.utils import fixture_path
from tests.smoke_tests import SmokeTest


TEST_SOURCE_DIR = fixture_path('./videos')
TEST_TARGET_DIR = './tests/smoke_tests/results/result_videos'


class Test(SmokeTest):
    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass(TEST_SOURCE_DIR, TEST_TARGET_DIR)

    def test_convert(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'convert')
        os.makedirs(results_dir)

        convert_targets = {
            'ogg': {'vcodec': ['theora'], 'acodec': ['vorbis']},
            'webm': {'vcodec': ['vp8'], 'acodec': ['vorbis']},
            'flv': {'vcodec': ['h264', 'flv'], 'acodec': ['mp3', 'aac']},
            'mp4': {'vcodec': ['h264', 'divx'], 'acodec': ['mp3', 'aac']},
            'mkv': {'vcodec': ['h263', 'mpeg1', 'mpeg2'], 'acodec': ['mp3', 'aac']},
        }

        reduced_convert_targets = {  # because `convert_targets` take too long
            'ogg': {'vcodec': ['theora'], 'acodec': ['vorbis']},
            'webm': {'vcodec': ['vp8'], 'acodec': ['vorbis']},
            'flv': {'vcodec': ['flv'], 'acodec': ['aac']},
            'mkv': {'vcodec': ['h264', 'h263', 'mpeg1', 'mpeg2'], 'acodec': ['mp3']},
        }
        convert_targets = reduced_convert_targets

        def save(target_name, result):
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.read())

        for format in convert_targets:
            for acodec in convert_targets[format]['acodec']:
                for vcodec in convert_targets[format]['vcodec']:
                    for source_name, source_file in self.source_files():
                        result, ext = convert(source_file, format, vcodec, acodec)
                        target_name = '%s_using_vcodec_%s_acodec_%s.%s' % \
                            (source_name, vcodec, acodec, ext)
                        save(target_name, result)
                        
                        if vcodec == 'h264':
                            source_file.seek(0)
                            # h264 конвертируется в baseline-профиль при 
                            # max_compatibility, протестируем, что всё хорошо::
                            result, ext = convert(source_file, format, vcodec, acodec,
                                                  with_max_compatibility=True)
                            target_name = '%s_using_vcodec_%s_acodec_%s_with_max_comp.%s' % \
                                (source_name, vcodec, acodec, ext)
                            save(target_name, result)

    def test_resize_crop(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'resize_crop')
        os.makedirs(results_dir)

        for source_name, source_file in self.source_files():
            result, ext = resize(source_file, 'crop', 30, 100)

            target_name = '%s_crop_30_100.%s' % (source_name, ext)
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.read())

        for source_name, source_file in self.source_files():
            result, ext = resize(source_file, 'crop', 300, 1000)

            target_name = '%s_crop_300_1000_upscale.%s' % (source_name, ext)
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.read())

    def test_resize_keep(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'resize_keep')
        os.makedirs(results_dir)

        for source_name, source_file in self.source_files():
            result, ext = resize(source_file, 'keep', 300, 1000)

            target_name = '%s_keep_50_50.%s' % (source_name, ext)
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.read())

    def test_watermark(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'watermark')
        os.makedirs(results_dir)

        for source_name, source_file in self.source_files():
            watermark_file = open(os.path.join(fixture_path('watermarks'), 'watermark.png'))
            result, ext = watermark(source_file, watermark_file, 100, 100, 10, 10, 'ne')

            target_name = '%s_w_watermark.%s' % (source_name, ext)
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.read())

    def test_extract_audio(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'extracted_audios')
        os.makedirs(results_dir)

        for codec in ('alac', 'aac', 'vorbis', 'ac3', 'mp3', 'flac'):
            for source_name, source_file in self.source_files():
                if source_name == 'no-audio.flv':
                    continue
                result, ext = extract_audio(source_file, codec)

                target_name = 'audio_from_%s.%s' % (source_name, ext)
                target_path = os.path.join(results_dir, target_name)
                with open(target_path, 'w') as target_file:
                    target_file.write(result.read())

    def test_capture_frame(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'captured_frames')
        os.makedirs(results_dir)

        for format in ('gif', 'bmp', 'gif', 'jpeg', 'png'):
            for source_name, source_file in self.source_files():
                result, ext = capture_frame(source_file, format, 1)

                target_name = 'frame_from_%s.%s' % (source_name, ext)
                target_path = os.path.join(results_dir, target_name)
                with open(target_path, 'w') as target_file:
                    r = result.read()
                    target_file.write(r)
