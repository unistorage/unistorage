# coding: utf-8
import unittest

from commands.compile_avconv_db import \
    parse_decoders, parse_encoders, parse_formats, make_avconv_db
from tests.utils import fixture_path


class Test(unittest.TestCase):
    def test(self):
        output_stream = open(fixture_path('ffmpeg_decoders_output.txt'))
        decoders = parse_decoders(output_stream)
        self.assertIn({'type': 'V', 'name': 'theora'}, decoders)
        self.assertNotIn({'type': 'V', 'name': 'libtheora'}, decoders)

        output_stream = open(fixture_path('ffmpeg_encoders_output.txt'))
        encoders = parse_encoders(output_stream)
        self.assertIn({'type': 'V', 'name': 'libtheora'}, encoders)

        output_stream = open(fixture_path('ffmpeg_formats_output.txt'))
        formats = parse_formats(output_stream)
        self.assertEqual({'encoding': False, 'decoding': True}, formats['dfa'])
        self.assertEqual({'encoding': True, 'decoding': True}, formats['mp4'])

        db = make_avconv_db(decoders=decoders, encoders=encoders, formats=formats)
        self.assertTrue(db['acodecs'])
        self.assertTrue(db['vcodecs'])
        self.assertTrue(db['formats'])
        self.assertTrue(db['vcodecs']['libtheora']['encoding'] and not \
                        db['vcodecs']['libtheora']['decoding'])
