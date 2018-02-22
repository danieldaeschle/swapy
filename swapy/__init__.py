import os
import mimetypes

from werkzeug.serving import run_simple
from werkzeug.wsgi import FileWrapper
from werkzeug.urls import iri_to_uri
from werkzeug.utils import escape

from jinja2 import FileSystemLoader
from jinja2.environment import Environment

from . import _utils
from .wrappers import Response


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
    module = _utils.caller_frame()
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
        HTTP status code which the server returns to the client
        It should be any 3xx code
        See more at Wikipedia - Http Status Codes
        Default = 301
    :return: :class:`swapy.wrappers.Response`
        Redirect response
    """
    location = iri_to_uri(location, safe_conversion=True)
    content = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n' \
              '<title>Redirecting...</title>\n' \
              '<h1>Redirecting...</h1>\n' \
              '<p>You should be redirected automatically to target URL: ' \
              '<a href="{}">{}</a>.  If not click the link.'.format(escape(location), escape(location))
    return Response(content, code, {'Location': location, 'Content-Type': 'text/html'})


def file(path, name=None):
    """
    Returns a file response

    :param path: str
        Path to the file
    :param name: str
        Name of the file which will be returned.
        If it is None the name is like the real file name.
        Default = None
    :return: :class:`werkzeug.wsgi.FileWrapper`
    """
    if not os.path.isabs(path):
        caller_file = os.path.abspath(_utils.caller_frame().f_globals['__file__'])
        path = caller_file.replace(os.path.basename(caller_file), path)
    f = open(path, 'rb')
    if file:
        mime = mimetypes.guess_type(path)[0]
        size = os.path.getsize(path)
        filename = os.path.basename(path) if not name else name
        headers = {'Content-Type': mime, 'Content-Disposition': 'attachment;filename=' + filename,
                   'Content-Length': size}
        return FileWrapper(f, 8192), 200, headers
    raise FileNotFoundError()


def favicon(path):
    """
    Registers a route to the favicon

    :param path: str
        Path to the file
    """
    _utils.favicon(_utils.caller(), path)


def environment(data):
    """
    Sets the given data as environment

    The keys "production" and "development" are reserved.
    All keys in "production" are used if the app runs without the debug=True.
    I the other case "development" is used.

    Example:
        'production': {
            'host': '0.0.0.0'
        },
        'development': {
            'host': '127.0.0.1'
        }

        If the app starts without debug mode the "host" key with the value "0.0.0.0" is the priority value.

    :param data: dict
    """
    module = _utils.caller()
    _utils.environment(module, data)


def get_env(key):
    """
    Returns the value of the give key in environment variables

    :param key: str
    :return: object
    """
    state = _utils.state(_utils.caller())
    return state.environment.get(key)


def set_env(key, value):
    """
    Sets a value for a key in the global environment

    :param key: str
    :param value: object
    """
    state = _utils.state(_utils.caller())
    state.environment.set(key, value)


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
    """
    _utils.ssl(_utils.caller(), host, path)


def error(f):
    """
    Registers a function as error handler

    :param f: function
        Function should receive an Exception object as parameter
    """
    _utils.error(_utils.caller(), f)


def shared(directory):
    """
    Registers a directory as shared

    :param directory: str
        Path to the directory
    """
    module = _utils.caller_frame()
    _utils.shared(module, directory)


def not_found(f):
    """
    Registers a function as 404 error handler

    :param f: function
        Function should receive an :class:`werkzeug.exceptions.Exception` object as parameter
    """
    _utils.not_found(_utils.caller(), f)


def routes():
    """
    Returns a list of all registered routes

    :return: list
    """
    module = _utils.caller()
    return [item[1]['url'] for item in list(_utils.state(module).routes.items())]


def on(url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
    """
    Route registerer for all http methods

    :param url: str
    :param methods: list | tuple
        HTTP method
        Default = ('GET', 'POST', 'PUT', 'DELETE')
    :return: function
    """
    return _utils.register_route(_utils.caller(), url, methods)


def on_get(url='/'):
    """
    Route registerer for GET http method

    :param url: str
    :return: function
    """
    return _utils.register_route(_utils.caller(), url, methods=['GET'])


def on_post(url='/'):
    """
    Route registerer for POST http method

    :param url: str
    :return: function
    """
    return _utils.register_route(_utils.caller(), url, methods=['POST'])


def on_put(url='/'):
    """
    Route registerer for PUT http method

    :param url: str
    :return: function
    """
    return _utils.register_route(_utils.caller(), url, methods=['PUT'])


def on_delete(url='/'):
    """
    Route registerer for DELETE http method

    :param url: str
    :return: function
    """
    return _utils.register_route(_utils.caller(), url, methods=['DELETE'])


def include(module, prefix=''):
    """
    Includes a source module into the target module

    :param module: module
        The source module
    :param prefix: str
        Routes from the source module will get the prefix in front of their route
        Default = ''
    """
    _utils.include(_utils.caller(), module, prefix)


def config(cfg):
    """
    A short function for all other setting functions like: include, ssl, error, favicon etc.
    It also handles the entry 'environment' key which can contains 'production' and 'development' or just
        global variables.
    The variables can used by extensions.
    'production' and 'development' are reserved variables in this case which you can't use if you don't want to
        separate that.

    :param cfg: dict
        The config dict
    """
    module = _utils.caller()
    if isinstance(cfg, dict):
        if cfg.get('use'):
            middlewares_ = cfg['use']
            if isinstance(middlewares_, (tuple, list)):
                _utils.use(module, *middlewares_)
            else:
                _utils.use(module, middlewares_)
        if cfg.get('include'):
            modules_ = cfg['include']

            def handle(args):
                if isinstance(args, (tuple, list)):
                    _utils.include(module, *args)
                else:
                    _utils.include(module, args)

            if isinstance(modules_, list):
                for target in modules_:
                    handle(target)
            else:
                handle(modules_)
        if cfg.get('error'):
            _utils.error(module, cfg['error'])
        if cfg.get('ssl'):
            ssl_ = cfg['ssl']
            if isinstance(ssl_, (tuple, list)):
                _utils.ssl(module, *ssl_)
            else:
                _utils.ssl(module, ssl_)
        if cfg.get('favicon'):
            _utils.favicon(module, cfg['favicon'])
        if cfg.get('not_found'):
            _utils.not_found(module, cfg['not_found'])
        if cfg.get('shared'):
            _utils.shared(_utils.caller_frame(), cfg['shared'])
        if cfg.get('environment'):
            _utils.environment(module, cfg['environment'])
    else:
        raise TypeError('Type {} is not supported as config. Please use a dict.'.format(type(cfg)))


def use(*middlewares_):
    """
    Registers middlewares for global use

    :param middlewares_: list
         List of decorators / middlewares (functions)
    """
    _utils.use(_utils.caller(), *middlewares_)


def app():
    """
    Returns the built app

    :return: function
        The app
    """
    return _utils.build_app(_utils.caller())


def run(host='127.0.0.1', port=5000, debug=False, module_name=None):
    """
    Runs the app

    :param host: str
        IP Address where the server serves
        '0.0.0.0' for public address
    :param port: int
    :param debug: bool
        Enables debug output and hot reload
    :param module_name: str
        Starts the app from the specific module if given
    """
    module = _utils.caller()
    state = _utils.state(module)
    state.debug = debug
    module = module_name if module_name else _utils.caller()
    if debug and module != '__main__':
        print('Warning: Please do not run apps outside of main')
    run_simple(host, port, _utils.build_app(module), use_debugger=debug, use_reloader=debug, ssl_context=state.ssl)
