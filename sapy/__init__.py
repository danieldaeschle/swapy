import inspect
import uuid
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException
from werkzeug.serving import run_simple
from werkzeug.routing import Rule, Map
from werkzeug.wsgi import responder
from .middlewares import ExceptionMiddleware
import os
import mimetypes


_url_map = {}
_middlewares = {}
_on_error = {}
_routes = {}


def _caller():
    """Returns the module which calls sapy"""

    return inspect.currentframe().f_back.f_back.f_globals['__name__']


def _init(name):
    """Adds every module which is calling first time to routes and middlewares"""

    global _url_map, _middlewares, _on_error
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


def _find_route(name):
    """Returns the route by name"""

    global _url_map
    for module in _url_map.keys():
        routes = _url_map[module]
        for route in routes:
            if route['url'] == name:
                return route
    return None


def send_file(path, name=None):
    file = open(path)
    if file:
        mime = mimetypes.guess_type(path)[0]
        size = os.path.getsize(path)
        filename = os.path.basename(path) if not name else name
        headers = {'Content-Type': mime, 'Content-Disposition': 'attachment;filename='+filename, 'Content-Length': size}
        return file.read(), 200, headers
    raise FileNotFoundError()


def register_route(url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
    """Adds a route to the module which calls this"""

    global _url_map, _middlewares, _on_error, _routes
    
    #  Adjust path
    if not url.startswith('/'):
        url = '/{}'.format(url)
    if url == '/*':
        url = '/<path:path>'

    def decorator(f):
        mws = _middlewares[_caller()]

        def handle(*args, **kwargs):
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
        _url_map[_caller()].add(route)
        _routes[_caller()][name] = {'function': handle, 'on_error': _on_error[_caller()]}
        return f
    return decorator


def error(f):
    global _on_error
    _on_error[_caller()] = f


def on(url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
    """Route registerer for all http methods"""

    _init(_caller())
    return register_route(url, methods)


def on_get(url='/'):
    """Route registerer for GET http method"""

    _init(_caller())
    return register_route(url, methods=['GET'])


def on_post(url='/'):
    """Route registerer for POST http method"""

    _init(_caller())
    return register_route(url, methods=['POST'])


def on_put(url='/'):
    """Route registerer for PUT http method"""

    _init(_caller())
    return register_route(url, methods=['PUT'])


def on_delete(url='/'):
    """Route registerer for DELETE http method"""

    _init(_caller())
    return register_route(url, methods=['DELETE'])


def include(module, prefix=''):
    """Includes a module into antoher module"""

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

    global _url_map, _routes

    @responder
    def application(environ, start_response):
        urls = _url_map[name].bind_to_environ(environ)
        req = Request(environ)

        try:
            def dispatch(endpoint, args):
                try:
                    args = dict(args)
                    setattr(req, 'url_args', args)
                    f = _routes[name][endpoint]['function']
                    res = f(req=req)
                    if type(res) == tuple and type(res[0]) != str:
                        raise Exception('Type {} in "{}" is not serializable as output'.format(type(res[0]), req.path))
                    elif type(res) != tuple and type(res) != str:
                        raise Exception('Type {} in "{}" is not serializable as output'.format(type(res), req.path))
                    if type(res) == tuple:
                        response = Response(*res)
                    else:
                        response = Response(res)
                except HTTPException as ex:
                    print('test')
                    return _error(ex, name)
                return response
            return urls.dispatch(dispatch, catch_http_exceptions=True)
        except Exception as e:
            return _error(e, name)
    return application


def run(host='127.0.0.1', port=5000, debug=False):
    """Runs the app"""

    run_simple(host, port, app(_caller()), use_debugger=debug, use_reloader=debug)
    # app(_caller()).run(host, port, debug, **options)
