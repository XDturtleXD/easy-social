# Easy Social

A small Twitter-like social media app built with Flask.

## Features

- Register, log in, and log out with Flask-Login.
- Create posts containing text, images, videos, or a combination.
- Repost existing posts.
- Comment on posts.
- Follow and unfollow users.
- View a personalized feed from yourself and people you follow.
- Local media uploads with extension-based image/video validation.

## Setup

```bash
poetry install
poetry run flask --app easy_social init-db
poetry run flask --app easy_social run
```

The app uses SQLite by default and creates `instance/easy_social.sqlite`.

Useful environment variables:

```bash
SECRET_KEY=change-me
DATABASE_URL=sqlite:////absolute/path/to/db.sqlite
```

## Tests

```bash
poetry run pytest
```

