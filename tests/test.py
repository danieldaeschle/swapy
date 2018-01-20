import sys
import os
sys.path.append(os.path.abspath('../'))

# noinspection PyUnresolvedReferences
import app
from swapy.test import run_test, url
import requests
import unittest

run_test(app.application)


class TestWorking(unittest.TestCase):

    def test_get(self):
        r = requests.get(url)
        assert r.content.decode() == 'Hello Swapy! :)'

    def test_code(self):
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)

    def test_post(self):
        pass

    def test_put(self):
        pass

    def test_delete(self):
        pass


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


class TestFiles(unittest.TestCase):

    def test_app_file(self):
        r = requests.get(url + 'file')
        self.assertEqual(r.headers['Content-Disposition'], 'attachment;filename=app.py')


class TestErrors(unittest.TestCase):
    pass


class TestRedirect(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()

