import json
from werkzeug.exceptions import HTTPException, abort


def json_exception(error):
    """
    Exception middleware which returns the error as JSOn string
    -> {"message": error, "status_code": code}
    
    :param error: Exception
        The Exception object
    :return: str
    """
    if isinstance(error, HTTPException):
        return json.dumps({'message': str(error), 'status_code': error.code}, indent=4), error.code
    else:
        return json.dumps({'message': str(error), 'status_code': 500}, indent=4), 500


def exception_middleware(error):
    """
    Default exception middleware
    
    :param error: Exception
        The Exception object
    :return: Exception
        Will be converted to a string from the server
    """
    return error


def json_middleware(f):
    """
    Returns every output from an route which has the JSON middleware to a JSON string
    Use it with:
        @json_middleware
        ...
    Or:
        use(json_middleware)
    
    :param f: callable
        The route
    :return: callable
    """
    def handle(*args, **kwargs):
        result = f(*args, **kwargs)  # Returns -> content[, status_code][, headers]
        code = 200
        headers = {}
        if type(result) == tuple:
            res = result[0]
            code = result[1] if len(result) > 1 else None
            headers = result[2] if len(result) > 2 else {}
        else:
            res = result
        try:
            headers['Content-Type'] = 'application/json'
            return json.dumps(res, indent=4), code, headers
        except TypeError:
            return result
    return handle


def html_middleware(f):
    """
    Appends a 'text/html' Content-Type header to each response from a route

    :param f: callable
    :return: callable
    """
    def handle(*args, **kwargs):
        result = f(*args, **kwargs)
        if isinstance(result, tuple):
            body = result[0]
            code = result[1] if len(result) > 1 else 200
            headers = result[2] if len(result) > 2 else {}
            headers['Content-Type'] = 'text/html'
            return body, code, headers
        return result, 200, {'Content-Type': 'text/html'}
    return handle


def cors_middleware(f):
    """
    Appends CORS headers to each response from a route

    :param f: callable
    :return: callable
    """
    def handle(*args, **kwargs):
        req = kwargs['req']
        result = f(*args, **kwargs)
        if req.method == 'OPTIONS':
            return '200 OK', 200, {'Content-Type': 'text/plain'}
        if isinstance(result, tuple):
            body = result[0]
            code = result[1] if len(result) > 1 else 200
            headers = result[2] if len(result) > 2 else {}
            headers['Content-Type'] = 'text/html'
            headers['Access-Control-Allow-Origin'] = '*'
            headers['Access-Control-Allow-Headers'] = '*'
            headers['Access-Control-Allow-Credentials'] = 'true'
            headers['Access-Control-Allow-Methods'] = 'GET, PUT, POST, DELETE, HEAD, PATCH, OPTIONS'
            headers['Access-Control-Expose-Headers'] = '*'
            return body, code, headers
        return result
    return handle


def expect_keys_middleware(f):
    """
    Returns a 400 error to the client if the route function tries to get a key from an object and cause a KeyError

    :param f: callable
    :return: callable
    """
    def handle(*args, **kwargs):
        try:
            res = f(*args, **kwargs)
        except KeyError:
            res = None
            abort(400)
        return res
    return handle


JsonException = json_exception
JsonMiddleware = json_middleware
HtmlMiddleware = html_middleware
ExceptionMiddleware = exception_middleware
CorsMiddleware = cors_middleware
ExpectKeysMiddleware = expect_keys_middleware
