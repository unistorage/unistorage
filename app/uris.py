from flask import current_app


def parse_resource_uri(uri):
    endpoint = None
    endpoint_args = {}
    try:
        endpoint, endpoint_args = current_app.url_map.bind('/').match(uri)
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