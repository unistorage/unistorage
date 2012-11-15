from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test_convert_mp3_to(self):
        original_uri = self.put_file('audios/god-save-the-queen.mp3')

        self.check(original_uri, mime='audio/mpeg')
        convert_action_url = '%s?action=convert&to=vorbis' % original_uri
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_url = r.json['resource_uri']
        r = self.app.get(converted_doc_url)
        self.check(converted_doc_url, mime='application/ogg')
