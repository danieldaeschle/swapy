import json
from werkzeug.exceptions import HTTPException


def _json_exception(error):
    if isinstance(error, HTTPException):
        return json.dumps({'message': str(error), 'status_code': error.code}, indent=4), error.code
    return error


def _exception_middleware(error):
    return error


def _json_middleware(f):
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


JsonException = _json_exception
JsonMiddleware = _json_middleware
ExceptionMiddleware = _exception_middleware
