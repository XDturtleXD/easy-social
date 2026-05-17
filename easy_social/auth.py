from __future__ import annotations

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .captcha import (
    CAPTCHA_SESSION_KEY,
    captcha_answer_matches,
    captcha_svg,
    generate_captcha_code,
)
from .extensions import db
from .models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/captcha.svg")
def captcha_image():
    code = current_app.config.get("CAPTCHA_TEST_CODE") or generate_captcha_code(
        current_app.config["CAPTCHA_LENGTH"]
    )
    session[CAPTCHA_SESSION_KEY] = code
    response = Response(captcha_svg(code), mimetype="image/svg+xml")
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("social.feed"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        captcha_answer = request.form.get("captcha_answer", "")

        error = None
        if not username or not email or not password:
            error = "Username, email, and password are required."
        elif not captcha_answer_matches(session.get(CAPTCHA_SESSION_KEY), captcha_answer):
            error = "Please complete the CAPTCHA challenge."
        elif len(username) > 40:
            error = "Username must be 40 characters or fewer."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(email=email).first():
            error = "That email is already registered."

        if error:
            flash(error, "error")
        else:
            session.pop(CAPTCHA_SESSION_KEY, None)
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("social.feed"))

    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("social.feed"))

    if request.method == "POST":
        username_or_email = request.form.get("username_or_email", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(
            (User.username == username_or_email)
            | (User.email == username_or_email.lower())
        ).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("social.feed"))

        flash("Invalid username/email or password.", "error")

    return render_template("auth/login.html")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

