# -*- coding: utf-8 -*-
"""
Bottle is a fast and simple micro-framework for small web applications. It
offers request dispatching (Routes) with url parameter support, templates,
a built-in HTTP Server and adapters for many third party WSGI/HTTP-server and
template engines - all in a single file and with no dependencies other than the
Python Standard Library.

Homepage and documentation: http://wiki.github.com/defnull/bottle

Licence (MIT)
-------------

    Copyright (c) 2009, Marcel Hellkamp.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.


Example
-------

This is an example::

    from bottle import route, run, request, response, send_file, abort

    @route('/')
    def hello_world():
        return 'Hello World!'

    @route('/hello/:name')
    def hello_name(name):
        return 'Hello %s!' % name

    @route('/hello', method='POST')
    def hello_post():
        name = request.POST['name']
        return 'Hello %s!' % name

    @route('/static/:filename#.*#')

    def static(filename):
        return static_file(filename, root='/path/to/static/files/')

    run(host='localhost', port=8080)
"""

from __future__ import with_statement
__author__ = 'Marcel Hellkamp'
__version__ = '0.8.0'
__license__ = 'MIT'

import base64
import cgi
import email.utils
import functools
import hmac
import inspect
import itertools
import mimetypes
import os
import re
import subprocess
import sys
import thread
import threading
import time

from Cookie import SimpleCookie
from tempfile import TemporaryFile
from traceback import format_exc
from urllib import quote as urlquote
from urlparse import urlunsplit, urljoin

try:
    from collections import MutableMapping as DictMixin
except ImportError: # pragma: no cover
    from UserDict import DictMixin

try:
    from urlparse import parse_qs
except ImportError: # pragma: no cover
    from cgi import parse_qs

try:
    import cPickle as pickle
except ImportError: # pragma: no cover
    import pickle

try:
    try:
        from json import dumps as json_dumps
    except ImportError: # pragma: no cover
        from simplejson import dumps as json_dumps
except ImportError: # pragma: no cover
    json_dumps = None

if sys.version_info >= (3,0,0): # pragma: no cover
    # See Request.POST
    from io import BytesIO
    from io import TextIOWrapper
    StringType = bytes
    def touni(x, enc='utf8'): # Convert anything to unicode (py3)
        return str(x, encoding=enc) if isinstance(x, bytes) else str(x)
else:
    from StringIO import StringIO as BytesIO
    from types import StringType
    TextIOWrapper = None
    def touni(x, enc='utf8'): # Convert anything to unicode (py2)
        return x if isinstance(x, unicode) else unicode(str(x), encoding=enc)

def tob(data, enc='utf8'): # Convert strings to bytes (py2 and py3)
    return data.encode(enc) if isinstance(data, unicode) else data






# Exceptions and Events

class BottleException(Exception):
    """ A base class for exceptions used by bottle. """
    pass


class HTTPResponse(BottleException):
    """ Used to break execution and imediately finish the response """
    def __init__(self, output='', status=200, header=None):
        super(BottleException, self).__init__("HTTP Response %d" % status)
        self.status = int(status)
        self.output = output
        self.headers = HeaderDict(header) if header else None

    def apply(self, response):
        if self.headers:
            for key, value in self.headers.iterallitems():
                response.headers[key] = value
        response.status = self.status


class HTTPError(HTTPResponse):
    """ Used to generate an error page """
    def __init__(self, code=500, output='Unknown Error', exception=None, traceback=None, header=None):
        super(HTTPError, self).__init__(output, code, header)
        self.exception = exception
        self.traceback = traceback

    def __repr__(self):
        return ''.join(ERROR_PAGE_TEMPLATE.render(e=self, DEBUG=DEBUG, HTTP_CODES=HTTP_CODES, request=request))






# Routing

class RouteError(BottleException):
    """ This is a base class for all routing related exceptions """


class RouteSyntaxError(RouteError):
    """ The route parser found something not supported by this router """


class RouteBuildError(RouteError):
    """ The route could not been build """


class Route(object):
    ''' Represents a single route and can parse the dynamic route syntax '''
    syntax = re.compile(r'(.*?)(?<!\\):([a-zA-Z_]+)?(?:#(.*?)#)?')
    default = '[^/]+'

    def __init__(self, route, target, name=None, static=False):
        """ Create a Route. The route string may contain `:key`,
            `:key#regexp#` or `:#regexp#` tokens for each dynamic part of the
            route. These can be escaped with a backslash infront of the `:`
            and are compleately ignored if static is true. A name may be used
            to refer to this route later (depends on Router)
        """
        self.route = route
        self.target = target
        self.name = name
        self._static = static
        self._tokens = None

    def tokens(self):
        """ Return a list of (type, value) tokens. """
        if not self._tokens:
            self._tokens = list(self.tokenise(self.route))
        return self._tokens

    @classmethod
    def tokenise(cls, route):
        ''' Split a string into an iterator of (type, value) tokens. '''
        match = None
        for match in cls.syntax.finditer(route):
            pre, name, rex = match.groups()
            if pre: yield ('TXT', pre.replace('\\:',':'))
            if rex and name: yield ('VAR', (rex, name))
            elif name: yield ('VAR', (cls.default, name))
            elif rex: yield ('ANON', rex)
        if not match:
            yield ('TXT', route.replace('\\:',':'))
        elif match.end() < len(route):
            yield ('TXT', route[match.end():].replace('\\:',':'))

    def group_re(self):
        ''' Return a regexp pattern with named groups '''
        out = ''
        for token, data in self.tokens():
            if   token == 'TXT':  out += re.escape(data)
            elif token == 'VAR':  out += '(?P<%s>%s)' % (data[1], data[0])
            elif token == 'ANON': out += '(?:%s)' % data
        return out

    def flat_re(self):
        ''' Return a regexp pattern with non-grouping parentheses '''
        return re.sub(r'\(\?P<[^>]*>|\((?!\?)', '(?:', self.group_re())

    def format_str(self):
        ''' Return a format string with named fields. '''
        if self.static:
            return self.route.replace('%','%%')
        out, i = '', 0
        for token, value in self.tokens():
            if token == 'TXT': out += value.replace('%','%%')
            elif token == 'ANON': out += '%%(anon%d)s' % i; i+=1
            elif token == 'VAR': out += '%%(%s)s' % value[1]
        return out

    @property
    def static(self):
        return not self.is_dynamic()

    def is_dynamic(self):
        ''' Return true if the route contains dynamic parts '''
        if not self._static:
            for token, value in self.tokens():
                if token != 'TXT':
                    return True
        self._static = True
        return False

    def __repr__(self):
        return self.route

    def __eq__(self, other):
        return self.route == other.route\
           and self.static == other.static\
           and self.name == other.name\
           and self.target == other.target


