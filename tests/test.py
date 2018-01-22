import sys
import os
sys.path.append(os.path.abspath('../'))

# noinspection PyUnresolvedReferences
from swapy.test import run_test, url
import requests
import unittest
import app

run_test(app.application)


class TestWorking(unittest.TestCase):

    def test_get(self):
        r = requests.get(url)
        assert r.content.decode() == 'Hello Swapy! :)'

    def test_code(self):
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)

    def test_post(self):
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)

    def test_put(self):
        r = requests.put(url, json={'name': 'Daniel'})
        self.assertEqual(r.content.decode(), 'Daniel')

    def test_delete(self):
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)


class TestExceptKeyMiddleware(unittest.TestCase):

    def test_form_keys_error(self):
        r = requests.post(url + 'create')
        self.assertEqual(r.status_code, 400)

    def test_form_code(self):
        r = requests.post(url + 'create', data={'test': 'something'})
        self.assertEqual(r.status_code, 200)

    def test_content(self):
        r = requests.post(url + 'create', data={'test': 'something'})
        self.assertEqual(r.content.decode(), 'something')


class TestJsonMiddleware(unittest.TestCase):

    def test_json(self):
        r = requests.get(url + 'json')
        self.assertEqual(r.json()['message'], 'hi')

    def test_header(self):
        r = requests.get(url + 'json')
        self.assertEqual(r.headers['Content-Type'], 'application/json')


class TestDatabaseWorking(unittest.TestCase):

    def test_sqlite(self):
        r = requests.get(url + 'db')
        self.assertEqual(r.content.decode(), 'true')


class TestHtmlMiddleware(unittest.TestCase):

    def test_header(self):
        r = requests.get(url + 'html')
        self.assertEqual(r.headers['Content-Type'], 'text/html')


class TestFile(unittest.TestCase):

    def test_app_file(self):
        r = requests.get(url + 'file')
        self.assertEqual(r.headers['Content-Disposition'], 'attachment;filename=app.py')


if __name__ == '__main__':
    unittest.main()
