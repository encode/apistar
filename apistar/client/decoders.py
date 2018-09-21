import cgi
import json
import os
import posixpath
import shutil
import tempfile
from urllib.parse import urlparse

from apistar.compat import DownloadedFile


class BaseDecoder:
    media_type = None

    def decode(self, bytestring, **options):
        raise NotImplementedError()


class JSONDecoder(BaseDecoder):
    media_type = 'application/json'

    def decode(self, response):
        """
        Return raw JSON data.
        """
        content = response.content.decode('utf-8')
        return json.loads(content)


class TextDecoder(BaseDecoder):
    media_type = 'text/*'

    def decode(self, response):
        return response.text


class DownloadDecoder(BaseDecoder):
    """
    A codec to handle raw file downloads, such as images and other media.
    """
    media_type = '*/*'

    def __init__(self, download_dir=None):
        """
        `download_dir` - If `None` then downloaded files will be temporary files
        that are deleted on close. If set to a value, then downloaded files
        will be saved to this directory, and will not be automatically deleted.
        """
        self._delete_on_close = download_dir is None
        self.download_dir = download_dir

    def decode(self, response):
        base_url = response.url
        content_type = response.headers.get('content-type')
        content_disposition = response.headers.get('content-disposition')

        # Write the download to a temporary .download file.
        fd, temp_path = tempfile.mkstemp(suffix='.download')
        with os.fdopen(fd, 'wb') as file_handle:
            for chunk in response.iter_content(chunk_size=4096):
                file_handle.write(chunk)

        # Determine the output filename.
        output_filename = _get_filename(base_url, content_type, content_disposition)

        # Determine the output directory.
        output_dir = self.download_dir
        if output_dir is None:
            output_dir = os.path.dirname(temp_path)

        # Determine the full output path.
        output_path = os.path.join(output_dir, output_filename)

        # Move the temporary download file to the final location.
        if output_path != temp_path:
            output_path = _unique_output_path(output_path)
            shutil.move(temp_path, output_path)

        # Open the file and return the file object.
        output_file = open(output_path, 'rb')
        downloaded = DownloadedFile(output_file, output_path, delete=self._delete_on_close)
        downloaded.basename = output_filename
        return downloaded


def _guess_extension(content_type):
    """
    Python's `mimetypes.guess_extension` is no use because it simply returns
    the first of an unordered set. We use the same set of media types here,
    but take a reasonable preference on what extension to map to.
    """
    return {
        'application/javascript': '.js',
        'application/msword': '.doc',
        'application/octet-stream': '.bin',
        'application/oda': '.oda',
        'application/pdf': '.pdf',
        'application/pkcs7-mime': '.p7c',
        'application/postscript': '.ps',
        'application/vnd.apple.mpegurl': '.m3u',
        'application/vnd.ms-excel': '.xls',
        'application/vnd.ms-powerpoint': '.ppt',
        'application/x-bcpio': '.bcpio',
        'application/x-cpio': '.cpio',
        'application/x-csh': '.csh',
        'application/x-dvi': '.dvi',
        'application/x-gtar': '.gtar',
        'application/x-hdf': '.hdf',
        'application/x-latex': '.latex',
        'application/x-mif': '.mif',
        'application/x-netcdf': '.nc',
        'application/x-pkcs12': '.p12',
        'application/x-pn-realaudio': '.ram',
        'application/x-python-code': '.pyc',
        'application/x-sh': '.sh',
        'application/x-shar': '.shar',
        'application/x-shockwave-flash': '.swf',
        'application/x-sv4cpio': '.sv4cpio',
        'application/x-sv4crc': '.sv4crc',
        'application/x-tar': '.tar',
        'application/x-tcl': '.tcl',
        'application/x-tex': '.tex',
        'application/x-texinfo': '.texinfo',
        'application/x-troff': '.tr',
        'application/x-troff-man': '.man',
        'application/x-troff-me': '.me',
        'application/x-troff-ms': '.ms',
        'application/x-ustar': '.ustar',
        'application/x-wais-source': '.src',
        'application/xml': '.xml',
        'application/zip': '.zip',
        'audio/basic': '.au',
        'audio/mpeg': '.mp3',
        'audio/x-aiff': '.aif',
        'audio/x-pn-realaudio': '.ra',
        'audio/x-wav': '.wav',
        'image/gif': '.gif',
        'image/ief': '.ief',
        'image/jpeg': '.jpe',
        'image/png': '.png',
        'image/svg+xml': '.svg',
        'image/tiff': '.tiff',
        'image/vnd.microsoft.icon': '.ico',
        'image/x-cmu-raster': '.ras',
        'image/x-ms-bmp': '.bmp',
        'image/x-portable-anymap': '.pnm',
        'image/x-portable-bitmap': '.pbm',
        'image/x-portable-graymap': '.pgm',
        'image/x-portable-pixmap': '.ppm',
        'image/x-rgb': '.rgb',
        'image/x-xbitmap': '.xbm',
        'image/x-xpixmap': '.xpm',
        'image/x-xwindowdump': '.xwd',
        'message/rfc822': '.eml',
        'text/css': '.css',
        'text/csv': '.csv',
        'text/html': '.html',
        'text/plain': '.txt',
        'text/richtext': '.rtx',
        'text/tab-separated-values': '.tsv',
        'text/x-python': '.py',
        'text/x-setext': '.etx',
        'text/x-sgml': '.sgml',
        'text/x-vcard': '.vcf',
        'text/xml': '.xml',
        'video/mp4': '.mp4',
        'video/mpeg': '.mpeg',
        'video/quicktime': '.mov',
        'video/webm': '.webm',
        'video/x-msvideo': '.avi',
        'video/x-sgi-movie': '.movie'
    }.get(content_type, '')


def _unique_output_path(path):
    """
    Given a path like '/a/b/c.txt'

    Return the first available filename that doesn't already exist,
    using an incrementing suffix if needed.

    For example: '/a/b/c.txt' or '/a/b/c (1).txt' or '/a/b/c (2).txt'...
    """
    basename, ext = os.path.splitext(path)
    idx = 0
    while os.path.exists(path):
        idx += 1
        path = "%s (%d)%s" % (basename, idx, ext)
    return path


def _safe_filename(filename):
    """
    Sanitize output filenames, to remove any potentially unsafe characters.
    """
    filename = os.path.basename(filename)

    keepcharacters = (' ', '.', '_', '-')
    filename = ''.join(
        char for char in filename
        if char.isalnum() or char in keepcharacters
    ).strip().strip('.')

    return filename


def _get_filename_from_content_disposition(content_disposition):
    """
    Determine an output filename based on the `Content-Disposition` header.
    """
    params = value, params = cgi.parse_header(content_disposition)

    if 'filename' in params:
        filename = params['filename']
        return _safe_filename(filename)

    return None


def _get_filename_from_url(url, content_type=None):
    """
    Determine an output filename based on the download URL.
    """
    parsed = urlparse(url)
    final_path_component = posixpath.basename(parsed.path.rstrip('/'))
    filename = _safe_filename(final_path_component)
    suffix = _guess_extension(content_type or '')

    if filename:
        if '.' not in filename:
            return filename + suffix
        return filename

    return 'download' + suffix


def _get_filename(base_url, content_type=None, content_disposition=None):
    """
    Determine an output filename to use for the download.
    """
    filename = None
    if content_disposition:
        filename = _get_filename_from_content_disposition(content_disposition)
        if filename is not None:
            return filename

    return _get_filename_from_url(base_url, content_type)
