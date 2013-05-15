from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test_extract_audio_from_3gp_to_mp3(self):
        original_uri = self.put_file('videos/gizmo.mp4')

        self.check(original_uri, mime='video/mp4')
        convert_action_url = '%s?action=extract_audio&to=mp3' % original_uri
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_uri = r.json['resource_uri']
        r = self.app.get(converted_doc_uri)
        self.check(converted_doc_uri, mime='audio/mpeg')
