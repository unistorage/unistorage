import os
import tempfile
import cPickle as pickle

import settings
import actions
from file_utils import get_video_data
from actions.utils import ValidationError
from actions.videos.utils import run_flvtool 
from actions.images.resize import perform as image_resize
from actions.videos.avconv import avprobe, avconv, vcodec_encoders, acodec_encoders


name = 'watermark'
applicable_for = 'video'
result_type_family = 'video'


with open(settings.AVCONV_DB_PATH) as f:
    avconv_db = pickle.load(f)


def validate_and_get_args(args, source_file=None):
    result = actions.common.watermark_validation.validate_and_get_args(args)

    data = source_file.fileinfo
    if not data['video'] or not data['audio']:
        raise ValidationError('Source video file must contain at least one audio and video stream')
    
    acodec_name = data['audio']['codec']
    vcodec_name = data['video']['codec']
    
    acodec = avconv_db['acodecs'].get(acodec_name)
    acodec_encoder = acodec
    if acodec_name in acodec_encoders:
        acodec_encoder_name = acodec_encoders[acodec_name]
        acodec_encoder = avconv_db['acodecs'].get(acodec_encoder_name)

    if not acodec or not acodec['decoding'] or not acodec_encoder['encoding']:
        raise ValidationError('Sorry, we can\'t handle audio stream encoded using %s' % acodec_name)
    
    vcodec = avconv_db['vcodecs'].get(vcodec_name)
    vcodec_encoder = vcodec
    if vcodec_name in vcodec_encoders:
        vcodec_encoder_name = vcodec_encoders[vcodec_name]
        vcodec_encoder = avconv_db['vcodecs'].get(vcodec_encoder_name)
    if not vcodec or not vcodec['decoding'] or not vcodec_encoder['encoding']:
        raise ValidationError('Sorry, we can\'t handle video stream encoded using %s' % vcodec_name)

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
    source_file_ext = '' 
    if hasattr(source_file, 'filename'):
        source_file_name, source_file_ext = os.path.splitext(source_file.filename)

    file_content = source_file.read()
    with tempfile.NamedTemporaryFile(suffix=source_file_ext) as source_tmp:
        source_tmp.write(file_content)
        source_tmp.flush()

        with tempfile.NamedTemporaryFile(mode='rb') as target_tmp:
            data = avprobe(source_tmp.name)
            video_width = data['video']['width']
            video_height = data['video']['height']
            wm_position = get_watermark_position(video_width, video_height, h_pad, v_pad, corner)
            wm_bbox = get_watermark_bbox(video_width, video_height, w, h)
            wm_tmp = None
            try:
                wm_tmp = resize_watermark(wm_file, wm_bbox)
                vf_params = 'movie=%s [wm];[in][wm] overlay=%s [out]' % (wm_tmp.name, wm_position)
                data['video']['filters'] = vf_params

                data['audio']['bitrate'] = data['audio'].get('bitrate') or '128k'

                fps = data['video'].get('fps')
                if fps:
                    data['video']['fps'] = '%.3f' % fps

                avconv(source_tmp.name, target_tmp.name, data)
                if data['format'] == 'flv':
                    run_flvtool(target_tmp.name)
                return open(target_tmp.name), data['format']
            finally:
                if wm_tmp:
                    os.unlink(wm_tmp.name)
