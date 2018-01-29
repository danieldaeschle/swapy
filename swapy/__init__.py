import inspect
import json
import uuid
import os
import mimetypes

from werkzeug.wrappers import Request as WRequest, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.serving import run_simple, make_ssl_devcert
from werkzeug.routing import Rule, Map
from werkzeug.wsgi import responder, FileWrapper, SharedDataMiddleware
from werkzeug.urls import iri_to_uri
from werkzeug.utils import escape

from jinja2 import FileSystemLoader
from jinja2.environment import Environment

from .middlewares import ExceptionMiddleware


_url_map = {}
_middlewares = {}
_on_error = {}
_on_not_found = {}
_routes = {}
_ssl_for = {}
_shared_dir = {}


def _caller():
    """
    Returns the module which calls swapy

    :return: str
        Name of the module
    """
    return inspect.currentframe().f_back.f_back.f_globals['__name__']


def _caller_frame():
    """
    Returns the frame of the module which calls swapy

    :return: Frame
        Frame of the module
    """
    return inspect.currentframe().f_back.f_back


def _init(module):
    """
    Adds every module which is calling first time to routes and middlewares

    :param module: str
        The name of the module which should be initialized
    """
    global _url_map, _middlewares, _on_error, _on_not_found, _ssl_for, _shared_dir

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
    if module not in _ssl_for:
        _ssl_for[module] = None
    if module not in _shared_dir:
        _shared_dir[module] = None


def _error_handler(e, module):
    """
    Handles the errors at requests

    :param e: Exception
    :param module: str
        Name of the module
    """
    global _on_error
    try:
        res = _on_error[module](e)
        if type(res) == tuple:
            return Response(*res)
        else:
            return Response(res)
    except TypeError:
        return e


def _error(module, f):
    """
    Sets the given function to the given module as error handler

    :param module: str
        Name of the module
    :param f: callable
        The function which will be set for the module as error handler
    """
    global _on_error
    _init(module)
    _on_error[module] = f


def _not_found_handler(e, module):
    """
    Error handler if the route is not found

    :param e: Exception
    :param module: str
        Name of the module
    :return: Response | Exception
    """
    global _on_not_found
    try:
        res = _on_not_found[module](e)
        if type(res) == tuple:
            return Response(*res)
        else:
            return Response(res)
    except TypeError:
        return e


def _shared(frame, directory):
    """
    Adds a directory as shared for the given module

    :param frame: Frame
        Frame of the module
    :param directory:
        Absolute path or relative path
    """
    global _shared_dir
    module_name = frame.f_globals['__name__']
    if directory is True:
        directory = 'shared'
    directory = os.path.join(os.path.dirname(frame.f_globals['__file__']), directory)
    directory = directory.replace('\\', '/')
    _shared_dir[module_name] = directory


def _find_route(name):
    """
    Returns the route by name (url)

    :param name: str
        Url of the route
    :return: Rule | None
        Route rule from werkzeug
    """

    global _url_map
    for module in _url_map.keys():
        routes = _url_map[module]
        for route in routes:
            if route['url'] == name:
                return route
    return None


