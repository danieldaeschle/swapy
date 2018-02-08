import sys
import os
import app
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')
# noinspection PyUnresolvedReferences
from swapy.testing import client

c = client(app.application)


def test_app_file():
    r = c.get('app-file')
    assert r.headers['Content-Disposition'] == 'attachment;filename=app.py'


def test_app_file_json():
    r = c.get('file-json')
    assert r.headers['Content-Disposition'] == 'attachment;filename=app.py'


def test_app_shared_file():
    r = c.get('shared/myFile.png')
    assert r.status_code == 200


def test_get():
    r = c.get('')
    assert r.data == b'Hello Swapy! :)'


def test_code():
    r = c.get('')
    assert r.status_code == 200


def test_post():
    r = c.get('')
    assert r.status_code == 200


def test_put():
    r = c.put('', data=json.dumps({'name': 'Daniel'}), headers={'Content-Type': 'application/json'})
    assert r.data == b'Daniel'


def test_delete():
    r = c.get('')
    assert r.status_code == 200


def test_form_keys_error():
    r = c.post('create')
    assert r.status_code == 400


def test_error():
    r = c.get('error')
    assert r.status_code == 500


def test_form_code():
    r = c.post('create', data={'test': 'something'})
    assert r.status_code == 200


def test_content():
    r = c.post('create', data={'test': 'something'})
    assert r.data == b'something'


def test_json():
    r = c.get('json')
    assert json.loads(r.data.decode())['message'] == 'hi'


def test_json_header():
    r = c.get('json')
    assert r.headers['Content-Type'] == 'application/json'


def test_sqlite():
    r = c.get('db')
    assert r.data == b'true'


def test_html_header():
    r = c.get('html')
    assert r.headers['Content-Type'] == 'text/html'


def test_html_render():
    r = c.get('html')
    assert b'Hello swapy!' in r.data


def test_not_found():
    r = c.get('something')
    assert r.status_code == 404


def test_another():
    r = c.get('test')
    assert r.status_code == 200


def test_session():
    c.get('set_session')
    r = c.get('get_session')
    assert r.data == b'value'


def test_cookies():
    c.get('set_cookie')
    r = c.get('get_cookie')
    assert r.data == b'value'
