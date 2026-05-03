from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from .extensions import db, login_manager, migrate
from .models import User


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{Path(app.instance_path) / 'easy_social.sqlite'}",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(Path(app.root_path) / "static" / "uploads"),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    from .auth import bp as auth_bp
    from .social import bp as social_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(social_bp)

    @app.cli.command("init-db")
    def init_db_command() -> None:
        db.create_all()
        print("Initialized the database.")

    return app

