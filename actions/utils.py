TYPE_FAMILIES = ('image', 'video', 'doc')

DOCUMENT_TYPES = (
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.oasis.opendocument.text', 'application/pdf', 'application/vnd.pdf',
    'application/x-pdf', 'application/rtf', 'application/x-rtf', 'text/richtext',
    'text/plain', 'text/html')


def get_type_family(content_type):
    if content_type.startswith('image'):
        return 'image'

    if content_type.startswith('video') or content_type in ('application/ogg',):
        return 'video'

    if content_type in DOCUMENT_TYPES:
        return 'doc'
    
    return None


class ValidationError(Exception):
    pass
