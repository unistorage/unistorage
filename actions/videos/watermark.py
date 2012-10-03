import os
import tempfile

from flask import g
from bson.objectid import ObjectId
from converter import FFMpeg, Converter

import settings
import actions
from actions import ActionException
from actions.utils import ValidationError, get_type_family
from actions.images.resize import perform as image_resize


name = 'watermark'
applicable_for = 'video'
result_type_family = 'video'
validate_and_get_args = actions.common.watermark_validation.validate_and_get_args


CORNER_MAP = {
    'ne': 'main_w-overlay_w-%(v_pad)d:%(h_pad)d',
    'se': 'main_w-overlay_w-%(v_pad)d:main_h-overlay_h-%(h_pad)d',
    'sw': '%(v_pad)d:main_h-overlay_h-%(h_pad)d',
    'nw': '%(v_pad)d:%(h_pad)d'
}


def get_dimension(value, percents_or_pixels):
    if isinstance(percents_or_pixels, float):
        return round(percents_or_pixels * value)
    else:
        return percents_or_pixels


def get_watermark_position(source_width, source_height, h_pad, v_pad, corner):
    wm_h_pad = get_dimension(source_width, h_pad)
    wm_v_pad = get_dimension(source_height, v_pad)
    return CORNER_MAP[corner] % {'h_pad': h_pad, 'v_pad': v_pad}


def get_watermark_bbox(source_width, source_height, w, h):
    wm_width = get_dimension(source_width, w)
    wm_height = get_dimension(source_height, h)
    return (wm_width, wm_height)


def get_video_data(video_path):
    c = Converter(ffmpeg_path=settings.FFMPEG_BIN, ffprobe_path=settings.FFPROBE_BIN)
    data = c.probe(video_path)
    for stream in data.streams:
        if stream.type == 'video':
            return {
                'width': stream.video_width,
                'height': stream.video_height,
                'format': data.format.format.split(',', 1)[0]
            }


def resize_watermark(wm, wm_bbox):
    resized_wm, resized_wm_ext = image_resize(wm, 'keep', *wm_bbox)

    wm_tmp = tempfile.NamedTemporaryFile(
            suffix='.%s' % resized_wm_ext, delete=False)
    wm_tmp.write(resized_wm.read())
    wm_tmp.close()
    return wm_tmp


def perform(source_file, wm_file, w, h, h_pad, v_pad, corner):
    source_tmp = None
    target_tmp = None
    wm_tmp = None
    try:
        source_tmp = tempfile.NamedTemporaryFile(delete=False)
        source_tmp.write(source_file.read())
        source_tmp.close()

        target_tmp = tempfile.NamedTemporaryFile(delete=False)
        target_tmp.close()

        video_data = get_video_data(source_tmp.name)
        video_width = video_data['width']
        video_height = video_data['height']
        video_format = video_data['format']

        wm_position = get_watermark_position(video_width, video_height, h_pad, v_pad, corner)
        wm_bbox = get_watermark_bbox(video_width, video_height, w, h)
        wm_tmp = resize_watermark(wm_file, wm_bbox)

        ffmpeg = FFMpeg()
        convertation = ffmpeg.convert(source_tmp.name, target_tmp.name, [
            '-acodec', 'copy', '-f', video_format,
            '-vf', 'movie=%s [wm];[in][wm] overlay=%s [out]' % (wm_tmp.name, wm_position),
        ])
        
        for step in convertation:
            pass

        result = open(target_tmp.name)
    finally:
        if target_tmp:
            os.unlink(target_tmp.name)
        if source_tmp:
            os.unlink(source_tmp.name)
        if wm_tmp:
            os.unlink(wm_tmp.name)

    return result, video_data['format']
