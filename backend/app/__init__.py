"""Application tier: Flask REST API for the photo-sharing system."""
from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .config import Config
from .extensions import db, jwt
from .storage import init_storage
from .utils import ApiError, error_response


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    init_storage(app)

    from .routes import auth, comments, groups, health, photos

    for module in (auth, groups, photos, comments, health):
        app.register_blueprint(module.bp)

    _register_error_handlers(app)

    with app.app_context():
        db.create_all()  # creates tables if they do not exist yet
        # Close connections opened above, so each Gunicorn worker starts
        # with its own fresh connection pool (safe with --preload).
        db.engine.dispose()

    return app


def _register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return error_response(err.message, err.status)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        if err.code == 413:
            return error_response("File is too large", 413)
        return error_response(err.description or err.name, err.code)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception(err)
        db.session.rollback()
        return error_response("Internal server error", 500)

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_response("Login required", 401)

    @jwt.invalid_token_loader
    def bad_token(reason):
        return error_response("Invalid token", 401)

    @jwt.expired_token_loader
    def expired_token(header, payload):
        return error_response("Session expired, please log in again", 401)
