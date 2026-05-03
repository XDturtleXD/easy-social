from __future__ import annotations

from datetime import datetime

import pytest

from easy_social.extensions import db
from easy_social.models import Comment, Post, User
from scripts.import_fake_data import (
    comment_author_for_post,
    comment_count_for_post,
    find_comment,
    find_post,
    find_repost,
    parse_timestamp,
)


def make_user(username: str) -> User:
    user = User(username=username, email=f"{username}@example.com")
    user.set_password("password")
    return user


def test_parse_timestamp_uses_iso_format():
    assert parse_timestamp("2026-04-18T12:30:45") == datetime(2026, 4, 18, 12, 30, 45)


def test_comment_count_cycles_between_three_and_five():
    assert [comment_count_for_post(index) for index in range(6)] == [3, 4, 5, 3, 4, 5]


def test_comment_author_excludes_post_author_and_cycles_candidates(app):
    with app.app_context():
        alice = make_user("alice")
        bob = make_user("bob")
        carol = make_user("carol")
        db.session.add_all([alice, bob, carol])
        db.session.commit()

        assert comment_author_for_post([alice, bob, carol], alice, 0) == bob
        assert comment_author_for_post([alice, bob, carol], alice, 1) == carol
        assert comment_author_for_post([alice, bob, carol], alice, 2) == bob


def test_comment_author_requires_another_user(app):
    with app.app_context():
        alice = make_user("alice")
        db.session.add(alice)
        db.session.commit()

        with pytest.raises(ValueError, match="At least two users"):
            comment_author_for_post([alice], alice, 0)


def test_seed_find_helpers_match_existing_records(app):
    with app.app_context():
        alice = make_user("alice")
        bob = make_user("bob")
        created_at = parse_timestamp("2026-04-18T12:30:45")
        original = Post(author=alice, body="Original", created_at=created_at)
        repost = Post(author=bob, body="", repost_of=original, created_at=created_at)
        comment = Comment(author=bob, post=original, body="Useful note")
        db.session.add_all([alice, bob, original, repost, comment])
        db.session.commit()

        assert find_post(alice, "Original", created_at) == original
        assert find_post(alice, "Different", created_at) is None
        assert find_repost(bob, original, created_at) == repost
        assert find_comment(bob, original, "Useful note") == comment
