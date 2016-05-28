#!/usr/bin/env python
# -*- coding: utf8 -*-
'''
urlnorm.py - URL normalization routines

urlnorm normalizes a URL by:
  * lowercasing the scheme and hostname
  * converting the hostname to IDN format
  * taking out default port if present (e.g., http://www.foo.com:80/)
  * collapsing the path (./, ../, //, etc)
  * removing the last character in the hostname if it is '.'
  * unescaping any percent escape sequences (where possible)
  * upercase percent escape (ie: %3f => %3F)
  * converts spaces to %20
  * converts ip encoded as an integer to dotted quad notation

Available functions:
  norm - given a URL (string), returns a normalized URL
  norm_netloc
  norm_path
  unquote_path
  unquote_params
  unquote_qs
  unquote_fragment


CHANGES:
1.1.5 - Python 3 and modernization
1.1.4 - unescape " " in params, query string, and fragments
1.1.3 - don't escape " " in path
1.1.2 - leave %20 as %20, collate ' ' to %20, leave '+' as '+'
1.1 - collate %20 and ' ' to '+'
1.1 - fix unescaping of parameters
1.1 - added int2ip
1.0.1 - fix problem unescaping %23 and %20 in query string
1.0 - new release
0.94 - idna handling, unescaping querystring, fragment, add ws + wss ports
0.92 - unknown schemes now pass the port through silently
0.91 - general cleanup
     - changed dictionaries to lists where appropriate
     - more fine-grained authority parsing and normalisation
'''
from __future__ import unicode_literals

import re
try:
    from urllib.parse import urlparse, urlunparse
except ImportError:
    from urlparse import urlparse, urlunparse
try:
    from string import ascii_lowercase as lower
except ImportError:
    from string import lower


# also update in setup.py
__title__ = 'urlnorm'
__version__ = '1.1.5'
__author__ = 'Jehiah Czebotar'
__email__ = 'ehiah@gmail.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 1999-2002, 2010'
__url__ = 'https://github.com/jehiah/urlnorm'
__download_url__ = "http://github.com/downloads/jehiah/urlnorm/urlnorm-%s.tar.gz" % __version__
__shortdesc__ = 'Normalize a URL to a standard unicode encoding'


class InvalidUrl(Exception):
    pass

_collapse = re.compile('([^/]+/\.\./?|/\./|//|/\.$|/\.\.$)')
_server_authority = re.compile('^(?:([^\@]+)\@)?([^\:\[\]]+|\[[a-fA-F0-9\:\.]+\])(?:\:(.*?))?$')
_default_port = {
    'http': '80',
    'itms': '80',
    'ws': '80',
    'https': '443',
    'wss': '443',
    'gopher': '70',
    'news': '119',
    'snews': '563',
    'nntp': '119',
    'snntp': '563',
    'ftp': '21',
    'telnet': '23',
    'prospero': '191',
}
_relative_schemes = [
    'http',
    'https',
    'ws',
    'wss',
    'itms',
    'news',
    'snews',
    'nntp',
    'snntp',
    'ftp',
    'file',
    ''
]

params_unsafe_list = set('?=+%#;')
qs_unsafe_list = set('?&=+%#')
fragment_unsafe_list = set('+%#')
path_unsafe_list = set('/?;%+#')
_hextochr = dict(('%02x' % i, chr(i)) for i in range(256))
_hextochr.update(('%02X' % i, chr(i)) for i in range(256))


def unquote_path(s):
    return unquote_safe(s, path_unsafe_list)


def unquote_params(s):
    return unquote_safe(s, params_unsafe_list)


def unquote_qs(s):
    return unquote_safe(s, qs_unsafe_list)


def unquote_fragment(s):
    return unquote_safe(s, fragment_unsafe_list)


