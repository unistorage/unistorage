# coding: utf-8
"""По `label` конструирует список `actions` и записывает его
в данные файла.
"""
from bson import ObjectId

from app import db


actions = [
    'convert',
    'resize',
    'watermark',
    'grayscale',
    'rotate',
    'extract_audio',
    'capture_frame',
]


def process_watermark(parts):
    watermark_id = parts.pop(0)
    corner = parts.pop()
    arguments = [ObjectId(watermark_id)]

    while parts:
        x = parts.pop(0)
        if x == '0':
            x += '.' + parts.pop(0)
        if '.' in x:
            arg = float(x)
        else:
            arg = int(x)
        arguments.append(arg)

    arguments.append(corner)
    return arguments


def process_capture_frame(parts):
    format = parts.pop(0)
    seconds = float('.'.join(parts))
    return [format, seconds]


def process_resize(parts):
    mode = parts.pop(0)
    dimensions = map(lambda dim: None if dim == 'None' else int(dim), parts)
    arguments = [mode]
    arguments.extend(dimensions)
    return arguments


def parse(label):
    parts = label.split('_')

    action = parts.pop(0)
    if action not in actions:
        if parts:
            action += '_' + parts.pop(0)
        else:
            try:
                ObjectId(action)
            except:
                raise Exception('First argument is neither an action name '
                                'nor ObjectId.')
            else:
                return 'template', {}

    assert action in actions

    if action == 'watermark':
        return action, process_watermark(parts)
    if action == 'capture_frame':
        return action, process_capture_frame(parts)
    if action == 'resize':
        return action, process_resize(parts)
    if action == 'rotate':
        assert len(parts) == 1
        return action, [int(parts.pop())]
    if action == 'convert':
        return action, parts
    if action == 'extract_audio':
        return action, parts
    if action == 'grayscale':
        return action, []



def callback(id_, file_, log=None):
    label = file_.get('label')
    if label and not file_.get('actions'):
        try:
            action = parse(label)
            db.fs.files.update({'_id': id_}, {
               '$set': {'actions': [action]}
            })
        except:
            if log:
                log.write('%s Label: %s\n' % (id_, label))
            print '  Not fixed!'
        else:
            print '  Fixed: %s -> %s' % (label, action)