class Router(object):
    ''' A route associates a string (e.g. URL) with an object (e.g. function)
        Some dynamic routes may extract parts of the string and provide them as
        a dictionary. This router matches a string against multiple routes and
        returns the associated object along with the extracted data.
    '''

    def __init__(self):
        self.routes = []     # List of all installed routes
        self.static = dict() # Cache for static routes
        self.dynamic = []    # Cache structure for dynamic routes
        self.named = dict()  # Cache for named routes and their format strings

    def add(self, *a, **ka):
        """ Adds a route->target pair or a Route object to the Router.
            See Route() for details.
        """
        route = a[0] if a and isinstance(a[0], Route) else Route(*a, **ka)
        self.routes.append(route)
        if route.name:
            self.named[route.name] = route.format_str()
        if route.static:
            self.static[route.route] = route.target
            return
        gpatt = route.group_re()
        fpatt = route.flat_re()
        try:
            gregexp = re.compile('^(%s)$' % gpatt) if '(?P' in gpatt else None
            combined = '%s|(^%s$)' % (self.dynamic[-1][0].pattern, fpatt)
            self.dynamic[-1] = (re.compile(combined), self.dynamic[-1][1])
            self.dynamic[-1][1].append((route.target, gregexp))
        except (AssertionError, IndexError), e: # AssertionError: Too many groups
            self.dynamic.append((re.compile('(^%s$)'%fpatt),[(route.target, gregexp)]))
        except re.error, e:
            raise RouteSyntaxError("Could not add Route: %s (%s)" % (route, e))

    def match(self, uri):
        ''' Matches an URL and returns a (handler, target) tuple '''
        if uri in self.static:
            return self.static[uri], {}
        for combined, subroutes in self.dynamic:
            match = combined.match(uri)
            if not match: continue
            target, groups = subroutes[match.lastindex - 1]
            groups = groups.match(uri).groupdict() if groups else {}
            return target, groups
        return None, {}

    def build(self, route_name, **args):
        ''' Builds an URL out of a named route and some parameters.'''
        try:
            return self.named[route_name] % args
        except KeyError:
            raise RouteBuildError("No route found with name '%s'." % route_name)

    def __eq__(self, other):
        return self.routes == other.routes






# WSGI abstraction: Application, Request and Response objects

class Bottle(object):
    """ WSGI application """

    def __init__(self, catchall=True, autojson=True, path = ''):
        """ Create a new bottle instance.
            You usually don't do that. Use `bottle.app.push()` instead.
        """
        self.routes = Router()
        self.mounts = {}
        self.error_handler = {}
        self.catchall = catchall
        self.config = dict()
        self.serve = True
        self.castfilter = []
        if autojson and json_dumps:
            self.add_filter(dict, dict2json)

    def mount(self, app, script_path):
        ''' Mount a Bottle application to a specific URL prefix '''
        if not isinstance(app, Bottle):
            raise TypeError('Only Bottle instances are supported for now.')
        script_path = '/'.join(filter(None, script_path.split('/')))
        path_depth = script_path.count('/') + 1
        if not script_path:
            raise TypeError('Empty script_path. Perhaps you want a merge()?')
        for other in self.mounts:
            if other.startswith(script_path):
                raise TypeError('Conflict with existing mount: %s' % other)
        @self.route('/%s/:#.*#' % script_path, method="ANY")
        def mountpoint():
            request.path_shift(path_depth)
            return app.handle(request.path, request.method)
        self.mounts[script_path] = app

    def add_filter(self, ftype, func):
        ''' Register a new output filter. Whenever bottle hits a handler output
            matching `ftype`, `func` is applyed to it. '''
        if not isinstance(ftype, type):
            raise TypeError("Expected type object, got %s" % type(ftype))
        self.castfilter = [(t, f) for (t, f) in self.castfilter if t != ftype]
        self.castfilter.append((ftype, func))
        self.castfilter.sort()

    def match_url(self, path, method='GET'):
        """ Find a callback bound to a path and a specific HTTP method.
            Return (callback, param) tuple or (None, {}).
            method: HEAD falls back to GET. HEAD and GET fall back to ALL.
        """
        path = path.strip().lstrip('/')
        handler, param = self.routes.match(method + ';' + path)
        if handler: return handler, param
        if method == 'HEAD':
            handler, param = self.routes.match('GET;' + path)
            if handler: return handler, param
        handler, param = self.routes.match('ANY;' + path)
        if handler: return handler, param
        return None, {}

    def get_url(self, routename, **kargs):
        """ Return a string that matches a named route """
        return '/' + self.routes.build(routename, **kargs).split(';', 1)[1]

    def route(self, path=None, method='GET', **kargs):
        """ Decorator: Bind a function to a GET request path.

            If the path parameter is None, the signature of the decorated
            function is used to generate the path. See yieldroutes()
            for details.

            The method parameter (default: GET) specifies the HTTP request
            method to listen to. You can specify a list of methods.
        """
        if isinstance(method, str): #TODO: Test this
            method = method.split(';')
        def wrapper(callback):
            paths = [] if path is None else [path.strip().lstrip('/')]
            if not paths: # Lets generate the path automatically
                paths = yieldroutes(callback)
            for p in paths:
                for m in method:
                    route = m.upper() + ';' + p
                    self.routes.add(route, callback, **kargs)
            return callback
        return wrapper

    def error(self, code=500):
        """ Decorator: Registrer an output handler for a HTTP error code"""
        def wrapper(handler):
            self.error_handler[int(code)] = handler
            return handler
        return wrapper

    def handle(self, url, method):
        """ Execute the handler bound to the specified url and method and return
        its output. If catchall is true, exceptions are catched and returned as
        HTTPError(500) objects. """
        if not self.serve:
            return HTTPError(503, "Server stopped")

        handler, args = self.match_url(url, method)
        if not handler:
            return HTTPError(404, "Not found:" + url)

        try:
            return handler(**args)
        except HTTPResponse, e:
            return e
        except Exception, e:
            if isinstance(e, (KeyboardInterrupt, SystemExit, MemoryError))\
            or not self.catchall:
                raise
            return HTTPError(500, 'Unhandled exception', e, format_exc(10))

    def _cast(self, out, request, response, peek=None):
        """ Try to convert the parameter into something WSGI compatible and set
        correct HTTP headers when possible.
        Support: False, str, unicode, dict, HTTPResponse, HTTPError, file-like,
        iterable of strings and iterable of unicodes
        """
        # Filtered types (recursive, because they may return anything)
        for testtype, filterfunc in self.castfilter:
            if isinstance(out, testtype):
                return self._cast(filterfunc(out), request, response)

        # Empty output is done here
        if not out:
            response.headers['Content-Length'] = 0
            return []
        # Join lists of byte or unicode strings. Mixed lists are NOT supported
        if isinstance(out, list) and isinstance(out[0], (StringType, unicode)):
            out = out[0][0:0].join(out) # b'abc'[0:0] -> b''
        # Encode unicode strings
        if isinstance(out, unicode):
            out = out.encode(response.charset)
        # Byte Strings are just returned
        if isinstance(out, StringType):
            response.headers['Content-Length'] = str(len(out))
            return [out]
        # HTTPError or HTTPException (recursive, because they may wrap anything)
        if isinstance(out, HTTPError):
            out.apply(response)
            return self._cast(self.error_handler.get(out.status, repr)(out), request, response)
        if isinstance(out, HTTPResponse):
            out.apply(response)
            return self._cast(out.output, request, response)

        # Cast Files into iterables
        if hasattr(out, 'read') and 'wsgi.file_wrapper' in request.environ:
            out = request.environ.get('wsgi.file_wrapper',
            lambda x, y: iter(lambda: x.read(y), ''))(out, 1024*64)

        # Handle Iterables. We peek into them to detect their inner type.
        try:
            out = iter(out)
            first = out.next()
            while not first:
                first = out.next()
        except StopIteration:
            return self._cast('', request, response)
        except HTTPResponse, e:
            first = e
        except Exception, e:
            first = HTTPError(500, 'Unhandled exception', e, format_exc(10))
            if isinstance(e, (KeyboardInterrupt, SystemExit, MemoryError))\
            or not self.catchall:
                raise
        # These are the inner types allowed in iterator or generator objects.
        if isinstance(first, HTTPResponse):
            return self._cast(first, request, response)
        if isinstance(first, StringType):
            return itertools.chain([first], out)
        if isinstance(first, unicode):
            return itertools.imap(lambda x: x.encode(response.charset),
                                  itertools.chain([first], out))
        return self._cast(HTTPError(500, 'Unsupported response type: %s'\
                                         % type(first)), request, response)

    def __call__(self, environ, start_response):
        """ The bottle WSGI-interface. """
        try:
            request.bind(environ, self)
            response.bind(self)
            out = self.handle(request.path, request.method)
            out = self._cast(out, request, response)
            if response.status in (100, 101, 204, 304) or request.method == 'HEAD':
                out = [] # rfc2616 section 4.3
            status = '%d %s' % (response.status, HTTP_CODES[response.status])
            start_response(status, response.headerlist)
            return out
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception, e:
            if not self.catchall:
                raise
            err = '<h1>Critical error while processing request: %s</h1>' \
                  % environ.get('PATH_INFO', '/')
            if DEBUG:
                err += '<h2>Error:</h2>\n<pre>%s</pre>\n' % repr(e)
                err += '<h2>Traceback:</h2>\n<pre>%s</pre>\n' % format_exc(10)
            environ['wsgi.errors'].write(err) #TODO: wsgi.error should not get html
            start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/html')])
            return [tob(err)]


