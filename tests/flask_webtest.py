import unittest
from copy import copy
from functools import partial

from flask import template_rendered
from webtest import TestApp


class ContextList(list):
    def __getitem__(self, key):
        if isinstance(key, basestring):
            for subcontext in self:
                if key in subcontext:
                    return subcontext[key]
            raise KeyError(key)
        else:
            return super(ContextList, self).__getitem__(key)

    def __contains__(self, key):
        try:
            value = self[key]
        except KeyError:
            return False
        return True


def store_rendered_templates(store, app, template, context):
    store.setdefault('templates', []).append(template)
    store.setdefault('context', ContextList()).append(copy(context))


def flattend(l):
    return l[0] if len(l) == 1 else l


class FlaskTestApp(TestApp):
    def __init__(self, app):
        super(FlaskTestApp, self).__init__(app)

    def do_request(self, req, status, expect_errors):
        data = {}
        on_template_render = partial(store_rendered_templates, data)

        template_rendered.connect(on_template_render)
        try:
            response = super(FlaskTestApp, self).do_request(req, status, expect_errors)
        finally:
            template_rendered.disconnect(on_template_render)

        context = data.get('context')
        templates = data.get('templates')
        if context:
            response.context = flattend(context)
        if templates:
            response.templates = templates
            if len(templates) == 1:
                response.template = templates[0]

        return response


class FlaskTestCase(unittest.TestCase):
    def assertTemplateUsed(self, response, template_name):
        if not hasattr(response, 'templates'):
            self.fail('No templates used to render the response')
        template_names = [t.name for t in response.templates]
        self.assertTrue(template_name in template_names,
            'Template "%s" was not a template used to render'
            ' the response. Actual template(s) used: %s' %
                (template_name, ', '.join(template_names)))
