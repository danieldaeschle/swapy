import inspect
import uuid
import os

from werkzeug.wsgi import responder, SharedDataMiddleware
from werkzeug.serving import make_ssl_devcert
from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError
from werkzeug.routing import Rule, Map
from werkzeug.contrib.sessions import FilesystemSessionStore

from .middlewares import DefaultException
from .wrappers import Request, response_from

_modules = {}


def caller():
    """
    Returns the module which calls swapy

    :return: str
        Name of the module
    """
    return inspect.currentframe().f_back.f_back.f_globals['__name__']


def caller_frame():
    """
    Returns the frame of the module which calls swapy

    :return: Frame
        Frame of the module
    """
    return inspect.currentframe().f_back.f_back


def init(module):
    """
    Adds a state_ object for every module into the modules list

    :param module: str
        The name of the module which should be initialized
    """
    global _modules
    if module not in _modules:
        _modules[module] = State()


def state(module):
    """
    Returns state_ of the given module

    :param module: str
        The name of the module
    :return: State
    """
    global _modules
    init(module)
    return _modules[module]


def error_handler(e, module):
    """
    Handles the errors at requests

    :param e: Exception
    :param module: str
        Name of the module
    """
    state_ = state(module)
    try:
        res = state_.on_error(e)
        if type(res) == tuple:
            return Response(*res)
        else:
            return Response(res)
    except TypeError:
        return e


def error(module, f):
    """
    Sets the given function to the given module as error handler

    :param module: str
        Name of the module
    :param f: callable
        The function which will be set for the module as error handler
    """
    state_ = state(module)
    state_.on_error = f


def not_found_handler(e, module):
    """
    Error handler if the route is not found

    :param e: Exception
    :param module: str
        Name of the module
    :return: WResponse | Exception
    """
    state_ = state(module)
    try:
        res = state_.on_not_found(e)
        if type(res) == tuple:
            return Response(*res)
        else:
            return Response(res)
    except TypeError:
        return e


def shared(frame, directory):
    """
    Adds a directory as shared for the given module

    :param frame: Frame
        Frame of the module
    :param directory:
        Absolute path or relative path
    """
    module_name = frame.f_globals['__name__']
    state_ = state(module_name)
    if directory is True:
        directory = 'shared'
    directory = os.path.join(os.path.dirname(frame.f_globals['__file__']), directory)
    directory = directory.replace('\\', '/')
    state_.shared = directory


def find_route(name):
    """
    Returns the route by name (url)

    :param name: str
        Url of the route
    :return: Rule | None
        Route rule from werkzeug
    """
    global _modules
    for state_ in _modules.keys():
        for route in state_.url_map:
            if route['url'] == name:
                return route
    return None


