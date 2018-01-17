import inspect
import uuid
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.serving import run_simple
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
_routes = {}
_debug = {}


def _caller():
    """Returns the module which calls sapy"""

    return inspect.currentframe().f_back.f_back.f_globals['__name__']


def _init(name):
    """Adds every module which is calling first time to routes and middlewares"""

    global _url_map, _middlewares, _on_error, _debug
    # if not _app:
    #     _app = Flask(__name__)
    #     for cls in HTTPException.__subclasses__():
    #         _app.register_error_handler(cls, _error)
    if name not in _url_map:
        _url_map[name] = Map([])
    if name not in _routes:
        _routes[name] = {}
    if name not in _middlewares:
        _middlewares[name] = []
    if name not in _on_error:
        _on_error[name] = ExceptionMiddleware
    if name not in _debug:
        _debug[name] = False


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
    pass


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


def error(f):
    global _on_error
    _init(_caller())
    _on_error[_caller()] = f


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
    

def app(name):
    """Returns the app"""

    global _url_map, _routes, _debug

    @responder
    def application(environ, _):
        urls = _url_map[name].bind_to_environ(environ)
        req = Request(environ)

        try:
            def dispatch(endpoint, args):
                try:
                    args = dict(args)
                    setattr(req, 'url_args', args)
                    f = _routes[name][endpoint]['function']
                    try:
                        res = f(req=req)
                    except TypeError:
                        res = f()
                    if type(res) == tuple and type(res[0]) != str and type(res[0]) != FileWrapper:
                        raise TypeError('Type {} in "{}" is not serializable as output'.format(type(res[0]), req.path))
                    elif type(res) != tuple and type(res) != str and type(res) != FileWrapper:
                        raise TypeError('Type {} in "{}" is not serializable as output'.format(type(res), req.path))
                    if type(res) == tuple:
                        if type(res[0]) == FileWrapper:
                            response = Response(*res, direct_passthrough=True)
                        else:
                            response = Response(*res)
                    else:
                        if type(res) == FileWrapper:
                            response = Response(res, direct_passthrough=True)
                        else:
                            response = Response(res)
                except NotFound as ex:
                    return _not_found(ex, name)
                except HTTPException as ex:
                    return _error(ex, name)
                return response
            return urls.dispatch(dispatch)
        except Exception as e:
            if not _debug[name]:
                return _error(e, name)
            return e
    return application


def run(host='127.0.0.1', port=5000, debug=False):
    """Runs the app"""
    global _debug

    _debug[_caller()] = debug
    run_simple(host, port, app(_caller()), use_debugger=debug, use_reloader=debug)
