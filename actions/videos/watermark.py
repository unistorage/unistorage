import os
import tempfile

import settings
import actions
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
            video_data = source_file.fileinfo

            video_width = video_data['video']['width']
            video_height = video_data['video']['height']
            wm_position = get_watermark_position(video_width, video_height, h_pad, v_pad, corner)
            wm_bbox = get_watermark_bbox(video_width, video_height, w, h)

            wm_tmp = None
            try:
                wm_tmp = resize_watermark(wm_file, wm_bbox)

                vf_params = 'movie=%s [wm];[in][wm] overlay=%s [out]' % (wm_tmp.name, wm_position)
                converter = Converter(avconv_path=settings.AVCONV_BIN,
                                      avprobe_path=settings.AVPROBE_BIN)

                fps = video_data['video']['fps']
                options = converter.parse_options({
                    'format': video_data['format'],
                    'video': {
                        'codec': video_data['video']['codec'],
                        'fps': fps and float('%.3f' % fps) or None,
                    },
                    'audio': {
                        'codec': video_data['audio']['codec'],
                        'bitrate': video_data['audio']['bitrate'] or 128,
                        'samplerate': video_data['audio']['samplerate'],
                    },
                })

                options.extend(['-vf', '%s' % vf_params])
                convertation = converter.avconv.convert(source_tmp.name, target_tmp.name, options)

                for step in convertation:
                    pass
                
                result = open(target_tmp.name)
                return result, video_data['format']
            finally:
                if wm_tmp:
                    os.unlink(wm_tmp.name)