class Request(threading.local, DictMixin):
    """ Represents a single HTTP request using thread-local attributes.
        The Resquest object wrapps a WSGI environment and can be used as such.
    """
    def __init__(self, environ=None, app=None):
        """ Create a new Request instance.

            You usually don't do this but use the global `bottle.request`
            instance instead.
         """
        self.bind(environ or {}, app)

    def bind(self, environ, app=None):
        """ Bind a new WSGI enviroment and clear out all previously computed
            attributes.

            This is done automatically for the global `bottle.request`
            instance on every request.
        """
        if isinstance(environ, Request): # Recycle already parsed content
            for key in self.__dict__: #TODO: Test this
                setattr(self, key, getattr(environ, key))
            self.app = app
            return
        self._GET = self._POST = self._GETPOST = self._COOKIES = None
        self._body = self._header = None
        self.environ = environ
        self.app = app
        # These attributes are used anyway, so it is ok to compute them here
        self.path = '/' + environ.get('PATH_INFO', '/').lstrip('/')
        self.method = environ.get('REQUEST_METHOD', 'GET').upper()

    def copy(self):
        ''' Returns a copy of self '''
        return Request(self.environ.copy(), self.app)

    def path_shift(self, count=1):
        ''' Shift some levels of PATH_INFO into SCRIPT_NAME and return the
            moved part. count defaults to 1'''
        #/a/b/  /c/d  --> 'a','b'  'c','d'
        if count == 0: return ''
        pathlist = self.path.strip('/').split('/')
        scriptlist = self.environ.get('SCRIPT_NAME','/').strip('/').split('/')
        if pathlist and pathlist[0] == '': pathlist = []
        if scriptlist and scriptlist[0] == '': scriptlist = []
        if count > 0 and count <= len(pathlist):
            moved = pathlist[:count]
            scriptlist = scriptlist + moved
            pathlist = pathlist[count:]
        elif count < 0 and count >= -len(scriptlist):
            moved = scriptlist[count:]
            pathlist = moved + pathlist
            scriptlist = scriptlist[:count]
        else:
            empty = 'SCRIPT_NAME' if count < 0 else 'PATH_INFO'
            raise AssertionError("Cannot shift. Nothing left from %s" % empty)
        self['PATH_INFO'] = self.path =  '/' + '/'.join(pathlist) \
                          + ('/' if self.path.endswith('/') and pathlist else '')
        self['SCRIPT_NAME'] = '/' + '/'.join(scriptlist)
        return '/'.join(moved)

    def __getitem__(self, key):
        """ Shortcut for Request.environ.__getitem__ """
        return self.environ[key]

    def __setitem__(self, key, value):
        """ Shortcut for Request.environ.__setitem__ """
        self.environ[key] = value

    def keys(self):
        """ Shortcut for Request.environ.keys() """
        return self.environ.keys()

    @property
    def query_string(self):
        """ The content of the QUERY_STRING environment variable. """
        return self.environ.get('QUERY_STRING', '')

    @property
    def fullpath(self):
        """ Request path including SCRIPT_NAME (if present) """
        return self.environ.get('SCRIPT_NAME', '').rstrip('/') + self.path

    @property
    def url(self):
        """ Full URL as requested by the client (computed).

            This value is constructed out of different environment variables
            and includes scheme, host, port, scriptname, path and query string.
        """
        scheme = self.environ.get('wsgi.url_scheme', 'http')
        host   = self.environ.get('HTTP_X_FORWARDED_HOST', self.environ.get('HTTP_HOST', None))
        if not host:
            host = self.environ.get('SERVER_NAME')
            port = self.environ.get('SERVER_PORT', '80')
            if scheme + port not in ('https443', 'http80'):
                host += ':' + port
        parts = (scheme, host, urlquote(self.fullpath), self.query_string, '')
        return urlunsplit(parts)

    @property
    def content_length(self):
        """ Content-Length header as an integer, -1 if not specified """
        return int(self.environ.get('CONTENT_LENGTH','') or -1)

    @property
    def header(self):
        ''' :class:`HeaderDict` filled with request headers.

            HeaderDict keys are case insensitive str.title()d
        '''
        if self._header is None:
            self._header = HeaderDict()
            for key, value in self.environ.iteritems():
                if key.startswith('HTTP_'):
                    key = key[5:].replace('_','-').title()
                    self._header[key] = value
        return self._header

    @property
    def GET(self):
        """ The QUERY_STRING parsed into a MultiDict.

            Keys and values are strings. Multiple values per key are possible.
            See MultiDict for details.
        """
        if self._GET is None:
            data = parse_qs(self.query_string, keep_blank_values=True)
            self._GET = MultiDict()
            for key, values in data.iteritems():
                for value in values:
                    self._GET[key] = value
        return self._GET

    @property
    def POST(self):
        """ The HTTP POST body parsed into a MultiDict.

            This supports urlencoded and multipart POST requests. Multipart
            is commonly used for file uploads and may result in some of the
            values beeing cgi.FieldStorage objects instead of strings.

            Multiple values per key are possible. See MultiDict for details.
        """
        if self._POST is None:
            save_env = dict() # Build a save environment for cgi
            for key in ('REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
                if key in self.environ:
                    save_env[key] = self.environ[key]
            save_env['QUERY_STRING'] = '' # Without this, sys.argv is called!
            if TextIOWrapper:
                fb = TextIOWrapper(self.body, encoding='ISO-8859-1')
            else:
                fb = self.body
            data = cgi.FieldStorage(fp=fb, environ=save_env)
            self._POST = MultiDict()
            for item in data.list:
                self._POST[item.name] = item if item.filename else item.value
        return self._POST

    @property
    def params(self):
        """ A combined MultiDict with POST and GET parameters. """
        if self._GETPOST is None:
            self._GETPOST = MultiDict(self.GET)
            self._GETPOST.update(dict(self.POST))
        return self._GETPOST

    @property
    def body(self):
        """ The HTTP request body as a seekable buffer object.

            This property returns a copy of the `wsgi.input` stream and should
            be used instead of `environ['wsgi.input']`.
         """
        if self._body is None:
            maxread = max(0, self.content_length)
            stream = self.environ['wsgi.input']
            self._body = BytesIO() if maxread < MEMFILE_MAX else TemporaryFile(mode='w+b')
            while maxread > 0:
                part = stream.read(min(maxread, MEMFILE_MAX))
                if not part: #TODO: Wrong content_length. Error? Do nothing?
                    break
                self._body.write(part)
                maxread -= len(part)
            self.environ['wsgi.input'] = self._body
        self._body.seek(0)
        return self._body

    @property
    def auth(self): #TODO: Tests and docs. Add support for digest. namedtuple?
        """ HTTP authorisation data as a (user, passwd) tuple. (experimental)

            This implementation currently only supports basic auth and returns
            None on errors.
        """
        return parse_auth(self.environ.get('HTTP_AUTHORIZATION'))

    @property
    def COOKIES(self):
        """ Cookie information parsed into a dictionary.

            Secure cookies are NOT decoded automatically. See
            Request.get_cookie() for details.
        """
        if self._COOKIES is None:
            raw_dict = SimpleCookie(self.environ.get('HTTP_COOKIE',''))
            self._COOKIES = {}
            for cookie in raw_dict.itervalues():
                self._COOKIES[cookie.key] = cookie.value
        return self._COOKIES

    def get_cookie(self, *args):
        """ Return the (decoded) value of a cookie. """
        value = self.COOKIES.get(*args)
        sec = self.app.config['securecookie.key']
        dec = cookie_decode(value, sec)
        return dec or value


class Response(threading.local):
    """ Represents a single HTTP response using thread-local attributes.
    """

    def __init__(self, app=None):
        self.bind(app)

    def bind(self, app):
        """ Resets the Response object to its factory defaults. """
        self._COOKIES = None
        self.status = 200
        self.headers = HeaderDict()
        self.content_type = 'text/html; charset=UTF-8'
        self.app = app

    def copy(self):
        ''' Returns a copy of self '''
        copy = Response(self.app)
        copy.status = self.status
        copy.headers = self.headers.copy()
        copy.content_type = self.content_type
        return copy

    def wsgiheader(self):
        ''' Returns a wsgi conform list of header/value pairs. '''
        for c in self.COOKIES.values():
            if c.OutputString() not in self.headers.getall('Set-Cookie'):
                self.headers.append('Set-Cookie', c.OutputString())
        return list(self.headers.iterallitems())
    headerlist = property(wsgiheader)

    @property
    def charset(self):
        """ Return the charset specified in the content-type header.

            This defaults to `UTF-8`.
        """
        if 'charset=' in self.content_type:
            return self.content_type.split('charset=')[-1].split(';')[0].strip()
        return 'UTF-8'

    @property
    def COOKIES(self):
        """ A dict-like SimpleCookie instance. Use Response.set_cookie() instead. """
        if not self._COOKIES:
            self._COOKIES = SimpleCookie()
        return self._COOKIES

    def set_cookie(self, key, value, **kargs):
        """ Add a new cookie with various options.

        If the cookie value is not a string, a secure cookie is created.

        Possible options are:
            expires, path, comment, domain, max_age, secure, version, httponly
            See http://de.wikipedia.org/wiki/HTTP-Cookie#Aufbau for details
        """
        if not isinstance(value, basestring):
            sec = self.app.config['securecookie.key']
            value = cookie_encode(value, sec).decode('ascii') #2to3 hack
        self.COOKIES[key] = value
        for k, v in kargs.iteritems():
            self.COOKIES[key][k.replace('_', '-')] = v

    def get_content_type(self):
        """ Current 'Content-Type' header. """
        return self.headers['Content-Type']

    def set_content_type(self, value):
        self.headers['Content-Type'] = value

    content_type = property(get_content_type, set_content_type, None,
                            get_content_type.__doc__)






# Data Structures

class MultiDict(DictMixin):
    """ A dict that remembers old values for each key """
    # collections.MutableMapping would be better for Python >= 2.6
    def __init__(self, *a, **k):
        self.dict = dict()
        for k, v in dict(*a, **k).iteritems():
            self[k] = v

    def __len__(self): return len(self.dict)
    def __iter__(self): return iter(self.dict)
    def __contains__(self, key): return key in self.dict
    def __delitem__(self, key): del self.dict[key]
    def keys(self): return self.dict.keys()
    def __getitem__(self, key): return self.get(key, KeyError, -1)
    def __setitem__(self, key, value): self.append(key, value)

    def append(self, key, value): self.dict.setdefault(key, []).append(value)
    def replace(self, key, value): self.dict[key] = [value]
    def getall(self, key): return self.dict.get(key) or []

    def get(self, key, default=None, index=-1):
        if key not in self.dict and default != KeyError:
            return [default][index]
        return self.dict[key][index]

    def iterallitems(self):
        for key, values in self.dict.iteritems():
            for value in values:
                yield key, value


class HeaderDict(MultiDict):
    """ Same as :class:`MultiDict`, but title()s the keys and overwrites by default. """
    def __contains__(self, key): return MultiDict.__contains__(self, self.httpkey(key))
    def __getitem__(self, key): return MultiDict.__getitem__(self, self.httpkey(key))
    def __delitem__(self, key): return MultiDict.__delitem__(self, self.httpkey(key))
    def __setitem__(self, key, value): self.replace(key, value)
    def append(self, key, value): return MultiDict.append(self, self.httpkey(key), str(value))
    def replace(self, key, value): return MultiDict.replace(self, self.httpkey(key), str(value))
    def getall(self, key): return MultiDict.getall(self, self.httpkey(key))
    def httpkey(self, key): return str(key).replace('_','-').title()


class AppStack(list):
    """ A stack implementation. """

    def __call__(self):
        """ Return the current default app. """
        return self[-1]

    def push(self, value=None):
        """ Add a new Bottle instance to the stack """
        if not isinstance(value, Bottle):
            value = Bottle()
        self.append(value)
        return value




# Module level functions

# Output filter

def dict2json(d):
    response.content_type = 'application/json'
    return json_dumps(d)


def abort(code=500, text='Unknown Error: Appliction stopped.'):
    """ Aborts execution and causes a HTTP error. """
    raise HTTPError(code, text)


def redirect(url, code=303):
    """ Aborts execution and causes a 303 redirect """
    scriptname = request.environ.get('SCRIPT_NAME', '').rstrip('/') + '/'
    location = urljoin(request.url, urljoin(scriptname, url))
    raise HTTPResponse("", status=code, header=dict(Location=location))


def send_file(*a, **k): #BC 0.6.4
    """ Raises the output of static_file() """
    raise static_file(*a, **k)


def static_file(filename, root, guessmime=True, mimetype=None, download=False):
    """ Opens a file in a save way and returns a HTTPError object with status
        code 200, 305, 401 or 404. Sets Content-Type, Content-Length and
        Last-Modified header. Obeys If-Modified-Since header and HEAD requests.
    """
    root = os.path.abspath(root) + os.sep
    filename = os.path.abspath(os.path.join(root, filename.strip('/\\')))
    header = dict()

    if not filename.startswith(root):
        return HTTPError(401, "Access denied.")
    if not os.path.exists(filename) or not os.path.isfile(filename):
        return HTTPError(404, "File does not exist.")
    if not os.access(filename, os.R_OK):
        return HTTPError(401, "You do not have permission to access this file.")

    if not mimetype and guessmime:
        header['Content-Type'] = mimetypes.guess_type(filename)[0]
    else:
        header['Content-Type'] = mimetype if mimetype else 'text/plain'

    if download == True:
        download = os.path.basename(filename)
    if download:
        header['Content-Disposition'] = 'attachment; filename="%s"' % download

    stats = os.stat(filename)
    lm = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stats.st_mtime))
    header['Last-Modified'] = lm
    ims = request.environ.get('HTTP_IF_MODIFIED_SINCE')
    if ims:
        ims = ims.split(";")[0].strip() # IE sends "<date>; length=146"
        ims = parse_date(ims)
        if ims is not None and ims >= int(stats.st_mtime):
           return HTTPResponse(status=304, header=header)
    header['Content-Length'] = stats.st_size
    if request.method == 'HEAD':
        return HTTPResponse('', header=header)
    else:
        return HTTPResponse(open(filename, 'rb'), header=header)

