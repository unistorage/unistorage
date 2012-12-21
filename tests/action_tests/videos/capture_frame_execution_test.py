from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test_capture_frame_to_jpeg(self):
        original_uri = self.put_file('videos/sample.3gp')

        self.check(original_uri, mime='video/3gpp')
        convert_action_url = '%s?action=capture_frame&to=jpeg&position=1' % original_uri
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        extracted_frame_uri = r.json['resource_uri']
        r = self.app.get(extracted_frame_uri)
        self.check(extracted_frame_uri, mime='image/jpeg')

    def test_capture_frame_to_png(self):
        original_uri = self.put_file('videos/gizmo.mp4')

        convert_action_url = '%s?action=capture_frame&to=png&position=1' % original_uri
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        extracted_frame_uri = r.json['resource_uri']
        r = self.app.get(extracted_frame_uri)
        self.check(extracted_frame_uri, mime='image/png')
