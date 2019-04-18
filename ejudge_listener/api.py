from flask import jsonify as flask_jsonify, current_app, Flask
from werkzeug.exceptions import HTTPException


def jsonify(data, status_code=200):
    response = {'status_code': status_code}
    if status_code in (200, 201):
        response['data'] = data
        response['status'] = 'success'
    else:
        response['error'] = data
        response['status'] = 'error'

    return flask_jsonify(response), status_code


DEFAULT_MESSAGE = (
    'Oops! An error happened. We are already trying to resolve the problem!'
)


def jsonify_http_exception(e: Exception):
    """Convert raised werkzeug.exceptions.* into JSON.

    Additional doc: http://flask.pocoo.org/snippets/83/
    """
    if isinstance(e, HTTPException):
        return jsonify(e.description, e.code)

    return jsonify_unknown_exception(e)


def jsonify_unknown_exception(_: Exception):
    """Convert any other exception to JSON."""
    current_app.logger.exception('Unhandled exception has been raised!')
    return jsonify(DEFAULT_MESSAGE, 500)


def register_error_handlers(app: Flask):
    """Set an error handler for each kind of exception."""
    app.errorhandler(HTTPException)(jsonify_http_exception)
