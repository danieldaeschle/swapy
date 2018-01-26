import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')

# noinspection PyUnresolvedReferences
from swapy.test import client
import unittest
import app
import json

# run_test(app.application)
c = client(app.application)


class TestFile(unittest.TestCase):

    def test_app_file(self):
        r = c.get('app-file')
        self.assertEqual(r.headers['Content-Disposition'], 'attachment;filename=app.py')

    def test_app_shared_file(self):
        r = c.get('shared/myFile.png')
        self.assertEqual(r.status_code, 200)


class TestWorking(unittest.TestCase):

    def test_get(self):
        r = c.get('')
        self.assertEqual(r.data, b'Hello Swapy! :)')

    def test_code(self):
        r = c.get('')
        self.assertEqual(r.status_code, 200)

    def test_post(self):
        r = c.get('')
        self.assertEqual(r.status_code, 200)

    def test_put(self):
        r = c.put('', data=json.dumps({'name': 'Daniel'}), headers={'Content-Type': 'application/json'})
        self.assertEqual(r.data, b'Daniel')

    def test_delete(self):
        r = c.get('')
        self.assertEqual(r.status_code, 200)


class TestExceptKeyMiddleware(unittest.TestCase):

    def test_form_keys_error(self):
        r = c.post('create')
        self.assertEqual(r.status_code, 400)

    def test_form_code(self):
        r = c.post('create', data={'test': 'something'})
        self.assertEqual(r.status_code, 200)

    def test_content(self):
        r = c.post('create', data={'test': 'something'})
        self.assertEqual(r.data, b'something')


class TestJsonMiddleware(unittest.TestCase):

    def test_json(self):
        r = c.get('json')
        self.assertEqual(json.loads(r.data.decode())['message'], 'hi')

    def test_header(self):
        r = c.get('json')
        self.assertEqual(r.headers['Content-Type'], 'application/json')


class TestDatabaseWorking(unittest.TestCase):

    def test_sqlite(self):
        r = c.get('db')
        self.assertEqual(r.data, b'true')


class TestHtmlMiddleware(unittest.TestCase):

    def test_header(self):
        r = c.get('html')
        self.assertEqual(r.headers['Content-Type'], 'text/html')


if __name__ == '__main__':
    unittest.main()
