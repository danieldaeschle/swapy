import sys
import os
sys.path.append(os.path.abspath('../'))

import app
from swapy.test import run_test, url
import requests
import os

run_test(app.application)


def test_working():
    r = requests.get(url)
    assert r.content.decode() == '"Hello Swapy! :)"'


def test_code():
    r = requests.get(url)
    assert r.status_code == 200


def test_db():
    r = requests.get(url + 'db')
    assert r.content.decode() == 'true'


def test_form_keys_error():
    r = requests.post(url + 'create')
    assert r.status_code == 400


def test_form_keys():
    r = requests.post(url + 'create', data={'test': 'something'})
    assert r.status_code == 200 and r.content.decode() == '"something"'


def test_json():
    r = requests.get(url + 'json')
    assert r.json()['message'] == 'hi' and r.headers['Content-Type'] == 'application/json'


if __name__ == '__main__':
    test_working()
    test_code()
    test_db()
    test_form_keys_error()
    test_form_keys()
    test_json()

