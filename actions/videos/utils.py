import subprocess

import settings
from actions import ActionException


def run_flvtool(file_path):
    try:
        proc = subprocess.Popen([settings.FLVTOOL_BIN, '-U', file_path],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except OSError:
        raise ActionException('Failed to start `flvtool`: %s' % settings.FLVTOOL_BIN)
    stdout_data, stderr_data = proc.communicate()
    return_code = proc.wait()
    if return_code != 0:
        raise ActionException('`flvtool` failed. Stderr: %s' % stderr_data)
