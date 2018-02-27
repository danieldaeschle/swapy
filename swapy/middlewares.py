import json
from werkzeug.exceptions import HTTPException, abort
from .wrappers import response_from


def json_exception(error):
    """
    Exception middleware which returns the error as JSON string
    -> {"message": error, "status_code": code}
    
    :param error: Exception
        The exception object
    :return: str
    """
    if isinstance(error, HTTPException):
        return json.dumps({'message': str(error), 'status_code': error.code}, indent=4), error.code
    else:
        return json.dumps({'message': str(error), 'status_code': 500}, indent=4), 500


def default_exception(error):
    """
    Default exception middleware
    
    :param error: Exception
        The Exception object
    :return: str
    """
    if isinstance(error, HTTPException):
        if error.code == 404:
            return '404 Not Found', error.code
        return str(error), error.code
    else:
        return str(error), 500


def json_middleware(f):
    """
    Returns every output from an route which has the JSON middleware to a JSON string
    
    :param f: function
        The route
    :return: function
    """
    def handle(*args, **kwargs):
        result = f(*args, **kwargs)
        response = response_from(result)
        try:
            response.content = json.dumps(response.content, indent=4)
        except TypeError:
            return response
        response.headers['Content-Type'] = 'application/json'
        return response
    return handle


def html_middleware(f):
    """
    Appends a 'text/html' Content-Type header to each response from a route

    :param f: function
    :return: function
    """
    def handle(*args, **kwargs):
        result = f(*args, **kwargs)
        response = response_from(result)
        response.headers['Content-Type'] = 'text/html'
        return response
    return handle


def cors_middleware(f):
    """
    Appends CORS headers to each response from a route

    :param f: function
    :return: function
    """
    def handle(req):
        result = f(req)
        response = response_from(result)
        if req.method == 'OPTIONS':
            return '200 OK', 200, {'Content-Type': 'text/plain'}
        else:
            response.headers['Content-Type'] = 'text/html'
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, PUT, POST, DELETE, HEAD, PATCH, OPTIONS'
            response.headers['Access-Control-Expose-Headers'] = '*'
        return response
    return handle


def expect_keys_middleware(f):
    """
    Returns a 400 error to the client if the route function tries to get a key from an object and cause a KeyError

    :param f: function
    :return: function
    """
    def handle(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except KeyError:
            result = None
            abort(400)
        return response_from(result)
    return handle


# Aliases for the function in camel case
JsonException = json_exception
DefaultException = default_exception
JsonMiddleware = json_middleware
HtmlMiddleware = html_middleware
CorsMiddleware = cors_middleware
ExpectKeysMiddleware = expect_keys_middleware
