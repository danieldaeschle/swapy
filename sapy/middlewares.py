import json
from werkzeug.exceptions import HTTPException, abort


def _json_exception(error):
    if isinstance(error, HTTPException):
        return json.dumps({'message': str(error), 'status_code': error.code}, indent=4), error.code
    else:
        return json.dumps({'message': str(error), 'status_code': 500}, indent=4), 500


def _exception_middleware(error):
    return error


def _json_middleware(f):
    def handle(*args, **kwargs):
        try:
            result = f(*args, **kwargs)  # Returns -> content[, status_code][, headers]
        except KeyError:
            result = None
            abort(400)
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


def _html_middleware(f):
    def handle(*args, **kwargs):
        result = f(*args, **kwargs)
        if type(result) == tuple:
            body = result[0]
            code = result[1] if len(result) > 1 else 200
            headers = result[2] if len(result) > 2 else {}
            headers['Content-Type'] = 'text/html'
            return body, code, headers
        return result, 200, {'Content-Type': 'text/html'}
    return handle


JsonException = _json_exception
JsonMiddleware = _json_middleware

HtmlMiddleware = _html_middleware
ExceptionMiddleware = _exception_middleware
