import sys
import os
import json
# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))
import swapy
from swapy.middlewares import JsonMiddleware
from swapy.testing import client

swapy.use(JsonMiddleware)


@swapy.on_get('json')
def get_json():
    return {'message': 'hi'}


@swapy.on_get('file-json')
def file_json():
    file = swapy.file('app_test.py')
    return file


@swapy.on('json-list')
def test_list():
    return [1, 2]


@swapy.on('routes')
def ret_routes():
    return swapy.routes()


if __name__ == '__main__':
    swapy.run(debug=True)

c = client(swapy.app())


def test_json_header():
    r = c.get('json')
    assert r.headers['Content-Type'] == 'application/json'


def test_json():
    r = c.get('json')
    assert json.loads(r.data.decode())['message'] == 'hi'


def test_app_file_json():
    r = c.get('file-json')
    assert r.headers['Content-Disposition'] == 'attachment;filename=app_test.py'


def test_json_list():
    r = c.get('json-list')
    assert json.loads(r.data.decode()) == [1, 2]
