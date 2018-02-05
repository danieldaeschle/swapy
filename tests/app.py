import sys
import os
import sqlite3
import another
# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))
from swapy import on_get, run, file, redirect, config, app, on_post, on_put, render, get_env, environment
from swapy.middlewares import JsonMiddleware, JsonException, ExpectKeysMiddleware, HtmlMiddleware
from swapy.wrappers import Response

conn = sqlite3.connect(':memory:', check_same_thread=False)
# ssl('127.0.0.1')
# error(JsonException)
# use(JsonMiddleware)
# favicon('myFile.png')
# include(another, prefix='/v1')
config({
    'error': JsonException,
    'include': another,
    'shared': True
})
environment({
    'production': {
        'secret_key': 'secret'
    },
    'development': {
        'secret_key': 'not_secret'
    }
})



@on_get()
def root():
    return 'Hello Swapy! :)', 200, {}


@on_put()
@ExpectKeysMiddleware
def put(req):
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
def redirect():
    """Redirects to Google"""
    return redirect('https://google.de')


@on_get('/app-file')
def app_file():
    return file('test/app.py')


@on_get('file-json')
@JsonMiddleware
def file_json():
    return file('test/app.py')


@on_get('/error')
def error():
    return object


@on_get('/error2')
def error():
    raise TypeError('lol')


@on_get('json')
@JsonMiddleware
def json():
    return {'message': 'hi'}


@on_get('html')
@HtmlMiddleware
def html():
    return render('shared/index.html', text='Hello swapy!')


@on_get('checkSecretKey')
def env():
    return get_env('secret_key')


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


@on_get('set_secure_cookie')
def secure_cookie(req):
    req.secure_cookie['key'] = 'value'


@on_get('get_secure_cookie')
def secure_cookie(req):
    return req.secure_cookie.get('key')


if __name__ == '__main__':
    run(debug=True)

application = app()
