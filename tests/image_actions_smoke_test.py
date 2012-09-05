import os
import glob
import shutil
import unittest

from image_actions import convert, resize, make_grayscale


class SmokeTest(unittest.TestCase):
    TEST_IMAGES_DIR = './tests/images'
    TEST_RESULTS_DIR = './tests/result_images'

    @classmethod
    def setUpClass(cls):
        cls.CONVERT_RESULTS_DIR = os.path.join(cls.TEST_RESULTS_DIR, 'convert')
        cls.CROP_RESULTS_DIR = os.path.join(cls.TEST_RESULTS_DIR, 'resize_w_crop')
        cls.GRAYSCALE_RESULTS_DIR = os.path.join(cls.TEST_RESULTS_DIR, 'make_grayscale')

        if os.path.exists(cls.TEST_RESULTS_DIR):
            shutil.rmtree(cls.TEST_RESULTS_DIR)
        os.mkdir(cls.TEST_RESULTS_DIR)
        os.mkdir(cls.CONVERT_RESULTS_DIR)
        os.mkdir(cls.CROP_RESULTS_DIR)
        os.mkdir(cls.GRAYSCALE_RESULTS_DIR)

    def _util(self, results_dir, postfix):
        for source_name in os.listdir(self.TEST_IMAGES_DIR):
            source_file_path = os.path.join(self.TEST_IMAGES_DIR, source_name)
            
            with open(source_file_path) as source_file:
                name, ext = os.path.splitext(source_name)
                target_file_path = os.path.join(results_dir, '%s_%s%s' % (name, postfix, ext))
                with open(target_file_path, 'w') as target_file:
                    yield source_file, source_name, target_file

    def test_resize_w_crop(self):
        """Test resize with crop mode"""
        for source_file, source_name, target_file in self._util(self.CROP_RESULTS_DIR, 'cropped'):
            if __name__ == 'main':
                print 'Cropping %s...' % source_name
            result, _ = resize(source_file, 'crop', 110, 110)
            target_file.write(result.getvalue())

    def test_grayscaling(self):
        """Test grayscaling"""
        for source_file, source_name, target_file in self._util(self.GRAYSCALE_RESULTS_DIR, 'grayscaled'):
            if __name__ == 'main':
                print 'Grayscaling %s...' % source_name
            result, _ = make_grayscale(source_file)
            target_file.write(result.getvalue())

    def test_convert(self):
        """Test convert"""
        for source_file_name in os.listdir(self.TEST_IMAGES_DIR):
            source_file_path = os.path.join(self.TEST_IMAGES_DIR, source_file_name)
            
            for format in ('gif', 'jpeg', 'bmp', 'tiff', 'png'):
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
