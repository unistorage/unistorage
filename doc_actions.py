import subprocess
import socket
import shutil
import tempfile
import time
import os
from StringIO import StringIO

import uno
import unohelper
from com.sun.star.connection import NoConnectException
from com.sun.star.beans import PropertyValue
from com.sun.star.io import XOutputStream

import settings
from tasks import ActionException


# Utils
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 0))
    _, port = s.getsockname()
    s.close()
    return port


class OutputStream(unohelper.Base, XOutputStream):
    def __init__(self, descriptor=None):
        self.descriptor = descriptor
        self.closed = 0

    def closeOutput(self):
        self.closed = 1
        if not self.descriptor.isatty:
            self.descriptor.close()

    def writeBytes(self, seq):
        self.descriptor.write(seq.value)

    def flush(self):
        pass


def to_properties(d):
    return tuple(PropertyValue(key, 0, value, 0) for key, value in d.iteritems())
# /Utils


def start_openoffice(home_dir, port):
    args = [settings.OPENOFFICE_BIN,
            '--accept=socket,host=localhost,port=%d;urp;StarOffice.ServiceManager' % port,
            '--userid="%s"' % home_dir,
            '--norestore', '--nofirststartwizard', '--nologo', '--nocrashreport',
            '--nodefault', '--quickstart', '--norestart', '--nolockcheck', '--headless']
    custom_env = os.environ.copy()
    custom_env['HOME'] = home_dir

    try:
        popen = subprocess.Popen(args, env=custom_env)
        pid = popen.pid
    except Exception, e:
        raise ActionException('Failed to start OpenOffice on port %d: %s' % (port, e.message))

    if pid <= 0:
        raise ActionException('Failed to start OpenOffice on port %d' % port)

    context = uno.getComponentContext()
    svc_mgr = context.ServiceManager
    resolver = svc_mgr.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', context)
    connection_params = 'uno:socket,host=%s,port=%s;urp;' \
                        'StarOffice.ComponentContext' % ('localhost', port)

    uno_context = None
    for times in xrange(5):
        try:
            uno_context = resolver.resolve(connection_params)
            break
        except NoConnectException:
            time.sleep(1)

    if not uno_context:
        raise ActionException('Failed to connect to OpenOffice on port %d' % port)

    uno_svc_mgr = uno_context.ServiceManager
    desktop = uno_svc_mgr.createInstanceWithContext('com.sun.star.frame.Desktop', uno_context)
    return popen, context, desktop


FILTER_MAP = {
    'doc': 'MS Word 97',
    'docx': 'MS Word 2007 XML',
    'odt': 'writer8',
    'pdf': 'writer_pdf_Export',
    'rtf': 'Rich Text Format',
    'txt': 'Text (encoded)',
    'html': 'XHTML Writer File',
} 


def convert(source_file, format):
    port = get_free_port()
    home_dir = tempfile.mkdtemp()
    output_stream = StringIO()

    try:
        popen, context, desktop = start_openoffice(home_dir, port)
        
        input_stream = context.ServiceManager.createInstanceWithContext(
                'com.sun.star.io.SequenceInputStream', context)
        input_stream.initialize((uno.ByteSequence(source_file.read()),))

        doc = desktop.loadComponentFromURL('private:stream', '_blank', 0, to_properties({
           'InputStream': input_stream,
        }))
        doc.storeToURL('private:stream', to_properties({
            'FilterData': uno.Any('[]com.sun.star.beans.PropertyValue', tuple(),),
            'FilterName': FILTER_MAP[format],
            'OutputStream': OutputStream(output_stream),
            'Overwrite': True
        }))

        source_file.close()
        doc.dispose()
        doc.close(True)

        try:
            desktop.terminate()
            # Sometimes it throws error:
            # com.sun.star.lang.DisposedException: Binary URP bridge disposed during call
            # But it doesn't seem to affect anything, so just pass
        except Exception:
            pass
        return_code = popen.wait()
        if return_code != 0:
            raise ActionException()
    finally:
        shutil.rmtree(home_dir)
        
    return output_stream, format
