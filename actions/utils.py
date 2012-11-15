# -*- coding: utf-8 -*-
UNISTORAGE_TYPES = ('unknown', 'image', 'video', 'audio', 'doc')

DOCUMENT_TYPES = (
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.oasis.opendocument.text', 'application/pdf', 'application/vnd.pdf',
    'application/x-pdf', 'application/rtf', 'application/x-rtf', 'text/richtext',
    'text/plain', 'text/html')


def get_unistorage_type(content_type, extra=None):
    """По `content_type` файла и, возможно, дополнительной информации (поле `extra` в БД)
    выясняет "семейство типов", к которому принадлежит файл: 'image', 'video', 'audio' или 'doc'.
    """
    if content_type.startswith('image'):
        return 'image'

    if content_type == 'application/ogg':
        # application/ogg может быть как видео, так и аудио. Если указана дополнительная
        # информация -- выясняем, какие потоки есть в наличии:
        if extra and extra.get('audio') and not extra.get('video'):
            return 'audio'
        else:
            return 'video'

    if content_type.startswith('video'):
        return 'video'
    
    if content_type.startswith('audio') or \
            content_type in ('application/adts', 'application/pcm'):
        return 'audio'

    if content_type in DOCUMENT_TYPES:
        return 'doc'
    
    return 'unknown'


class ValidationError(Exception):
    pass
