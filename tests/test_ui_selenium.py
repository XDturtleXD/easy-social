from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

import pytest
from werkzeug.serving import make_server

from easy_social import create_app
from easy_social.extensions import db
from easy_social.models import Comment, Post, User

selenium = pytest.importorskip("selenium")

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture(scope="module")
def ui_app():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{temp_path / 'ui.sqlite'}",
                "UPLOAD_FOLDER": str(temp_path / "uploads"),
                "WTF_CSRF_ENABLED": False,
            }
        )
        with app.app_context():
            db.create_all()
        yield app


@pytest.fixture(scope="module")
def live_server(ui_app):
    try:
        server = make_server("127.0.0.1", 0, ui_app, threaded=True)
    except SystemExit:
        pytest.skip("Selenium live server could not bind to a local port")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture()
def browser():
    browser_name = os.environ.get("SELENIUM_BROWSER", "chrome").lower()
    headless = os.environ.get("SELENIUM_HEADLESS", "1") != "0"

    try:
        if browser_name == "firefox":
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument("-headless")
            driver = webdriver.Firefox(options=options)
        else:
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--window-size=1280,900")
            driver = webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Selenium browser could not start: {exc.msg}")

    yield driver

    driver.quit()


@pytest.fixture(autouse=True)
def clean_database(ui_app):
    with ui_app.app_context():
        db.session.query(Comment).delete()
        db.session.query(Post).delete()
        db.session.query(User).delete()
        db.session.commit()


def wait_for_text(browser, text: str):
    WebDriverWait(browser, 5).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))


def register_via_ui(browser, live_server: str, username: str):
    browser.get(f"{live_server}/auth/register")
    form = browser.find_element(By.CSS_SELECTOR, "form.form-stack")
    form.find_element(By.NAME, "username").send_keys(username)
    form.find_element(By.NAME, "email").send_keys(f"{username}@example.com")
    form.find_element(By.NAME, "password").send_keys("password")
    form.submit()
    wait_for_text(browser, "Feed")


def logout_via_ui(browser):
    browser.find_element(By.CSS_SELECTOR, "header form").submit()
    wait_for_text(browser, "Log in")


@pytest.mark.ui
def test_user_can_register_create_post_and_comment(browser, live_server):
    register_via_ui(browser, live_server, "alice")

    composer = browser.find_element(By.CSS_SELECTOR, "form.composer")
    composer.find_element(By.NAME, "body").send_keys("Hello from Selenium")
    composer.submit()
    wait_for_text(browser, "Hello from Selenium")

    browser.find_element(By.PARTIAL_LINK_TEXT, "0 comments").click()
    wait_for_text(browser, "Comments")
    comment_form = browser.find_element(By.CSS_SELECTOR, "form.comment-form")
    comment_form.find_element(By.NAME, "body").send_keys("First UI comment")
    comment_form.submit()
    wait_for_text(browser, "First UI comment")


@pytest.mark.ui
def test_following_user_adds_their_posts_to_feed(browser, live_server):
    register_via_ui(browser, live_server, "bob")
    composer = browser.find_element(By.CSS_SELECTOR, "form.composer")
    composer.find_element(By.NAME, "body").send_keys("Bob browser update")
    composer.submit()
    wait_for_text(browser, "Bob browser update")
    logout_via_ui(browser)

    register_via_ui(browser, live_server, "alice")
    assert "Bob browser update" not in browser.find_element(By.TAG_NAME, "body").text

    browser.find_element(By.LINK_TEXT, "Explore").click()
    wait_for_text(browser, "@bob")
    browser.find_element(By.XPATH, "//button[normalize-space()='Follow']").click()
    wait_for_text(browser, "Unfollow")

    browser.find_element(By.LINK_TEXT, "Feed").click()
    wait_for_text(browser, "Bob browser update")