def _register_route(module, url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
    """
    Adds a route to the module which calls this

    :param module: str
        Name of the module
    :param url: str
        Default = '/'
    :param methods:
        HTTP methods
        Default = ('GET', 'POST', 'PUT', 'DELETE')
    :return: callable
        A decorator which registers a function
    """
    global _url_map, _middlewares, _on_error, _routes
    _init(module)

    #  Adjust path
    if not url.startswith('/'):
        url = '/{}'.format(url)
    if url == '/*':
        url = '/<path:path>'

    # Check if rule already exists
    for route in _url_map[module].iter_rules():
        if route.rule == url and [method for method in route.methods if method in methods]:
            raise Exception('Path "{}" already exists in "{}". Cannot add route to module "{}". '
                            'Maybe you included routes with the same url?'.format(route.rule, module, module))

    def decorator(f):
        """
        Registers a function as route

        :param f: callable
        :return: callable
            Returns f
        """
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
        rule = Rule(url, methods=methods, endpoint=name, strict_slashes=False)
        _url_map[module].add(rule)
        _routes[module][name] = {'function': handle, 'on_error': _on_error[module], 'url': url}
        return f
    return decorator


def _use(module, *middlewares_):
    """
    Registers middlewares

    :param module: str
        Name of the module
    :param middlewares_: callable[]
        List of decorators / middlewares
    """
    global _middlewares
    _init(module)
    for middleware in middlewares_:
        _middlewares[module].append(middleware)


def _ssl(module, host='127.0.0.1', path=None):
    """
    Adds SSL support for development

    :param module: str
        Name of the module
    :param host: str
        Domain or IP of the server
        Default = '127.0.0.1'
    :param path: str
        Path to cert files (without .crt and .key ending)
        If empty you have to install python OpenSSL lib
        Default = None
    """
    global _ssl_for
    if path:
        _ssl_for[module] = make_ssl_devcert(path, host=host)
    else:
        import importlib
        # noinspection PyDeprecation
        open_ssl = importlib.find_loader('OpenSSL')
        if open_ssl:
            _ssl_for[module] = 'adhoc'
        else:
            raise ModuleNotFoundError('SSL generation requires the PyOpenSSl module. Please install it or pass the path\
             to your self generated certificate')


def _favicon(module, path):
    """
    Registers route for favicon

    :param module: str
        Name of the module
    :param path: str
        Path to favicon file
    """
    def handle():
        with open(path, 'rb') as f:
            return f.read()
    _register_route(module, '/favicon.ico')(handle)


def _not_found(module, f):
    """
    Registers not found function

    :param module: str
        Name of the module
    :param f: callable
        Function which will be registered
    """
    global _on_not_found
    _init(module)
    _on_not_found[module] = f


def _include(module, target, prefix=''):
    """
    Includes all functions from source module into target module

    :param module: str
        Name of the source module
    :param target: str
        Name of the target module
    :param prefix: str
        Route prefix for functions of the source module
    """
    global _url_map
    _init(module)
    _init(target.__name__)
    if not prefix.startswith('/') and len(prefix) >= 1:
        prefix = '/{}'.format(prefix)
    if prefix == '/':
        prefix = ''
    routes = _url_map[target.__name__]
    for route in routes.iter_rules():
        rule = '{}{}'.format(prefix, route.rule)
        for r in _url_map[module].iter_rules():
            if rule == r.rule:
                raise Exception('Path "{}" already exists in "{}". Module "{}" cannot be included in "{}".'
                                .format(rule, module, target.__name__, module))
    for name in _routes[target.__name__].keys():
        _routes[module][name] = _routes[target.__name__][name]
    for route in routes.iter_rules():
        rule = '{}{}'.format(prefix, route.rule)
        new_route = Rule(rule, endpoint=route.endpoint, methods=route.methods, strict_slashes=False)
        _url_map[module].add(new_route)


def _build_app(module):
    """
    Returns the built app

    :param module: str
        Name of the module
    :return: callable
        The application
    """

    global _url_map, _routes, _shared_dir

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
                except TypeError:
                    res = f()

                # Checks if the type is iterable to prevent more errors
                iter(res)

                if isinstance(res, tuple) or isinstance(res, tuple) and isinstance(res[0], FileWrapper):
                    return Response(*res, direct_passthrough=True)
                elif isinstance(res, FileWrapper):
                    return Response(res, direct_passthrough=True)
                else:
                    return Response(res)
            except NotFound as ex:
                return _not_found_handler(ex, module)
            except HTTPException as ex:
                return _error_handler(ex, module)
        return urls.dispatch(dispatch)
    if _shared_dir[module]:
        return SharedDataMiddleware(application, {
            '/shared': _shared_dir[module]
        })
    return application


def render(file_path, **kwargs):
    """
    Returns a rendered HTML file

    :param file_path: str
        Path to file including filename and extension
    :param kwargs: object
        Additional arguments which will forward to the template
    :return: str
        Rendered HTML file
    """
    module = _caller_frame()
    path = os.path.dirname(os.path.realpath(module.f_globals['__file__']))
    env = Environment()
    env.loader = FileSystemLoader(path)
    template = env.get_template(file_path)
    return template.render(kwargs)


def redirect(location, code=301):
    """
    Returns a redirect response

    :param location: str
        Url where the user should be redirect
        Example: https://github.com
    :param code: int
        HTTP code which the server returns to the client
        It should be any 3xx code
        See more at Wikipedia - Http Status Codes
        Default = 301
    :return: (str, int, dict)
        Redirect response
    """
    location = iri_to_uri(location, safe_conversion=True)
    response = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'\
        '<title>Redirecting...</title>\n'\
        '<h1>Redirecting...</h1>\n'\
        '<p>You should be redirected automatically to target URL: '\
        '<a href="{}">{}</a>.  If not click the link.'.format(escape(location), escape(location))
    return response, code, {'Location': location, 'Content-Type': 'text/html'}


def file(path, name=None):
    """
    Returns a file response

    :param path: str
        Path to the file
    :param name: str
        Name of the file
        If it is None the name is like the file name
        Default = None
    :return: FileWrapper
        FileWrapper class from werkzeug
    """
    if not os.path.isabs(path):
        path = os.path.abspath(_caller_frame().f_globals['__file__'])
    f = open(path, 'rb')
    if file:
        mime = mimetypes.guess_type(path)[0]
        size = os.path.getsize(path)
        filename = os.path.basename(path) if not name else name
        headers = {'Content-Type': mime, 'Content-Disposition': 'attachment;filename='+filename, 'Content-Length': size}
        return FileWrapper(f, 8192), 200, headers
    raise FileNotFoundError()


def favicon(path):
    """
    Registers a route to the favicon

    :param path: str
        Path to the file
    """
    _favicon(_caller(), path)


def ssl(host='127.0.0.1', path=None):
    """
    Registers SSL

    :param host: str
        IP address of the server
        Default = '127.0.0.1'
    :param path: str
        Path to the certificates
        If it is None swapy generates certificates for development, but then you should have python OpenSSL installed
        Default = None
    :return:
    """
    _ssl(_caller(), host, path)


def error(f):
    """
    Registers a function as error handler

    :param f: callable
        Callable should receive an Exception object as parameter
    """
    _error(_caller(), f)


def shared(directory):
    """
    Registers a directory as shared

    :param directory: str
        Path to the directory
    """
    module = _caller_frame()
    _shared(module, directory)


def not_found(f):
    """
    Registers a function as 404 error handler

    :param f: callable
        Callable should receive an Exception object as parameter
    """
    _not_found(_caller(), f)


def on(url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
    """
    Route registerer for all http methods

    :param url: str
    :param methods: list | tuple
        HTTP method
        Default = ('GET', 'POST', 'PUT', 'DELETE')
    :return: callable
    """
    return _register_route(_caller(), url, methods)


def on_get(url='/'):
    """
    Route registerer for GET http method

    :param url: str
    :return: callable
    """
    return _register_route(_caller(), url, methods=['GET'])


def on_post(url='/'):
    """
    Route registerer for POST http method

    :param url: str
    :return: callable
    """
    return _register_route(_caller(), url, methods=['POST'])


def on_put(url='/'):
    """
    Route registerer for PUT http method

    :param url: str
    :return: callable
    """
    return _register_route(_caller(), url, methods=['PUT'])


def on_delete(url='/'):
    """
    Route registerer for DELETE http method

    :param url: str
    :return: callable
    """
    return _register_route(_caller(), url, methods=['DELETE'])


def include(module, prefix=''):
    """
    Includes a source module into the target module

    :param module: str
        Name of the source module
    :param prefix: str
        Routes from the source module will get the prefix in front of their route
        Default = ''
    """
    _include(_caller(), module, prefix)


def config(cfg):
    """
    A short function for all other setting functions like: include, ssl, error, favicon etc.
    It also handles the entry 'environment' key which can contains 'production' and 'development' or just
        global variables.
    The variables can used by extensions.
    'production' and 'development' are reserved varaibles in this case which you can't use if you don't want to
        seperate that.

    :param cfg: dict
        The config dict
    """
    module = _caller()
    if isinstance(cfg, dict):
        if cfg.get('use'):
            middlewares_ = cfg['use']
            if isinstance(middlewares_, (tuple, list)):
                _use(module, *middlewares_)
            else:
                _use(module, middlewares_)
        if cfg.get('include'):
            modules_ = cfg['include']

            def handle(args):
                if isinstance(args, (tuple, list)):
                    _include(module, *args)
                else:
                    _include(module, args)
            if isinstance(modules_, list):
                for target in modules_:
                    handle(target)
            else:
                handle(modules_)
        if cfg.get('error'):
            _error(module, cfg['error'])
        if cfg.get('ssl'):
            ssl_ = cfg['ssl']
            if isinstance(ssl_, (tuple, list)):
                _ssl(module, *ssl_)
            else:
                _ssl(module, ssl_)
        if cfg.get('favicon'):
            _favicon(module, cfg['favicon'])
        if cfg.get('not_found'):
            _not_found(module, cfg['not_found'])
        if cfg.get('shared'):
            _shared(_caller_frame(), cfg['shared'])
    else:
        raise TypeError('Type {} is not supported as config. Please use a dict.'.format(type(cfg)))


def use(*middlewares_):
    """
    Registers middlewares for global use

    :param middlewares_: callable[]
         Arguments of decorators / middlewares
    """
    _use(_caller(), *middlewares_)


def app():
    """
    Returns the built app

    :return: callable
        The app
    """
    return _build_app(_caller())


def run(host='127.0.0.1', port=5000, debug=False, module_name=None):
    """
    It runs the app

    :param host: IP address
        '0.0.0.0' for public access
    :param port: int
    :param debug: bool
        Enables debug output and hot reload
    :param module_name: str
        Starts the app from the specific module if given
    """
    global _ssl_for

    module = module_name if module_name else _caller()
    run_simple(host, port, _build_app(module), use_debugger=debug, use_reloader=debug, ssl_context=_ssl_for[module])


class Request(WRequest):
    """
    Request class which inherits from werkzeug's request class
    It adds the json function
    """
    @property
    def json(self):
        """
        Returns dict from json string if available

        :return: dict
        """
        try:
            content = json.loads(self.data.decode())
        except json.JSONDecodeError:
            content = {}
        return content
