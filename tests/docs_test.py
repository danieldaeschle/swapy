import sys
import os
# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))
import swapy
from swapy.ext import api_docs
from swapy.testing import client
from swapy.middlewares import JsonMiddleware

api_docs.init()


@swapy.on('test')
def test():
    """HI :)"""
    return 'Hi!'


@swapy.on_get('another/<int:id>')
def another(req):
    """Just another test"""
    print(req.headers)
    return str(req.url_args)


@swapy.on('json')
@JsonMiddleware
def json(req):
    return req.json


c = client(swapy.app())


if __name__ == '__main__':
    swapy.run(debug=True)


def test_works():
    r = c.get('docs')
    assert 'HI :)' in r.data.decode()
