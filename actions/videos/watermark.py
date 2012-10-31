import os
import tempfile

import settings
import actions
from file_utils import get_video_data
from actions.utils import ValidationError
from actions.videos.utils import run_flvtool 
from actions.images.resize import perform as image_resize

name = 'watermark'
applicable_for = 'video'
result_type_family = 'video'


def validate_and_get_args(args, source_file=None):
    from converter import Converter
    c = Converter()  # XXX

    result = actions.common.watermark_validation.validate_and_get_args(args)
    
    data = source_file.fileinfo
    if not data['video'] or not data['audio']:
        raise ValidationError('Source video file must contain at least one audio and video stream')
    vcodec = data['video']['codec']
    acodec = data['audio']['codec']
    
    if acodec not in c.audio_codecs.keys():
        raise ValidationError('Sorry, we can\'t handle audio stream encoded using %s' % acodec)
    if vcodec not in c.video_codecs.keys():
        raise ValidationError('Sorry, we can\'t handle video stream encoded using %s' % vcodec)

    return result


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
    return CORNER_MAP[corner] % {'h_pad': wm_h_pad, 'v_pad': wm_v_pad}


def get_watermark_bbox(source_width, source_height, w, h):
    wm_width = get_dimension(source_width, w)
    wm_height = get_dimension(source_height, h)
    return (wm_width, wm_height)


def resize_watermark(wm, wm_bbox):
    resized_wm, resized_wm_ext = image_resize(wm, 'keep', *wm_bbox)

    wm_tmp = tempfile.NamedTemporaryFile(suffix='.%s' % resized_wm_ext, delete=False)
    wm_tmp.write(resized_wm.read())
    wm_tmp.close()
    return wm_tmp


def perform(source_file, wm_file, w, h, h_pad, v_pad, corner):
    from converter import Converter

    file_content = source_file.read()
    with tempfile.NamedTemporaryFile() as source_tmp:
        source_tmp.write(file_content)
        source_tmp.flush()

        with tempfile.NamedTemporaryFile(mode='rb') as target_tmp:
            data = get_video_data(file_content)
            video_data = data['video']
            audio_data = data['audio']

            video_width = video_data['width']
            video_height = video_data['height']

            wm_position = get_watermark_position(video_width, video_height, h_pad, v_pad, corner)
            wm_bbox = get_watermark_bbox(video_width, video_height, w, h)

            wm_tmp = None
            try:
                wm_tmp = resize_watermark(wm_file, wm_bbox)

                vf_params = 'movie=%s [wm];[in][wm] overlay=%s [out]' % (wm_tmp.name, wm_position)
                converter = Converter(avconv_path=settings.AVCONV_BIN,
                                      avprobe_path=settings.AVPROBE_BIN)

                fps = video_data['fps']
                options = converter.parse_options({
                    'format': data['format'],
                    'video': {
                        'codec': video_data['codec'],
                        'fps': fps and '%.3f' % fps or None,
                    },
                    'audio': {
                        'codec': audio_data['codec'],
                        'bitrate': audio_data['bitrate'] or 128,
                        'samplerate': audio_data['samplerate'],
                    },
                })

                options.extend(['-vf', '%s' % vf_params])
                convertation = converter.avconv.convert(source_tmp.name, target_tmp.name, options)

                for step in convertation:
                    pass
                
                if data['format'] == 'flv':
                    run_flvtool(target_tmp.name)
                
                return open(target_tmp.name), data['format']
            finally:
                if wm_tmp:
                    os.unlink(wm_tmp.name)