def url(routename, **kargs):
    return app().get_url(routename, **kargs)
url.__doc__ = Bottle.get_url.__doc__

def mount(app, script_path):
    return app().mount(app, script_path)
mount.__doc__ = Bottle.mount.__doc__

# Utilities

def debug(mode=True):
    """ Change the debug level.
    There is only one debug level supported at the moment."""
    global DEBUG
    DEBUG = bool(mode)


def parse_date(ims):
    """ Parse rfc1123, rfc850 and asctime timestamps and return UTC epoch. """
    try:
        ts = email.utils.parsedate_tz(ims)
        return time.mktime(ts[:8] + (0,)) - (ts[9] or 0) - time.timezone
    except (TypeError, ValueError, IndexError):
        return None


def parse_auth(header):
    """ Parse rfc2617 HTTP authentication header string (basic) and return (user,pass) tuple or None"""
    try:
        method, data = header.split(None, 1)
        if method.lower() == 'basic':
            name, pwd = base64.b64decode(data).split(':', 1)
            return name, pwd
    except (KeyError, ValueError, TypeError):
        return None


def cookie_encode(data, key):
    ''' Encode and sign a pickle-able object. Return a string '''
    msg = base64.b64encode(pickle.dumps(data, -1))
    sig = base64.b64encode(hmac.new(key, msg).digest())
    return u'!'.encode('ascii') + sig + u'?'.encode('ascii') + msg #2to3 hack


