from app_test import application
from waitress import serve

if __name__ == '__main__':
    serve(application, host='127.0.0.1', port=2000)
