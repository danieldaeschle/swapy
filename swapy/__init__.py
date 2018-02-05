import os
import mimetypes

from werkzeug.serving import run_simple
from werkzeug.wsgi import FileWrapper
from werkzeug.urls import iri_to_uri
from werkzeug.utils import escape

from jinja2 import FileSystemLoader
from jinja2.environment import Environment

from . import utils


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
    module = utils.caller_frame()
    path = os.path.dirname(os.path.realpath(module.f_globals['__file__']))
    env = Environment()
    env.loader = FileSystemLoader(path)
    template = env.get_template(file_path)
    return template.render(kwargs)


def redirect(location, code=301):
    """
    Returns a redirect WResponse

    :param location: str
        Url where the user should be redirect
        Example: https://github.com
    :param code: int
        HTTP code which the server returns to the client
        It should be any 3xx code
        See more at Wikipedia - Http Status Codes
        Default = 301
    :return: (str, int, dict)
        Redirect WResponse
    """
    location = iri_to_uri(location, safe_conversion=True)
    response = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n' \
               '<title>Redirecting...</title>\n' \
               '<h1>Redirecting...</h1>\n' \
               '<p>You should be redirected automatically to target URL: ' \
               '<a href="{}">{}</a>.  If not click the link.'.format(escape(location), escape(location))
    return response, code, {'Location': location, 'Content-Type': 'text/html'}


def file(path, name=None):
    """
    Returns a file WResponse

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
        path = os.path.abspath(utils.caller_frame().f_globals['__file__'])
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
    utils.favicon(utils.caller(), path)


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
    module = utils.caller()
    utils.environment(module, data)


def get_env(key):
    """
    Returns the value of the give key in environment variables

    :param key: str
    :return: any
    """
    state = utils.state(utils.caller())
    return state.environment.get(key)


def set_env(key, value, runtime=None):
    """
    Sets a value for a key in the global environment

    :param key: str
    :param value: any
    :param runtime: str
        It is None, "development" or "production"
    """
    state = utils.state(utils.caller())
    state.environment.set(key, value, runtime)


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
    utils.ssl(utils.caller(), host, path)


def error(f):
    """
    Registers a function as error handler

    :param f: callable
        Callable should receive an Exception object as parameter
    """
    utils.error(utils.caller(), f)


def shared(directory):
    """
    Registers a directory as shared

    :param directory: str
        Path to the directory
    """
    module = utils.caller_frame()
    utils.shared(module, directory)


def not_found(f):
    """
    Registers a function as 404 error handler

    :param f: callable
        Callable should receive an Exception object as parameter
    """
    utils.not_found(utils.caller(), f)


def on(url='/', methods=('GET', 'POST', 'PUT', 'DELETE')):
    """
    Route registerer for all http methods

    :param url: str
    :param methods: list | tuple
        HTTP method
        Default = ('GET', 'POST', 'PUT', 'DELETE')
    :return: callable
    """
    return utils.register_route(utils.caller(), url, methods)


def on_get(url='/'):
    """
    Route registerer for GET http method

    :param url: str
    :return: callable
    """
    return utils.register_route(utils.caller(), url, methods=['GET'])


def on_post(url='/'):
    """
    Route registerer for POST http method

    :param url: str
    :return: callable
    """
    return utils.register_route(utils.caller(), url, methods=['POST'])


def on_put(url='/'):
    """
    Route registerer for PUT http method

    :param url: str
    :return: callable
    """
    return utils.register_route(utils.caller(), url, methods=['PUT'])


def on_delete(url='/'):
    """
    Route registerer for DELETE http method

    :param url: str
    :return: callable
    """
    return utils.register_route(utils.caller(), url, methods=['DELETE'])


def include(module, prefix=''):
    """
    Includes a source module into the target module

    :param module: str
        Name of the source module
    :param prefix: str
        Routes from the source module will get the prefix in front of their route
        Default = ''
    """
    utils.include(utils.caller(), module, prefix)


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
    module = utils.caller()
    if isinstance(cfg, dict):
        if cfg.get('use'):
            middlewares_ = cfg['use']
            if isinstance(middlewares_, (tuple, list)):
                utils.use(module, *middlewares_)
            else:
                utils.use(module, middlewares_)
        if cfg.get('include'):
            modules_ = cfg['include']

            def handle(args):
                if isinstance(args, (tuple, list)):
                    utils.include(module, *args)
                else:
                    utils.include(module, args)

            if isinstance(modules_, list):
                for target in modules_:
                    handle(target)
            else:
                handle(modules_)
        if cfg.get('error'):
            utils.error(module, cfg['error'])
        if cfg.get('ssl'):
            ssl_ = cfg['ssl']
            if isinstance(ssl_, (tuple, list)):
                utils.ssl(module, *ssl_)
            else:
                utils.ssl(module, ssl_)
        if cfg.get('favicon'):
            utils.favicon(module, cfg['favicon'])
        if cfg.get('not_found'):
            utils.not_found(module, cfg['not_found'])
        if cfg.get('shared'):
            utils.shared(utils.caller_frame(), cfg['shared'])
        if cfg.get('environment'):
            utils.environment(module, cfg['environment'])
    else:
        raise TypeError('Type {} is not supported as config. Please use a dict.'.format(type(cfg)))


def use(*middlewares_):
    """
    Registers middlewares for global use

    :param middlewares_: callable[]
         Arguments of decorators / middlewares
    """
    utils.use(utils.caller(), *middlewares_)


def app():
    """
    Returns the built app

    :return: callable
        The app
    """
    return utils.build_app(utils.caller())


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
    module = utils.caller()
    state = utils.state(module)
    state.debug = debug
    module = module_name if module_name else utils.caller()
    if debug and module != '__main__':
        print('Warning: Please do not run apps outside of main')
    run_simple(host, port, utils.build_app(module), use_debugger=debug, use_reloader=debug, ssl_context=state.ssl)