def cookie_decode(data, key):
    ''' Verify and decode an encoded string. Return an object or None'''
    if isinstance(data, unicode): data = data.encode('ascii') #2to3 hack
    if cookie_is_encoded(data):
        sig, msg = data.split(u'?'.encode('ascii'),1) #2to3 hack
        if sig[1:] == base64.b64encode(hmac.new(key, msg).digest()):
           return pickle.loads(base64.b64decode(msg))
    return None


def cookie_is_encoded(data):
    ''' Verify and decode an encoded string. Return an object or None'''
    return bool(data.startswith(u'!'.encode('ascii')) and u'?'.encode('ascii') in data) #2to3 hack


def tonativefunc(enc='utf-8'):
    ''' Returns a function that turns everything into 'native' strings using enc '''
    if sys.version_info >= (3,0,0):
        return lambda x: x.decode(enc) if isinstance(x, bytes) else str(x)
    return lambda x: x.encode(enc) if isinstance(x, unicode) else str(x)


def yieldroutes(func):
    """ Return a generator for routes that match the signature (name, args)
    of the func parameter. This may yield more than one route if the function
    takes optional keyword arguments. The output is best described by example:
      a()         -> '/a'
      b(x, y)     -> '/b/:x/:y'
      c(x, y=5)   -> '/c/:x' and '/c/:x/:y'
      d(x=5, y=6) -> '/d' and '/d/:x' and '/d/:x/:y'
    """
    path = func.__name__.replace('__','/').lstrip('/')
    spec = inspect.getargspec(func)
    argc = len(spec[0]) - len(spec[3] or [])
    path += ('/:%s' * argc) % tuple(spec[0][:argc])
    yield path
    for arg in spec[0][argc:]:
        path += '/:%s' % arg
        yield path






# Decorators
#TODO: Replace default_app() with app()

def validate(**vkargs):
    """
    Validates and manipulates keyword arguments by user defined callables.
    Handles ValueError and missing arguments by raising HTTPError(403).
    """
    def decorator(func):
        def wrapper(**kargs):
            for key, value in vkargs.iteritems():
                if key not in kargs:
                    abort(403, 'Missing parameter: %s' % key)
                try:
                    kargs[key] = value(kargs[key])
                except ValueError:
                    abort(403, 'Wrong parameter format for: %s' % key)
            return func(**kargs)
        return wrapper
    return decorator


def route(*a, **ka):
    """ Decorator: Bind a route to a callback.
        The method parameter (default: GET) specifies the HTTP request
        method to listen to """
    return app().route(*a, **ka)

get = functools.partial(route, method='GET')
get.__doc__ = route.__doc__

post = functools.partial(route, method='POST')
post.__doc__ = route.__doc__.replace('GET','POST')

put = functools.partial(route, method='PUT')
put.__doc__ = route.__doc__.replace('GET','PUT')

delete = functools.partial(route, method='DELETE')
delete.__doc__ = route.__doc__.replace('GET','DELETE')

def default():
    raise DeprecationWarning("Use @error(404) instead.")

def error(code=500):
    """
    Decorator for error handler. Same as app().error(code, handler).
    """
    return app().error(code)






