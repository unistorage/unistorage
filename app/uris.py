from flask import current_app, url_for, request


def parse_resource_uri(uri):
    endpoint = None
    endpoint_args = {}
    try:
        endpoint, endpoint_args = current_app.create_url_adapter(request).match(uri)
    except:
        pass
    return endpoint, endpoint_args


def parse_file_uri(uri):
    endpoint, args = parse_resource_uri(uri)
    if endpoint != 'storage.file_view' or '_id' not in args:
        raise ValueError('%s is not a file URI.' % uri)
    return args['_id']


def parse_template_uri(uri):
    endpoint, args = parse_resource_uri(uri)
    if endpoint != 'storage.template_view' or '_id' not in args:
        raise ValueError('%s is not a template URI.' % uri)
    return args['_id']


def get_resource_uri_for(resource_name, resource_id):
    return url_for('.%s_view' % resource_name, _id=resource_id, _external=False)
