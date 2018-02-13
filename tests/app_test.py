import sys
import os
import sqlite3
import app_another
import json
# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))
from swapy import on_get, run, file, redirect, config, app, on_post, on_put, render
from swapy.middlewares import JsonMiddleware, JsonException, ExpectKeysMiddleware, HtmlMiddleware
from swapy.wrappers import Response
from swapy.testing import client

conn = sqlite3.connect(':memory:', check_same_thread=False)
# ssl('127.0.0.1')
# error(JsonException)
# use(JsonMiddleware)
# favicon('myFile.png')
# include(another, prefix='/v1')
config({
    'error': JsonException,
    'include': app_another,
    'shared': True
})


@on_get()
def root():
    return 'Hello Swapy! :)', 200, {}


@on_put()
@ExpectKeysMiddleware
def ret_put(req):
    name = req.json['name']
    return name


@on_post('/create')
@ExpectKeysMiddleware
def create(req):
    return req.form['test']


@on_get('db')
def database():
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return 'true'


@on_get('/redirect')
def redirect_to_google():
    """Redirects to Google"""
    return redirect('https://google.de')


@on_get('/app-file')
def app_file():
    return file('test/app_test.py')


@on_get('file-json')
@JsonMiddleware
def file_json():
    return file('test/app_test.py')


@on_get('/error')
def error():
    return object


@on_get('/error2')
def error():
    raise TypeError('lol')


@on_get('json')
@JsonMiddleware
def get_json():
    return {'message': 'hi'}


@on_get('html')
@HtmlMiddleware
def html():
    return render('shared/index.html', text='Hello swapy!')


@on_get('set_session')
def session(req):
    req.session['key'] = 'value'
    return '', 200


@on_get('get_session')
def session(req):
    val = req.session.get('key')
    return val


@on_get('set_cookie')
def cookie():
    res = Response()
    res.set_cookies({'key': 'value'})
    return res


@on_get('get_cookie')
def cookie(req):
    return req.cookies.get('key')


c = client(app())


def test_app_file():
    r = c.get('app-file')
    assert r.headers['Content-Disposition'] == 'attachment;filename=app_test.py'


def test_app_file_json():
    r = c.get('file-json')
    assert r.headers['Content-Disposition'] == 'attachment;filename=app_test.py'


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


if __name__ == '__main__':
    run(debug=True)