# Server adapter

class ServerAdapter(object):
    def __init__(self, host='127.0.0.1', port=8080, **kargs):
        self.options = kargs
        self.host = host
        self.port = int(port)

    def run(self, handler): # pragma: no cover
        pass

    def __repr__(self):
        args = ', '.join(['%s=%s'%(k,repr(v)) for k, v in self.options.items()])
        return "%s(%s)" % (self.__class__.__name__, args)


class CGIServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
        from wsgiref.handlers import CGIHandler
        CGIHandler().run(handler) # Just ignore host and port here


class FlupFCGIServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
       import flup.server.fcgi
       flup.server.fcgi.WSGIServer(handler, bindAddress=(self.host, self.port)).run()


class WSGIRefServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
        from wsgiref.simple_server import make_server
        srv = make_server(self.host, self.port, handler)
        srv.serve_forever()


class CherryPyServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
        from cherrypy import wsgiserver
        server = wsgiserver.CherryPyWSGIServer((self.host, self.port), handler)
        server.start()


class PasteServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
        from paste import httpserver
        from paste.translogger import TransLogger
        app = TransLogger(handler)
        httpserver.serve(app, host=self.host, port=str(self.port), **self.options)


class FapwsServer(ServerAdapter):
    """
    Extremly fast webserver using libev.
    See http://william-os4y.livejournal.com/
    """
    def run(self, handler): # pragma: no cover
        import fapws._evwsgi as evwsgi
        from fapws import base
        evwsgi.start(self.host, self.port)
        evwsgi.set_base_module(base)
        def app(environ, start_response):
            environ['wsgi.multiprocess'] = False
            return handler(environ, start_response)
        evwsgi.wsgi_cb(('',app))
        evwsgi.run()


class TornadoServer(ServerAdapter):
    """ Untested. As described here:
        http://github.com/facebook/tornado/blob/master/tornado/wsgi.py#L187 """
    def run(self, handler): # pragma: no cover
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop
        container = tornado.wsgi.WSGIContainer(handler)
        server = tornado.httpserver.HTTPServer(container)
        server.listen(port=self.port)
        tornado.ioloop.IOLoop.instance().start()


class AppEngineServer(ServerAdapter):
    """ Untested. """
    def run(self, handler):
        from google.appengine.ext.webapp import util
        util.run_wsgi_app(handler)


class TwistedServer(ServerAdapter):
    """ Untested. """
    def run(self, handler):
        from twisted.web import server, wsgi
        from twisted.python.threadpool import ThreadPool
        from twisted.internet import reactor
        thread_pool = ThreadPool()
        thread_pool.start()
        reactor.addSystemEventTrigger('after', 'shutdown', thread_pool.stop)
        factory = server.Site(wsgi.WSGIResource(reactor, thread_pool, handler))
        reactor.listenTCP(self.port, factory, interface=self.host)
        reactor.run()


class DieselServer(ServerAdapter):
    """ Untested. """
    def run(self, handler):
        from diesel.protocols.wsgi import WSGIApplication
        app = WSGIApplication(handler, port=self.port)
        app.run()


class GunicornServer(ServerAdapter):
    """ Untested. """
    def run(self, handler):
        import gunicorn.arbiter
        gunicorn.arbiter.Arbiter((self.host, self.port), 4, handler).run()


class AutoServer(ServerAdapter):
    """ Untested. """
    adapters = [CherryPyServer, PasteServer, TwistedServer, WSGIRefServer]
    def run(self, handler):
        for sa in self.adapters:
            try:
                return sa(self.host, self.port, **self.options).run(handler)
            except ImportError:
                pass


def run(app=None, server=WSGIRefServer, host='127.0.0.1', port=8080,
        interval=1, reloader=False, **kargs):
    """ Runs bottle as a web server. """
    app = app if app else default_app()
    quiet = bool(kargs.get('quiet', False))
    # Instantiate server, if it is a class instead of an instance
    if isinstance(server, type):
        server = server(host=host, port=port, **kargs)
    if not isinstance(server, ServerAdapter):
        raise RuntimeError("Server must be a subclass of WSGIAdapter")
    if not quiet and isinstance(server, ServerAdapter): # pragma: no cover
        if not reloader or os.environ.get('BOTTLE_CHILD') == 'true':
            print "Bottle server starting up (using %s)..." % repr(server)
            print "Listening on http://%s:%d/" % (server.host, server.port)
            print "Use Ctrl-C to quit."
            print
        else:
            print "Bottle auto reloader starting up..."
    try:
        if reloader and interval:
            reloader_run(server, app, interval)
        else:
            server.run(app)
    except KeyboardInterrupt:
        if not quiet: # pragma: no cover
            print "Shutting Down..."


#TODO: If the parent process is killed (with SIGTERM) the childs survive...
def reloader_run(server, app, interval):
    if os.environ.get('BOTTLE_CHILD') == 'true':
        # We are a child process
        files = dict()
        for module in sys.modules.values():
            file_path = getattr(module, '__file__', None)
            if file_path and os.path.isfile(file_path):
                file_split = os.path.splitext(file_path)
                if file_split[1] in ('.py', '.pyc', '.pyo'):
                    file_path = file_split[0] + '.py'
                    files[file_path] = os.stat(file_path).st_mtime
        thread.start_new_thread(server.run, (app,))
        while True:
            time.sleep(interval)
            for file_path, file_mtime in files.iteritems():
                if not os.path.exists(file_path):
                    print "File changed: %s (deleted)" % file_path
                elif os.stat(file_path).st_mtime > file_mtime:
                    print "File changed: %s (modified)" % file_path
                else: continue
                print "Restarting..."
                app.serve = False
                time.sleep(interval) # be nice and wait for running requests
                sys.exit(3)
    while True:
        args = [sys.executable] + sys.argv
        environ = os.environ.copy()
        environ['BOTTLE_CHILD'] = 'true'
        exit_status = subprocess.call(args, env=environ)
        if exit_status != 3:
            sys.exit(exit_status)






# Templates

class TemplateError(HTTPError):
    def __init__(self, message):
        HTTPError.__init__(self, 500, message)


