from __future__ import annotations

import pytest

from easy_social.captcha import (
    CAPTCHA_ALPHABET,
    captcha_answer_matches,
    captcha_svg,
    generate_captcha_code,
)

pytestmark = pytest.mark.unit


def test_generate_captcha_code_uses_configured_length_and_safe_alphabet():
    code = generate_captcha_code(8)

    assert len(code) == 8
    assert set(code).issubset(set(CAPTCHA_ALPHABET))


def test_captcha_answer_matches_case_insensitively():
    assert captcha_answer_matches("ABC12", " abc12 ")


def test_captcha_answer_rejects_missing_or_wrong_answers():
    assert not captcha_answer_matches(None, "ABC12")
    assert not captcha_answer_matches("ABC12", "")
    assert not captcha_answer_matches("ABC12", "ABC13")


def test_captcha_svg_renders_as_image_without_plain_description_leak():
    svg = captcha_svg("ABC12")

    assert svg.startswith("<svg")
    assert 'role="img"' in svg
    assert "<desc>" not in svg
