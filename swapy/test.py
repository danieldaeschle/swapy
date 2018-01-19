from werkzeug.serving import make_server
import threading
import os

os.environ['NO_PROXY'] = '127.0.0.1'

url = 'http://127.0.0.1:5000/'


class ServerThread(threading.Thread):

    def __init__(self, app):
        threading.Thread.__init__(self)
        self.daemon = True
        self.srv = make_server('127.0.0.1', 5000, app)

    def run(self):
        self.srv.serve_forever()


def run_test(app):
    server = ServerThread(app)
    server.start()
    return server