class BaseTemplate(object):
    """ Base class and minimal API for template adapters """
    extentions = ['tpl','html','thtml','stpl']
    settings = {} #used in prepare()
    defaults = {} #used in render()

    def __init__(self, source=None, name=None, lookup=[], encoding='utf8', settings={}):
        """ Create a new template.
        If the source parameter (str or buffer) is missing, the name argument
        is used to guess a template filename. Subclasses can assume that
        self.source and/or self.filename are set. Both are strings.
        The lookup, encoding and settings parameters are stored as instance
        variables.
        The lookup parameter stores a list containing directory paths.
        The encoding parameter should be used to decode byte strings or files.
        The settings parameter contains a dict for engine-specific settings.
        """
        self.name = name
        self.source = source.read() if hasattr(source, 'read') else source
        self.filename = source.filename if hasattr(source, 'filename') else None
        self.lookup = map(os.path.abspath, lookup)
        self.encoding = encoding
        self.settings = self.settings.copy() # Copy from class variable
        self.settings.update(settings) # Apply
        if not self.source and self.name:
            self.filename = self.search(self.name, self.lookup)
            if not self.filename:
                raise TemplateError('Template %s not found.' % repr(name))
        if not self.source and not self.filename:
            raise TemplateError('No template specified.')
        self.prepare(**self.settings)

    @classmethod
    def search(cls, name, lookup=[]):
        """ Search name in all directiries specified in lookup.
        First without, then with common extentions. Return first hit. """
        if os.path.isfile(name): return name
        for spath in lookup:
            fname = os.path.join(spath, name)
            if os.path.isfile(fname):
                return fname
            for ext in cls.extentions:
                if os.path.isfile('%s.%s' % (fname, ext)):
                    return '%s.%s' % (fname, ext)

    @classmethod
    def global_config(cls, key, *args):
        ''' This reads or sets the global settings stored in class.settings. '''
        if args:
            cls.settings[key] = args[0]
        else:
            return cls.settings[key]

    def prepare(self, **options):
        """ Run preparatios (parsing, caching, ...).
        It should be possible to call this again to refresh a template or to
        update settings.
        """
        raise NotImplementedError

    def render(self, **args):
        """ Render the template with the specified local variables and return
        a single byte or unicode string. If it is a byte string, the encoding
        must match self.encoding. This method must be thread save!
        """
        raise NotImplementedError


class MakoTemplate(BaseTemplate):
    def prepare(self, **options):
        from mako.template import Template
        from mako.lookup import TemplateLookup
        options.update({'input_encoding':self.encoding})
        #TODO: This is a hack... http://github.com/defnull/bottle/issues#issue/8
        mylookup = TemplateLookup(directories=['.']+self.lookup, **options)
        if self.source:
            self.tpl = Template(self.source, lookup=mylookup)
        else: #mako cannot guess extentions. We can, but only at top level...
            name = self.name
            if not os.path.splitext(name)[1]:
                name += os.path.splitext(self.filename)[1]
            self.tpl = mylookup.get_template(name)

    def render(self, **args):
        _defaults = self.defaults.copy()
        _defaults.update(args)
        return self.tpl.render(**_defaults)


class CheetahTemplate(BaseTemplate):
    def prepare(self, **options):
        from Cheetah.Template import Template
        self.context = threading.local()
        self.context.vars = {}
        options['searchList'] = [self.context.vars]
        if self.source:
            self.tpl = Template(source=self.source, **options)
        else:
            self.tpl = Template(file=self.filename, **options)

    def render(self, **args):
        self.context.vars.update(self.defaults)
        self.context.vars.update(args)
        out = str(self.tpl)
        self.context.vars.clear()
        return [out]


class Jinja2Template(BaseTemplate):
    def prepare(self, prefix='#', filters=None, tests=None):
        from jinja2 import Environment, FunctionLoader
        self.env = Environment(line_statement_prefix=prefix,
                               loader=FunctionLoader(self.loader))
        if filters: self.env.filters.update(filters)
        if tests: self.env.tests.update(tests)
        if self.source:
            self.tpl = self.env.from_string(self.source)
        else:
            self.tpl = self.env.get_template(self.filename)

    def render(self, **args):
        _defaults = self.defaults.copy()
        _defaults.update(args)
        return self.tpl.render(**_defaults).encode("utf-8")

    def loader(self, name):
        fname = self.search(name, self.lookup)
        if fname:
            with open(fname) as f:
                return f.read().decode(self.encoding)


class SimpleTemplate(BaseTemplate):
    blocks = ('if','elif','else','except','finally','for','while','with','def','class')
    dedent_blocks = ('elif', 'else', 'except', 'finally')

    def prepare(self, escape_func=cgi.escape, noescape=False):
        self.cache = {}
        if self.source:
            self.code = self.translate(self.source)
            self.co = compile(self.code, '<string>', 'exec')
        else:
            self.code = self.translate(open(self.filename).read())
            self.co = compile(self.code, self.filename, 'exec')
        enc = self.encoding
        self._str = lambda x: touni(x, enc)
        self._escape = lambda x: escape_func(touni(x, enc))
        if noescape:
            self._str, self._escape = self._escape, self._str

    def translate(self, template):
        stack = [] # Current Code indentation
        lineno = 0 # Current line of code
        ptrbuffer = [] # Buffer for printable strings and token tuple instances
        codebuffer = [] # Buffer for generated python code
        touni = functools.partial(unicode, encoding=self.encoding)

        def tokenize(line):
            for i, part in enumerate(re.split(r'\{\{(.*?)\}\}', line)):
                if i % 2:
                    if part.startswith('!'): yield 'RAW', part[1:]
                    else: yield 'CMD', part
                else: yield 'TXT', part

        def flush(): # Flush the ptrbuffer
            if not ptrbuffer: return
            cline = ''
            for line in ptrbuffer:
                for token, value in line:
                    if token == 'TXT': cline += repr(value)
                    elif token == 'RAW': cline += '_str(%s)' % value
                    elif token == 'CMD': cline += '_escape(%s)' % value
                    cline +=  ', '
                cline = cline[:-2] + '\\\n'
            cline = cline[:-2]
            if cline[:-1].endswith('\\\\\\\\\\n'):
                cline = cline[:-7] + cline[-1] # 'nobr\\\\\n' --> 'nobr'
            cline = '_printlist((' + cline + '))'
            del ptrbuffer[:] # Do this before calling code() again
            code(cline)

        def code(stmt):
            for line in stmt.splitlines():
                codebuffer.append('  ' * len(stack) + line.strip())

        for line in template.splitlines(True):
            lineno += 1
            line = line if isinstance(line, unicode)\
                        else unicode(line, encoding=self.encoding)
            if lineno <= 2:
                m = re.search(r"%.*coding[:=]\s*([-\w\.]+)", line)
                if m: self.encoding = m.group(1)
                if m: line = line.replace('coding','coding (removed)')
            if line.strip()[:2].count('%') == 1:
                line = line.split('%',1)[1].lstrip() # Full line following the %
                cline = line.split('#')[0].strip() # Line without commends (TODO: fails for 'a="#"')
                cmd = re.split(r'[^a-zA-Z0-9_]', line)[0]
                flush() ##encodig (TODO: why?)
                if cmd in self.blocks:
                    if cmd in self.dedent_blocks: cmd = stack.pop()
                    code(line)
                    if cline.endswith(':'): stack.append(cmd)
                elif cmd == 'end' and stack:
                    code('#end(%s) %s' % (stack.pop(), line.strip()[3:]))
                elif cmd == 'include':
                    p = cline.split(None, 2)[1:]
                    if len(p) == 2:
                        code("_=_include(%s, _stdout, %s)" % (repr(p[0]), p[1]))
                    elif p:
                        code("_=_include(%s, _stdout)" % repr(p[0]))
                    else: # Empty %include -> reverse of %rebase
                        code("_printlist(_base)")
                elif cmd == 'rebase':
                    p = cline.split(None, 2)[1:]
                    if len(p) == 2:
                        code("globals()['_rebase']=(%s, dict(%s))" % (repr(p[0]), p[1]))
                    elif p:
                        code("globals()['_rebase']=(%s, {})" % repr(p[0]))
                else:
                    code(line)
            else: # Line starting with text (not '%') or '%%' (escaped)
                if line.strip().startswith('%%'):
                    line = line.replace('%%', '%', 1)
                ptrbuffer.append(tokenize(line))
        flush()
        return '\n'.join(codebuffer) + '\n'

    def subtemplate(self, name, stdout, **args):
        if name not in self.cache:
            self.cache[name] = self.__class__(name=name, lookup=self.lookup)
        return self.cache[name].execute(stdout, **args)

    def execute(self, _stdout, **args):
        env = self.defaults.copy()
        env.update({'_stdout': _stdout, '_printlist': _stdout.extend,
               '_include': self.subtemplate, '_str': self._str,
               '_escape': self._escape})
        env.update(args)
        eval(self.co, env)
        if '_rebase' in env:
            subtpl, rargs = env['_rebase']
            subtpl = self.__class__(name=subtpl, lookup=self.lookup)
            rargs['_base'] = _stdout[:] #copy stdout
            del _stdout[:] # clear stdout
            return subtpl.execute(_stdout, **rargs)
        return env

    def render(self, **args):
        """ Render the template using keyword arguments as local variables. """
        stdout = []
        self.execute(stdout, **args)
        return stdout


