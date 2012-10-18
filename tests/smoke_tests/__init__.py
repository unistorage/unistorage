import os
import shutil
import unittest


class SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls, source_dir, target_dir):
        cls.target_dir = target_dir
        cls.source_dir = source_dir
        if os.path.exists(cls.target_dir):
            shutil.rmtree(cls.target_dir)

    def source_files(self):
        for source_name in os.listdir(self.source_dir):
            source_path = os.path.join(self.source_dir, source_name)
            
            with open(source_path) as source_file:
                yield source_name, source_file
