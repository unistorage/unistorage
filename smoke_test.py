import os
import glob
import shutil

from image_actions import convert, resize, make_grayscale


TEST_IMAGES_DIR = './test_images'

TEST_RESULTS_DIR = './test_results'
CONVERT_RESULTS_DIR = os.path.join(TEST_RESULTS_DIR, 'convert')
CROP_RESULTS_DIR = os.path.join(TEST_RESULTS_DIR, 'resize_w_crop')
GRAYSCALE_RESULTS_DIR = os.path.join(TEST_RESULTS_DIR, 'make_grayscale')

shutil.rmtree(TEST_RESULTS_DIR)
os.mkdir(TEST_RESULTS_DIR)
os.mkdir(CONVERT_RESULTS_DIR)
os.mkdir(CROP_RESULTS_DIR)
os.mkdir(GRAYSCALE_RESULTS_DIR)

# Test resize with crop
for source_file_name in os.listdir(TEST_IMAGES_DIR):
    source_file_path = os.path.join(TEST_IMAGES_DIR, source_file_name)
    
    with open(source_file_path) as source_file:
        print 'Cropping %s...' % source_file_name
        result = resize(source_file, 'crop', 110, 110)
        target_file_path = os.path.join(CROP_RESULTS_DIR,
                '%s_cropped%s' % os.path.splitext(source_file_name))

        with open(target_file_path, 'w') as target_file:
            target_file.write(result.getvalue())

# Test grayscaling
for source_file_name in os.listdir(TEST_IMAGES_DIR):
    source_file_path = os.path.join(TEST_IMAGES_DIR, source_file_name)
    
    with open(source_file_path) as source_file:
        print 'Grayscaling %s...' % source_file_name
        result = make_grayscale(source_file)
        target_file_path = os.path.join(GRAYSCALE_RESULTS_DIR,
                '%s_grayscaled%s' % os.path.splitext(source_file_name))

        with open(target_file_path, 'w') as target_file:
            target_file.write(result.getvalue())

# Test convert
for source_file_name in os.listdir(TEST_IMAGES_DIR):
    source_file_path = os.path.join(TEST_IMAGES_DIR, source_file_name)
    
    for format in ('gif', 'jpeg', 'bmp', 'tiff', 'png'):
        with open(source_file_path) as source_file:
            print 'Converting %s to %s...' % (source_file_name, format)
            result = convert(source_file, format)
            target_file_path = os.path.join(CONVERT_RESULTS_DIR,
                    '%s.%s' % (source_file_name, format))

            with open(target_file_path, 'w') as target_file:
                target_file.write(result.getvalue())

print 'Done\n!See results in %s' % TEST_RESULTS_DIR