def template(tpl, template_adapter=SimpleTemplate, **kwargs):
    '''
    Get a rendered template as a string iterator.
    You can use a name, a filename or a template string as first parameter.
    '''
    if tpl not in TEMPLATES or DEBUG:
        settings = kwargs.get('template_settings',{})
        lookup = kwargs.get('template_lookup', TEMPLATE_PATH)
        if isinstance(tpl, template_adapter):
            TEMPLATES[tpl] = tpl
            if settings: TEMPLATES[tpl].prepare(settings)
        elif "\n" in tpl or "{" in tpl or "%" in tpl or '$' in tpl:
            TEMPLATES[tpl] = template_adapter(source=tpl, lookup=lookup, settings=settings)
        else:
            TEMPLATES[tpl] = template_adapter(name=tpl, lookup=lookup, settings=settings)
    if not TEMPLATES[tpl]:
        abort(500, 'Template (%s) not found' % tpl)
    kwargs['abort'] = abort
    kwargs['request'] = request
    kwargs['response'] = response
    return TEMPLATES[tpl].render(**kwargs)

mako_template = functools.partial(template, template_adapter=MakoTemplate)
cheetah_template = functools.partial(template, template_adapter=CheetahTemplate)
jinja2_template = functools.partial(template, template_adapter=Jinja2Template)

def view(tpl_name, **defaults):
    ''' Decorator: Rendes a template for a handler.
        Return a dict of template vars to fill out the template.
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, dict):
                tplvars = defaults.copy()
                tplvars.update(result)
                return template(tpl_name, **tplvars)
            return result
        return wrapper
    return decorator

mako_view = functools.partial(view, template_adapter=MakoTemplate)
cheetah_view = functools.partial(view, template_adapter=CheetahTemplate)
jinja2_view = functools.partial(view, template_adapter=Jinja2Template)






# Modul initialization and configuration

TEMPLATE_PATH = ['./', './views/']
TEMPLATES = {}
DEBUG = False
MEMFILE_MAX = 1024*100
HTTP_CODES = {
    100: 'CONTINUE',
    101: 'SWITCHING PROTOCOLS',
    200: 'OK',
    201: 'CREATED',
    202: 'ACCEPTED',
    203: 'NON-AUTHORITATIVE INFORMATION',
    204: 'NO CONTENT',
    205: 'RESET CONTENT',
    206: 'PARTIAL CONTENT',
    300: 'MULTIPLE CHOICES',
    301: 'MOVED PERMANENTLY',
    302: 'FOUND',
    303: 'SEE OTHER',
    304: 'NOT MODIFIED',
    305: 'USE PROXY',
    306: 'RESERVED',
    307: 'TEMPORARY REDIRECT',
    400: 'BAD REQUEST',
    401: 'UNAUTHORIZED',
    402: 'PAYMENT REQUIRED',
    403: 'FORBIDDEN',
    404: 'NOT FOUND',
    405: 'METHOD NOT ALLOWED',
    406: 'NOT ACCEPTABLE',
    407: 'PROXY AUTHENTICATION REQUIRED',
    408: 'REQUEST TIMEOUT',
    409: 'CONFLICT',
    410: 'GONE',
    411: 'LENGTH REQUIRED',
    412: 'PRECONDITION FAILED',
    413: 'REQUEST ENTITY TOO LARGE',
    414: 'REQUEST-URI TOO LONG',
    415: 'UNSUPPORTED MEDIA TYPE',
    416: 'REQUESTED RANGE NOT SATISFIABLE',
    417: 'EXPECTATION FAILED',
    500: 'INTERNAL SERVER ERROR',
    501: 'NOT IMPLEMENTED',
    502: 'BAD GATEWAY',
    503: 'SERVICE UNAVAILABLE',
    504: 'GATEWAY TIMEOUT',
    505: 'HTTP VERSION NOT SUPPORTED',
}
""" A dict of known HTTP error and status codes """



ERROR_PAGE_TEMPLATE = SimpleTemplate("""
%import cgi
%status_name = HTTP_CODES.get(e.status, 'Unknown').title()
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html>
    <head>
        <title>Error {{e.status}}: {{status_name}}</title>
    </head>
    <body>
        <h1>Error {{e.status}}: {{status_name}}</h1>
        <p>Sorry, the requested URL <tt>{{cgi.escape(request.url)}}</tt> caused an error:</p>
        <pre>{{cgi.escape(str(e.output))}}</pre>
        %if DEBUG and e.exception:
          <h2>Exception:</h2>
          <pre>{{cgi.escape(repr(e.exception))}}</pre>
        %end
        %if DEBUG and e.traceback:
          <h2>Traceback:</h2>
          <pre>{{cgi.escape(e.traceback)}}</pre>
        %end
    </body>
</html>
""") #TODO: use {{!bla}} instead of cgi.escape as soon as strlunicode is merged
""" The HTML template used for error messages """

TRACEBACK_TEMPLATE = '<h2>Error:</h2>\n<pre>%s</pre>\n' \
                     '<h2>Traceback:</h2>\n<pre>%s</pre>\n'

request = Request()
""" Whenever a page is requested, the :class:`Bottle` WSGI handler stores
metadata about the current request into this instance of :class:`Request`.
It is thread-save and can be accessed from within handler functions. """

response = Response()
""" The :class:`Bottle` WSGI handler uses metasata assigned to this instance
of :class:`Response` to generate the WSGI response. """

local = threading.local()
""" Thread-local namespace. Not used by Bottle, but could get handy """

# Initialize app stack (create first empty Bottle app)
# BC: 0.6.4 and needed for run()
app = default_app = AppStack()
app.push()
