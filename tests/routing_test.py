from tests.utils import StorageFunctionalTest
import mock

import celeryconfig


class FunctionalTest(StorageFunctionalTest):
    def get_route(self):
        router = celeryconfig.Router()
        task, args, kwargs = self.sent_tasks.pop()
        return router.route_for_task(task, args, kwargs)

    def test(self):
        image_uri = self.put_file('images/some.jpeg')
        video_uri = self.put_file('videos/video.webm')

        self.app.get('%s?action=convert&to=gif' % image_uri)
        self.assertEqual(self.get_route()['routing_key'], 'images')

        self.app.get('%s?action=capture_frame&position=1&to=jpeg' % video_uri)
        self.assertEqual(self.get_route()['routing_key'], 'non-images')

        self.app.get('%s?action=convert&to=jpeg&with_low_priority' % image_uri)
        self.assertEqual(self.get_route()['routing_key'], 'low-priority')

    def test_s3(self):
        self.patch_user({'s3': True})
        with mock.patch('app.aws.put_file'):
            s3_file_uri = self.put_file('images/some.jpeg')

        self.app.get('%s?action=convert&to=gif' % s3_file_uri)
        self.assertEqual(self.get_route()['routing_key'], 's3-images')
