from tests.utils import FunctionalTest, WorkerMixin, ContextMixin


class FunctionalTest(FunctionalTest, WorkerMixin):
    def test_convert_docx_to_html(self):
        original_id = self.put_file('./docs/test.docx')

        url = '/%s/' % original_id
        r = self.app.get(url, headers=self.headers)
        self.check(url, mime='application/msword')
        
        convert_action_url = url + '?action=convert&to=html'
        r = self.app.get(convert_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_url = '/%s/' % r.json['id']
        r = self.app.get(converted_doc_url, headers=self.headers)
        mimetype = r.json['information']['mimetype']
        self.assertTrue('xml' in mimetype or 'html' in mimetype)

    def test_convert_odt_to_pdf(self):
        original_id = self.put_file('./docs/test.odt')

        url = '/%s/' % original_id
        self.check(url, mime='application/vnd.oasis.opendocument.text')
        
        convert_action_url = url + '?action=convert&to=pdf'
        r = self.app.get(convert_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_url = '/%s/' % r.json['id']
        r = self.app.get(converted_doc_url, headers=self.headers)
        self.check(converted_doc_url, mime='application/pdf')
