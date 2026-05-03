from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path

from easy_social import create_app
from easy_social.extensions import db
from easy_social.models import Comment, Post, User


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "seed_data"

COMMENT_TEMPLATES = [
    "This makes the thread feel much easier to follow.",
    "Good note. I want to check this path in the demo too.",
    "That detail would help a new user understand what changed.",
    "I like how specific this is without making the post too long.",
    "This is exactly the kind of sample conversation the feed needed.",
]


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def find_post(author: User, body: str, created_at: datetime) -> Post | None:
    return Post.query.filter_by(
        author_id=author.id,
        body=body,
        created_at=created_at,
        repost_of_id=None,
    ).one_or_none()


def find_repost(author: User, repost_of: Post, created_at: datetime) -> Post | None:
    return Post.query.filter_by(
        author_id=author.id,
        repost_of_id=repost_of.id,
        created_at=created_at,
    ).one_or_none()


def find_comment(author: User, post: Post, body: str) -> Comment | None:
    return Comment.query.filter_by(
        author_id=author.id,
        post_id=post.id,
        body=body,
    ).one_or_none()


def comment_count_for_post(index: int) -> int:
    return 3 + (index % 3)


def comment_author_for_post(users: list[User], post_author: User, index: int) -> User:
    candidates = [user for user in users if user.id != post_author.id]
    if not candidates:
        raise ValueError("At least two users are required to seed comments")
    return candidates[index % len(candidates)]


def import_fake_data(data_dir: Path) -> dict[str, int]:
    db.create_all()

    users_by_username: dict[str, User] = {}
    post_keys: dict[str, Post] = {}
    seeded_posts: list[Post] = []
    counts = {
        "users_created": 0,
        "users_updated": 0,
        "follows_created": 0,
        "posts_created": 0,
        "comments_created": 0,
        "reposts_created": 0,
    }

    for row in read_csv(data_dir / "users.csv"):
        user = User.query.filter_by(username=row["username"]).one_or_none()
        if user is None:
            user = User(
                username=row["username"],
                email=row["email"],
                bio=row["bio"],
                created_at=parse_timestamp(row["created_at"]),
            )
            user.set_password(row["password"])
            db.session.add(user)
            counts["users_created"] += 1
        else:
            user.email = row["email"]
            user.bio = row["bio"]
            counts["users_updated"] += 1

        users_by_username[user.username] = user

    db.session.flush()

    for row in read_csv(data_dir / "follows.csv"):
        follower = users_by_username[row["follower"]]
        followed = users_by_username[row["followed"]]
        if follower.id == followed.id:
            raise ValueError(f"{follower.username} cannot follow themselves")
        if not follower.is_following(followed):
            follower.follow(followed)
            counts["follows_created"] += 1

    for row in read_csv(data_dir / "posts.csv"):
        author = users_by_username[row["username"]]
        created_at = parse_timestamp(row["created_at"])
        post = find_post(author, row["body"], created_at)
        if post is None:
            post = Post(author=author, body=row["body"], created_at=created_at)
            db.session.add(post)
            counts["posts_created"] += 1
        post_keys[row["post_key"]] = post
        seeded_posts.append(post)

    db.session.flush()

    seeded_users = list(users_by_username.values())
    for post_index, post in enumerate(seeded_posts):
        for comment_index in range(comment_count_for_post(post_index)):
            author = comment_author_for_post(
                seeded_users,
                post.author,
                post_index + comment_index,
            )
            body = COMMENT_TEMPLATES[(post_index + comment_index) % len(COMMENT_TEMPLATES)]
            if find_comment(author, post, body) is None:
                comment = Comment(
                    author=author,
                    post=post,
                    body=body,
                    created_at=post.created_at + timedelta(minutes=comment_index + 1),
                )
                db.session.add(comment)
                counts["comments_created"] += 1

    for row in read_csv(data_dir / "reposts.csv"):
        author = users_by_username[row["username"]]
        repost_of = post_keys[row["repost_of_key"]]
        created_at = parse_timestamp(row["created_at"])
        repost = find_repost(author, repost_of, created_at)
        if repost is None:
            repost = Post(author=author, body="", repost_of=repost_of, created_at=created_at)
            db.session.add(repost)
            counts["reposts_created"] += 1

    db.session.commit()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Import fake Easy Social CSV seed data.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Directory containing seed CSV files. Defaults to {DEFAULT_DATA_DIR}.",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        counts = import_fake_data(args.data_dir)

    print(
        "Imported fake data: "
        f"{counts['users_created']} users created, "
        f"{counts['users_updated']} users updated, "
        f"{counts['follows_created']} follows created, "
        f"{counts['posts_created']} posts created, "
        f"{counts['comments_created']} comments created, "
        f"{counts['reposts_created']} reposts created."
    )


if __name__ == "__main__":
    main()
