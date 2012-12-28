from tests.utils import StorageFunctionalTest


class ValidationTest(StorageFunctionalTest):
    def test_unsupported_codecs_validation(self):
        source_uri = self.put_file('videos/no-audio.flv')
        
        extract_audio_action_url = '%s?action=extract_audio&to=mp3' % source_uri
        r = self.app.get(extract_audio_action_url, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], 'Source file has no audio stream.')

