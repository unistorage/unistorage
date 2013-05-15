import os

from actions.images.convert import perform as convert
from actions.images.resize import perform as resize
from actions.images.grayscale import perform as grayscale
from actions.images.rotate import perform as rotate
from actions.images.watermark import perform as watermark
from tests.utils import fixture_path
from tests.smoke_tests import SmokeTest


TEST_SOURCE_DIR = fixture_path('images')
TEST_TARGET_DIR = './tests/smoke_tests/results/result_images'


class Test(SmokeTest):
    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass(TEST_SOURCE_DIR, TEST_TARGET_DIR)

    def test_resize_w_crop(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'resize_w_crop')
        os.makedirs(results_dir)

        for source_name, source_file in self.source_files():
            result, ext = resize(source_file, 'crop', 110, 110)

            target_name = '%s_cropped.%s' % (source_name, ext)
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.getvalue())

    def test_grayscaling(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'grayscale')
        os.makedirs(results_dir)

        for source_name, source_file in self.source_files():
            result, ext = grayscale(source_file)

            target_name = '%s_grayscaled.%s' % (source_name, ext)
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.getvalue())

    def test_convert(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'convert')
        os.makedirs(results_dir)

        for format in ('gif', 'jpeg', 'bmp', 'png'):
            for source_name, source_file in self.source_files():
                result, ext = convert(source_file, format)

                target_name = '%s.%s' % (source_name, ext)
                target_path = os.path.join(results_dir, target_name)
                with open(target_path, 'w') as target_file:
                    target_file.write(result.getvalue())

    def test_rotate(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'rotate')
        os.makedirs(results_dir)

        for source_name, source_file in self.source_files():
            result, ext = rotate(source_file, 90)
            
            target_name = '%s_rotated.%s' % (source_name, ext)
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.getvalue())

    def test_watermark(self):
        results_dir = os.path.join(TEST_TARGET_DIR, 'watermark')
        os.makedirs(results_dir)

        for source_name, source_file in self.source_files():
            watermark_file = open(os.path.join(fixture_path('watermarks'), 'watermark.png'))
            result, ext = watermark(source_file, watermark_file, 100, 100, 10, 10, 'ne')
            
            target_name = '%s_watermarked.%s' % (source_name, ext)
            target_path = os.path.join(results_dir, target_name)
            with open(target_path, 'w') as target_file:
                target_file.write(result.getvalue())
