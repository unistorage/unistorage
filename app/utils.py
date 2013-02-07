# coding: utf-8
import os.path
from StringIO import StringIO
from tempfile import NamedTemporaryFile

from bson import ObjectId
from bson.errors import InvalidId
from werkzeug.routing import BaseConverter, ValidationError
from flask.wrappers import Request


class ObjectIdConverter(BaseConverter):
    def to_python(self, value):
        try:
            return ObjectId(value)
        except InvalidId:
            raise ValidationError()

    def to_url(self, value):
        return str(value)


def stream_factory(total_content_length, content_type, filename='',
                   content_length=None):
    """Замена :func:`werkzeug.formparser.default_stream_factory`.
    Возвращает NamedTemporaryFile, а не TemporaryFile, что позволяет
    передать файл на вход `ffmpeg` без копирования.
    """
    name, extension = os.path.splitext(filename)
    if total_content_length > 1024 * 500:
        return NamedTemporaryFile('wb+', suffix=extension)
    return StringIO()


class CustomRequest(Request):
    """Наследник :class:`flask.wrappers.Request`, использующий
    :func:`stream_factory`.
    """
    def _get_file_stream(self, total_content_length, content_type,
                         filename=None, content_length=None):
        return stream_factory(total_content_length, content_type,
                              filename=filename, content_length=content_length)
