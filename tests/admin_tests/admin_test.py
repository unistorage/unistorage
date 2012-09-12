from flask import url_for

from tests.utils import FunctionalTest, ContextMixin


class FunctionalTest(ContextMixin, FunctionalTest):
    def setUp(self):
        super(FunctionalTest, self).setUp();
        self.index_url = url_for('admin.index')
        self.login_url = url_for('admin.login')
        self.logout_url = url_for('admin.logout')

    def login(self):
        form = self.app.get(self.login_url).form
        form.set('login', 'admin')
        form.set('password', 'admin')
        form.submit()

    def logout(self):
        self.app.get(self.logout_url)
    
    def test(self):
        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 302)
        self.assertTrue(self.login_url in r.headers['Location'])

        self.login()
        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 200)

        self.logout()
        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 302)
        self.assertTrue(self.login_url in r.headers['Location'])
