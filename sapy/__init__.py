from flask import Flask, request as f_req, jsonify
from werkzeug.exceptions import HTTPException
import inspect
from .request import Request
import uuid

_app = None
_routes = {}
_decorators = {}
_on_error = None


def _caller():
    return inspect.currentframe().f_back.f_back.f_globals['__name__']


def _init(name):
    global _app, _routes, _decorators
    if not _app:
        _app = Flask(__name__)
        for cls in HTTPException.__subclasses__():
            _app.register_error_handler(cls, _error)
    if not name in _routes:
        _routes[name] = []
    if not name in _decorators:
        _decorators[name] = []


def _error(error):
    global _on_error
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    if _on_error:
        return _on_error(error, code)
    return str(error), code


def _register_route(url='/', methods=['GET', 'POST', 'PUT', 'DELETE']):
    global _routes, _decorators
    if not url.startswith('/'):
        url = '/{}'.format(url)
    def decorator(f):
        decorators = _decorators[_caller()]
        def handle():
            r = Request(
                f_req.method, f_req.headers, f_req.data,
                f_req.cookies, f_req.remote_addr,
                f_req.args, f_req.files, f_req.form,
                f_req.url
            )
            try:
                res = f(r)
            except TypeError:
                res = f()
            if res:
                def use_decorators(output):
                    for deco in decorators:
                        output = deco(output)
                    return output

                if res is tuple:
                    return use_decorators(res[0]) if res else None, res[1] if len(res) > 1 else None, res[2] if len(res) > 2 else None
                else:
                    return use_decorators(res)
            else:
                return ''
        handle.__name__ = str(uuid.uuid4())
        _routes[_caller()].append([url, methods, handle])
        return f
    return decorator


def on(url='/', methods=['GET', 'POST', 'PUT', 'DELETE']):
    _init(_caller())
    return _register_route(url, methods)


def on_get(url='/'):
    _init(_caller())
    return _register_route(url, methods=['GET'])


def on_post(url='/'):
    _init(_caller())
    return _register_route(url, methods=['POST'])


def on_put(url='/'):
    _init(_caller())
    return _register_route(url, methods=['PUT'])


def on_delete(url='/'):
    _init(_caller())
    return _register_route(url, methods=['DELETE'])


def include(module, prefix=''):
    global _routes
    _init(_caller())
    _init(module.__name__)
    if not prefix.startswith('/') and len(prefix) >= 1:
        prefix = '/{}'.format(prefix)
    if prefix == '/':
        prefix = ''
    routes = _routes[module.__name__]
    for route in routes:
        route[0] = '{}{}'.format(prefix, route[0])
        _routes[_caller()].append(route)


def use(decorator):
    global _decorators
    _init(_caller())
    if callable(decorator):
        _decorators[_caller()].append(decorator)


def on_error(f):
    global _on_error
    res = f()
    if callable(res):
        _on_error = res
    else:
        raise Exception('{} is not a function'.format(f.__name__))


def app(name):
    global _app, _routes
    _init(name)
    routes = _routes[name]
    for url, methods, f in routes:
        _app.add_url_rule(url, methods=methods, view_func=f)
    return _app


def run(host='127.0.0.1', port=5000, debug=False, **options):
    app(_caller()).run(host, port, debug, **options)
