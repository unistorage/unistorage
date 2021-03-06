from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test_capture_frame_to_jpeg(self):
        original_uri = self.put_file('videos/gizmo.mp4')

        self.check(original_uri, mime='video/mp4')
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

    def test_capture_frame_validation(self):
        original_uri = self.put_file('videos/gizmo.mp4')

        convert_action_url = '%s?action=capture_frame&to=png&position=10' % original_uri
        r = self.app.get(convert_action_url, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], '`position` must be less than video duration.')
