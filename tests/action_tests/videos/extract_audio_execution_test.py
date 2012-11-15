from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test_extract_audio_from_3gp_to_mp3(self):
        original_uri = self.put_file('videos/sample.3gp')

        self.check(original_uri, mime='video/3gpp')
        convert_action_url = '%s?action=extract_audio&to=mp3' % original_uri
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_url = r.json['resource_uri']
        r = self.app.get(converted_doc_url)
        self.check(converted_doc_url, mime='audio/mpeg')
