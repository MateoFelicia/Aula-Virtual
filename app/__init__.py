# app/__init__.py
from flask import Flask, redirect, url_for
from app.config import config
from app.extensions import db, login_manager, migrate


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.modules.auth import auth_bp
    from app.modules.courses import courses_bp
    from app.modules.content import content_bp
    from app.modules.evaluations import evaluations_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(evaluations_bp)

    @app.route('/')
    def index():
        return redirect(url_for('courses.index'))

    return app