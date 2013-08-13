# coding: utf-8
import mimetypes


UNISTORAGE_TYPES = ('unknown', 'image', 'video', 'audio', 'doc', 'presentation')

DOCUMENT_TYPES = (
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.oasis.opendocument.text', 'application/pdf', 'application/vnd.pdf',
    'application/x-pdf', 'application/rtf', 'application/x-rtf', 'text/richtext',
    'text/plain', 'text/html')

PRESENTATION_TYPES = (
    'application/vnd.ms-powerpoint',
    'application/vnd.oasis.opendocument.presentation',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
)


def get_unistorage_type(content_type, file_name=None, extra=None):
    """По `content_type` файла и, возможно, дополнительной информации (имя файла, 
    поле `extra` в БД) выясняет :term:`unistorage_type`, к которому принадлежит файл.
    Если параметр `extra` не указан, результат считается предположительным.
    """
    if content_type.startswith('image'):
        if extra is None:
            return 'image'
        else:
            if 'width' in extra and 'height' in extra:
                return 'image'
            else:
                return 'unknown'

    if content_type == 'application/ogg':
        # application/ogg может быть как видео, так и аудио. Если указана дополнительная
        # информация -- выясняем, какие потоки есть в наличии.
        if extra is None:
            return 'video'
        else:
            audio = extra.get('audio')
            video = extra.get('video')
            if audio and not video:
                return 'audio'
            elif video:
                return 'video'
            else:
                return 'unknown'

    if content_type.startswith('video') or content_type.endswith('octet-stream'):
        if extra is None:
            if content_type.startswith('video'):
                return 'video'
            else:
                return 'unknown'
        else:
            audio = extra.get('audio')
            video = extra.get('video')
            if audio and not video:
                return 'audio'
            elif video:
                return 'video'
            else:
                return 'unknown'

    if content_type.startswith('audio') or \
            content_type in ('application/adts', 'application/pcm'):
        return 'audio'

    if content_type == 'application/msword':
        if mimetypes.guess_type(file_name) in PRESENTATION_TYPES:
            return 'presentation'
        else:
            return 'doc'

    if content_type in DOCUMENT_TYPES:
        return 'doc'

    if content_type in PRESENTATION_TYPES:
        return 'presentation'
    
    return 'unknown'


class ValidationError(Exception):
    pass


class ActionError(Exception):
    pass
