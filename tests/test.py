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

    def test_content(self):
        r = requests.get(url)
        assert r.content.decode() == 'Hello Swapy! :)'

    def test_code(self):
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


if __name__ == '__main__':
    unittest.main()

