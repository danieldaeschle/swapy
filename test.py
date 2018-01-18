from sapy import on_get, run, include, use, on, error, file, redirect, on_post, favicon, ssl, config
from sapy.middlewares import JsonMiddleware, JsonException, HtmlMiddleware
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
    'use': JsonMiddleware,
    'favicon': 'favicon.png',
    'include': another
})


@on_get()
def root():
    return 'Hello Sapify! :)', 200, {}


@on_get('/create')
def create(req):
    print(req.form['test'])
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return 'Test'


@on_get('/redirect')
def redirect():
    return redirect('https://google.de')


@on_get('/file')
def file():
    return file('test.py')


@on_get('/error')
def error():
    return object


@on_get('/error2')
def error():
    raise TypeError('lol')


@on_get('json')
def json():
    return {'message': 'hi'}


# @on('/*')
# def not_found(req):
#     return {'message': 'Endpoint \'{}\' doesn\'t exists'.format(req.path)}, 404

if __name__ == '__main__':
    run(debug=True)
