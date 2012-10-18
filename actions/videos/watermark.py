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


def get_video_data(video_path):
    from converter import Converter

    c = Converter(avconv_path=settings.AVCONV_BIN, avprobe_path=settings.AVPROBE_BIN)
    data = c.probe(video_path)

    extension = os.path.splitext(video_path)[1]
    formats = data.format.format.split(',')

    result = {
        'format': extension in formats and extension or formats[0],
        'audio': {},
        'video': {}
    }

    for stream in data.streams:
        if stream.type == 'audio':
            result['audio'].update({
                'codec': stream.codec,
                'samplerate': stream.audio_samplerate
            })
        if stream.type == 'video':
            result['video'].update({
                'width': stream.video_width,
                'height': stream.video_height,
                'codec': stream.codec
            })

    return result


def resize_watermark(wm, wm_bbox):
    resized_wm, resized_wm_ext = image_resize(wm, 'keep', *wm_bbox)

    wm_tmp = tempfile.NamedTemporaryFile(suffix='.%s' % resized_wm_ext, delete=False)
    wm_tmp.write(resized_wm.read())
    wm_tmp.close()
    return wm_tmp


def perform(source_file, wm_file, w, h, h_pad, v_pad, corner):
    from converter import Avconv, Converter

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

        video_width = video_data['video']['width']
        video_height = video_data['video']['height']
        wm_position = get_watermark_position(video_width, video_height, h_pad, v_pad, corner)
        wm_bbox = get_watermark_bbox(video_width, video_height, w, h)
        wm_tmp = resize_watermark(wm_file, wm_bbox)

        vf_params = 'movie=%s [wm];[in][wm] overlay=%s [out]' % (wm_tmp.name, wm_position)
        avconv = Avconv(avconv_path=settings.AVCONV_BIN,
                        avprobe_path=settings.AVPROBE_BIN)
        video_codec = video_data['video']['codec']
        video_format = video_data['format']
        convertation = avconv.convert(source_tmp.name, target_tmp.name,
                                      ['-acodec', 'copy', '-vcodec', video_codec, '-f', video_format, '-vf', vf_params])

        try:
            for step in convertation:
                pass
        except:
            c = Converter(avconv_path=settings.AVCONV_BIN,
                          avprobe_path=settings.AVPROBE_BIN)
            options = c.parse_options({
                'format': 'avi',
                'audio': {
                    'codec': 'rawaudio',
                    'samplerate': 44100
                },
                'video': {'codec': 'rawvideo'}
            })
            convert_to_raw = ' '.join(
                [settings.AVCONV_BIN, '-i', source_tmp.name] + options + ['pipe:'])

            vcodec = video_data['video']['codec']
            acodec = video_data['audio']['codec']

            if vcodec not in c.vcodec_names:
                vcodec = c.vcodecs_avconv_name_to_name_map[vcodec]
            if acodec not in c.acodec_names:
                acodec = c.acodecs_avconv_name_to_name_map[acodec]

            options = c.parse_options({
                'format': video_data['format'],
                'audio': {
                    'codec': acodec,
                    'samplerate': video_data['audio']['samplerate']
                },
                'video': {'codec': vcodec}
            })

            watermark_and_convert_back = ' '.join(
                [settings.AVCONV_BIN, '-i', 'pipe:'] +
                options +
                ['-vf', '"%s"' % vf_params, '-y', target_tmp.name])

            command = '%s | %s' % (convert_to_raw, watermark_and_convert_back)
            convertation = avconv.run(command, shell=True)

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
