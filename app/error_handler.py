from flask import current_app, Flask
from werkzeug.exceptions import HTTPException

from app.utils import jsonify

DEFAULT_MESSAGE = (
    'Oops! An error happened. We are already ' 'trying to resolve the problem!'
)


def jsonify_http_exception(e: HTTPException):
    """Convert raised werkzeug.exceptons.* into JSON.

    Additional doc: http://flask.pocoo.org/snippets/83/
    """
    return jsonify(e.description, e.code)


def jsonify_unknown_exception(e: Exception):
    """Convert any other exception to JSON."""
    current_app.logger.exception('Unhandled exception has been raised!')
    return jsonify(DEFAULT_MESSAGE, 500)


def register_error_handlers(app: Flask):
    """Set an error handler for each kind of exception."""
    app.errorhandler(HTTPException)(jsonify_http_exception)

    # Don't jsonify an exception in dev mode
    if not app.debug:
        app.errorhandler(Exception)(jsonify_unknown_exception)
