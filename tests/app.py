import sys
import os
sys.path.append(os.path.abspath('../'))

# noinspection PyUnresolvedReferences
from swapy import on_get, run, file, redirect, config, app, on_post, use
# noinspection PyUnresolvedReferences
from swapy.middlewares import JsonMiddleware, JsonException, ExpectKeysMiddleware, HtmlMiddleware
import another
import sqlite3
conn = sqlite3.connect(':memory:', check_same_thread=False)

# ssl('127.0.0.1')
# error(JsonException)
# use(JsonMiddleware)
# favicon('favicon.png')
# include(another, prefix='/v1')
config({
    'error': JsonException,
    'favicon': 'favicon.png',
    'include': another
})


@on_get()
def root():
    return 'Hello Swapy! :)', 200, {}


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


@on_get('/file')
def app_file():
    return file('app.py')


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
    return 'Hello World!'


# @on('/*')
# def not_found(req):
#     return {'message': 'Endpoint \'{}\' doesn\'t exists'.format(req.path)}, 404

if __name__ == '__main__':
    run(debug=True)

application = app()
