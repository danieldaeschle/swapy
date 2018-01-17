import inspect
import uuid
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.serving import run_simple, make_ssl_devcert
from werkzeug.routing import Rule, Map
from werkzeug.wsgi import responder, FileWrapper
from werkzeug.urls import iri_to_uri
from werkzeug.utils import escape
from .middlewares import ExceptionMiddleware
import os
import mimetypes


_url_map = {}
_middlewares = {}
_on_error = {}
_on_not_found = {}
_routes = {}
_ssl = {}


def _caller():
    """Returns the module which calls sapy"""

    return inspect.currentframe().f_back.f_back.f_globals['__name__']


def _init(module):
    """Adds every module which is calling first time to routes and middlewares"""

    global _url_map, _middlewares, _on_error, _on_not_found, _ssl

    if module not in _url_map:
        _url_map[module] = Map([])
    if module not in _routes:
        _routes[module] = {}
    if module not in _middlewares:
        _middlewares[module] = []
    if module not in _on_error:
        _on_error[module] = ExceptionMiddleware
    if module not in _on_not_found:
        _on_not_found[module] = ExceptionMiddleware
    if module not in _ssl:
        _ssl[module] = None


def _error(e, module):
    global _on_error
    try:
        res = _on_error[module](e)
        if type(res) == tuple:
            return Response(*res)
        else:
            return Response(res)
    except TypeError:
        return e


def _not_found(e, module):
    global _on_not_found
    try:
        res = _on_not_found[module](e)
        if type(res) == tuple:
            return Response(*res)
        else:
            return Response(res)
    except TypeError:
        return e


def _find_route(name):
    """Returns the route by name"""

    global _url_map
    for module in _url_map.keys():
        routes = _url_map[module]
        for route in routes:
            if route['url'] == name:
                return route
    return None


def _register_route(module, url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
    """Adds a route to the module which calls this"""

    global _url_map, _middlewares, _on_error, _routes

    #  Adjust path
    if not url.startswith('/'):
        url = '/{}'.format(url)
    if url == '/*':
        url = '/<path:path>'

    def decorator(f):
        mws = _middlewares[module]

        def handle(*_, **kwargs):
            target = f
            req = kwargs['req']
            for m in mws:
                target = m(target)
            try:
                res = target(req)
            except TypeError:
                res = target()
            if res:
                return res
            else:
                return ''

        name = str(uuid.uuid4())
        route = Rule(url, methods=methods, endpoint=name, strict_slashes=False)
        _url_map[module].add(route)
        _routes[module][name] = {'function': handle, 'on_error': _on_error[module]}
        return f

    return decorator


def _build_app(module):
    """Returns the app"""

    global _url_map, _routes

    @responder
    def application(environ, _):
        urls = _url_map[module].bind_to_environ(environ)
        req = Request(environ)

        def dispatch(endpoint, args):
            try:
                args = dict(args)
                setattr(req, 'url_args', args)
                f = _routes[module][endpoint]['function']
                try:
                    res = f(req=req)
                except KeyError:
                    res = f()

                # Checks if the type is iterable to prevent more errors
                iter(res)

                if type(res) == tuple and type(res[0]) == FileWrapper:
                    return Response(*res, direct_passthrough=True)
                elif type(res) == FileWrapper:
                    return Response(res, direct_passthrough=True)
                else:
                    return Response(res)
            except NotFound as ex:
                return _not_found(ex, module)
            except HTTPException as ex:
                return _error(ex, module)
        return urls.dispatch(dispatch)
    return application


def redirect(location, code=301):
    location = iri_to_uri(location, safe_conversion=True)
    response = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'\
        '<title>Redirecting...</title>\n'\
        '<h1>Redirecting...</h1>\n'\
        '<p>You should be redirected automatically to target URL: '\
        '<a href="{}">{}</a>.  If not click the link.'.format(escape(location), escape(location))
    return response, code, {'Location': location, 'Content-Type': 'text/html'}


def file(path, name=None):
    f = open(path, 'rb')
    if file:
        mime = mimetypes.guess_type(path)[0]
        size = os.path.getsize(path)
        filename = os.path.basename(path) if not name else name
        headers = {'Content-Type': mime, 'Content-Disposition': 'attachment;filename='+filename, 'Content-Length': size}
        return FileWrapper(f, 8192), 200, headers
    raise FileNotFoundError()


def favicon(path):
    _register_route(_caller(), '/favicon.ico')(lambda: file(path))


def ssl(host, path=None):
    global _ssl
    module = _caller()
    if path:
        _ssl[module] = make_ssl_devcert(path, host=host)
    else:
        import importlib
        open_ssl = importlib.find_loader('OpenSSL')
        if open_ssl:
            _ssl[module] = 'adhoc'
        else:
            raise ModuleNotFoundError('SSL generation requires the PyOpenSSl module. Please install it or pass the path\
             to your self generated certificate')


def error(f):
    global _on_error
    _init(_caller())
    _on_error[_caller()] = f


def not_found(f):
    global _on_not_found
    _init(_caller())
    _on_not_found[_caller()] = f


def on(url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
    """Route registerer for all http methods"""

    module = _caller()
    _init(module)
    return _register_route(module, url, methods)


def on_get(url='/'):
    """Route registerer for GET http method"""

    module = _caller()
    _init(module)
    return _register_route(module, url, methods=['GET'])


def on_post(url='/'):
    """Route registerer for POST http method"""

    module = _caller()
    _init(module)
    return _register_route(module, url, methods=['POST'])


def on_put(url='/'):
    """Route registerer for PUT http method"""

    module = _caller()
    _init(module)
    return _register_route(module, url, methods=['PUT'])


def on_delete(url='/'):
    """Route registerer for DELETE http method"""

    module = _caller()
    _init(module)
    return _register_route(module, url, methods=['DELETE'])


def include(module, prefix=''):
    """Includes a module into another module"""

    global _url_map
    _init(_caller())
    _init(module.__name__)
    if not prefix.startswith('/') and len(prefix) >= 1:
        prefix = '/{}'.format(prefix)
    if prefix == '/':
        prefix = ''
    routes = _url_map[module.__name__]
    for route in routes.iter_rules():
        rule = '{}{}'.format(prefix, route.rule)
        new_route = Rule(rule, endpoint=route.endpoint, methods=route.methods, strict_slashes=False)
        _url_map[_caller()].add(new_route)
    for name in _routes[module.__name__].keys():
        _routes[_caller()][name] = _routes[module.__name__][name]


def use(middleware):
    """Registers middlewares for global use"""

    _init(_caller())
    _middlewares[_caller()].append(middleware)


def app():
    module = _caller()
    return _build_app(module)


def run(host='127.0.0.1', port=5000, debug=False):
    """Runs the app"""
    global _ssl

    module = _caller()
    run_simple(host, port, _build_app(module), use_debugger=debug, use_reloader=debug, ssl_context=_ssl[module])