def register_route(module, url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
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
    state_ = state(module)

    #  Adjust path
    if not url.startswith('/'):
        url = '/{}'.format(url)
    if url == '/*':
        url = '/<path:path>'

    # Check if rule already exists
    for route in state_.url_map.iter_rules():
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
        def handle(*args, **kwargs):
            target = f
            for m in state_.middlewares:
                target = m(target(*args, **kwargs))
            try:
                res = target(*args, **kwargs)
            except TypeError as e:
                if 'arguments' in str(e):
                    res = target(**kwargs)
                else:
                    res = target(*args, **kwargs)
            if res:
                return res
            else:
                return ''

        name = str(uuid.uuid4())
        rule = Rule(url, methods=methods, endpoint=name, strict_slashes=False)
        state_.url_map.add(rule)
        state_.routes[name] = {'function': handle, 'on_error': state_.on_error, 'url': url}
        return f

    return decorator


def use(module, *middlewares_):
    """
    Registers middlewares

    :param module: str
        Name of the module
    :param middlewares_: callable[]
        List of decorators / middlewares
    """
    state_ = state(module)
    for middleware in middlewares_:
        state_.middlewares.append(middleware)


def ssl(module, host='127.0.0.1', path=None):
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
    state_ = state(module)
    if path:
        state_.ssl = make_ssl_devcert(path, host=host)
    else:
        import importlib
        # noinspection PyDeprecation
        open_ssl = importlib.find_loader('OpenSSL')
        if open_ssl:
            state_.ssl = 'adhoc'
        else:
            raise ModuleNotFoundError('SSL generation requires the PyOpenSSl module. Please install it or pass the path\
             to your self generated certificate')


def favicon(module, path):
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

    register_route(module, '/favicon.ico')(handle)


def not_found(module, f):
    """
    Registers "not found" function

    :param module: str
        Name of the module
    :param f: callable
        Function which will be registered
    """
    state_ = state(module)
    state_.on_not_found = f


def include(module, target, prefix=''):
    """
    Includes all functions from source module into target module

    :param module: str
        Name of the source module
    :param target: str
        Name of the target module
    :param prefix: str
        Route prefix for functions of the source module
    """
    state_ = state(module)
    state_target = state(target.__name__)
    if not prefix.startswith('/') and len(prefix) >= 1:
        prefix = '/{}'.format(prefix)
    if prefix == '/':
        prefix = ''
    routes = state_target.url_map
    for route in routes.iter_rules():
        rule = '{}{}'.format(prefix, route.rule)
        for r in state_.url_map.iter_rules():
            if rule == r.rule:
                raise Exception('Path "{}" already exists in "{}". Module "{}" cannot be included in "{}".'
                                .format(rule, module, target.__name__, module))
    for name in state_target.routes.keys():
        state_.routes[name] = state_target.routes[name]
    for route in routes.iter_rules():
        rule = '{}{}'.format(prefix, route.rule)
        new_route = Rule(rule, endpoint=route.endpoint, methods=route.methods, strict_slashes=False)
        state_.url_map.add(new_route)
    state_target.environment = state_.environment


def environment(module, data):
    """
    Sets the environment data to the given module

    :param module: str
        The name of the module
    :param data: dict
    """
    state_ = state(module)
    state_.environment.parse(data)


def build_app(module):
    """
    Returns the built app

    :param module: str
        Name of the module
    :return: callable
        The application
    """
    state_ = state(module)
    session_store = FilesystemSessionStore()

    @responder
    def application(environ, _):
        urls = state_.url_map.bind_to_environ(environ)
        req = Request(environ)
        req.state = state_
        sid = req.cookies.get('session_id')
        if sid is None:
            req.session = session_store.new()
        else:
            req.session = session_store.get(sid)

        def dispatch(endpoint, args):
            try:
                args = dict(args)
                req.url_args = args
                f = state_.routes[endpoint]['function']
                res = response_from(f(req))
                try:
                    iter(res.content)
                except TypeError:
                    raise InternalServerError('Result {} of \'{}\' is not a valid response'
                                              .format(res.content, req.path))
                ret = Response(res.content, res.code, res.headers, direct_passthrough=True)
                for cookie in res.cookies.keys():
                    ret.set_cookie(cookie, res.cookies[cookie])
                if req.state.environment.get('secret_key') is not None and req.secure_cookie.should_save:
                    req.secure_cookie.save_cookie(ret)
                return ret
            except NotFound as ex:
                return not_found_handler(ex, module)
            except HTTPException as ex:
                return error_handler(ex, module)
        try:
            result = urls.dispatch(dispatch)
        except NotFound as e:
            result = not_found_handler(e, module)
        if req.session.should_save:
            session_store.save(req.session)
            result.set_cookie('session_id', req.session.sid)
        return result

    if state_.shared:
        application = SharedDataMiddleware(application, {
            '/shared': state_.shared
        })
    return application


class State:
    """
    state_ class for every module
    """
    _slots__ = ['url_map', 'middlewares', 'on_error', 'on_not_found', 'routes', 'ssl', 'shared', 'environment', 'debug']

    def __init__(self):
        self.url_map = Map([])
        self.middlewares = []
        self.on_error = DefaultException
        self.on_not_found = DefaultException
        self.routes = {}
        self.ssl = None
        self.shared = None
        self.environment = Environment(self)
        self.debug = False


class Environment:
    """
    Environment class
    I need it that it can be referenced
    """
    _slots__ = ['data', 'development', 'production', '_state']

    def __init__(self, _state, data=None, development=None, production=None):
        self._state = _state
        if data is None:
            data = {}
        self.data = data
        self.development = development
        self.production = production

    def parse(self, data):
        self.development = data.get('development')
        self.production = data.get('production')
        data.pop('development')
        data.pop('production')
        self.data = data

    def __getitem__(self, item):
        self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __repr__(self):
        return self.runtime_data

    @property
    def runtime_data(self):
        data = self.data
        runtime = 'development' if self._state.debug else 'production'
        if self.production and self.development:
            if runtime == 'development':
                for key in self.development.keys():
                    data[key] = self.development[key]
            elif runtime == 'production':
                for key in self.production.keys():
                    data[key] = self.production[key]
        return data

    def get(self, key):
        return self.runtime_data.get(key)

    def set(self, key, value, runtime=None):
        if key == 'development' or key == 'production':
            raise AttributeError('Key {} is a reserved environment variable. You can\'t use it it this case.')
        if runtime is None:
            self.data[key] = value
        elif runtime == 'development':
            if not self.development:
                self.development = {}
            self.development[key] = value
        elif runtime == 'production':
            if not self.production:
                self.production = {}
            self.production[key] = value
        else:
            raise AttributeError('Parameter "status" must be None, "production" or "development"')
