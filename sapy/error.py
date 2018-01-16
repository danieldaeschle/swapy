from flask import jsonify


def json_catch():
    def handle(error, code):
        return jsonify({'message': str(error), 'status_code': code})
    return handle
