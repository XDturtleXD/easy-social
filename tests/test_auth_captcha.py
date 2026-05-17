from __future__ import annotations

import pytest

from easy_social.models import User

pytestmark = pytest.mark.integration


def test_register_page_includes_captcha_challenge(client):
    response = client.get("/auth/register")

    assert response.status_code == 200
    assert b"/auth/captcha.svg" in response.data
    assert b'name="captcha_answer"' in response.data


def test_captcha_image_sets_no_store_header(client):
    response = client.get("/auth/captcha.svg")

    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"
    assert response.headers["Cache-Control"] == "no-store, max-age=0"


def test_registration_rejects_missing_captcha(client, app):
    response = client.post(
        "/auth/register",
        data={
            "username": "bot",
            "email": "bot@example.com",
            "password": "password",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please complete the CAPTCHA challenge." in response.data
    with app.app_context():
        assert User.query.filter_by(username="bot").first() is None


def test_registration_rejects_wrong_captcha_after_challenge_loaded(client, app):
    client.get("/auth/captcha.svg")

    response = client.post(
        "/auth/register",
        data={
            "username": "bot",
            "email": "bot@example.com",
            "password": "password",
            "captcha_answer": "WRONG",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please complete the CAPTCHA challenge." in response.data
    with app.app_context():
        assert User.query.filter_by(username="bot").first() is None


def test_registration_accepts_correct_captcha(client, app):
    client.get("/auth/captcha.svg")

    response = client.post(
        "/auth/register",
        data={
            "username": "alice",
            "email": "alice@example.com",
            "password": "password",
            "captcha_answer": app.config["CAPTCHA_TEST_CODE"],
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Feed" in response.data
    with app.app_context():
        assert User.query.filter_by(username="alice").one()