def unquote_safe(s, unsafe_list):
    '''unquote percent escaped string except for percent escape sequences that are in unsafe_list'''
    # note: this build utf8 raw strings ,then does a .decode('utf8') at the end.
    # as a result it's doing .encode('utf8') on each block of the string as it's processed.
    res = _utf8(s).split('%')
    for i in range(1, len(res)):
        item = res[i]
        try:
            raw_chr = _hextochr[item[:2]]
            if raw_chr in unsafe_list or ord(raw_chr) < 20:
                # leave it unescaped (but uppercase the percent escape)
                res[i] = '%' + item[:2].upper() + item[2:]
            else:
                res[i] = raw_chr + item[2:]
        except KeyError:
            res[i] = '%' + item
        except UnicodeDecodeError:
            # note: i'm not sure what this does
            res[i] = chr(int(item[:2], 16)) + item[2:]
    o = "".join(res)
    return _unicode(o)


def norm(url):
    '''given a string URL, return its normalized/unicode form'''
    url = _unicode(url)  # operate on unicode strings
    url_tuple = urlparse(url)
    normalized_tuple = norm_tuple(*url_tuple)
    return urlunparse(normalized_tuple)


def norm_tuple(scheme, authority, path, parameters, query, fragment):
    '''given individual url components, return its normalized form'''
    scheme = lower(scheme)
    if not scheme:
        raise InvalidUrl('missing URL scheme')
    authority = norm_netloc(scheme, authority)
    if not authority:
        raise InvalidUrl('missing netloc')
    path = norm_path(scheme, path)
    # TODO: put query in sorted order; or at least group parameters together
    # Note that some websites use positional parameters or the name part of a query so this would break the internet
    # query = urlencode(parse_qs(query, keep_blank_values=1), doseq=1)
    parameters = unquote_params(parameters)
    query = unquote_qs(query)
    fragment = unquote_fragment(fragment)
    return (scheme, authority, path, parameters, query, fragment)


def norm_path(scheme, path):
    if scheme in _relative_schemes:
        last_path = path
        while 1:
            path = _collapse.sub('/', path, 1)
            if last_path == path:
                break
            last_path = path
    path = unquote_path(path)
    if not path:
        return '/'
    return path

MAX_IP = 0xffffffff


def int2ip(ipnum):
    assert isinstance(ipnum, int)
    if MAX_IP < ipnum or ipnum < 0:
        raise TypeError("expected int between 0 and %d inclusive" % MAX_IP)
    ip1 = ipnum >> 24
    ip2 = ipnum >> 16 & 0xFF
    ip3 = ipnum >> 8 & 0xFF
    ip4 = ipnum & 0xFF
    return "%d.%d.%d.%d" % (ip1, ip2, ip3, ip4)


def norm_netloc(scheme, netloc):
    if not netloc:
        return netloc
    match = _server_authority.match(netloc)
    if not match:
        raise InvalidUrl('no host in netloc %r' % netloc)

    userinfo, host, port = match.groups()
    # catch a few common errors:
    if host.isdigit():
        try:
            host = int2ip(int(host))
        except TypeError:
            raise InvalidUrl('host %r does not escape to a valid ip' % host)
    if host[-1] == '.':
        host = host[:-1]

    # bracket check is for ipv6 hosts
    if '.' not in host and not (host[0] == '[' and host[-1] == ']'):
        raise InvalidUrl('host %r is not valid' % host)

    authority = lower(host)
    if 'xn--' in authority:
        subdomains = [_idn(subdomain) for subdomain in authority.split('.')]
        authority = '.'.join(subdomains)

    if userinfo:
        authority = "%s@%s" % (userinfo, authority)
    if port and port != _default_port.get(scheme, None):
        authority = "%s:%s" % (authority, port)
    return authority


def _idn(subdomain):
    if subdomain.startswith('xn--'):
        try:
            subdomain = subdomain.decode('idna')
        except UnicodeError:
            raise InvalidUrl('Error converting subdomain %r to IDN' % subdomain)
    return subdomain


def _utf8(value):
    value = value.encode('utf-8')
    return value


def _unicode(value):
    value = value.decode('utf-8')
    return value
