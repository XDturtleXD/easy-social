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

Install Poetry and Task, then install the project dependencies:

```bash
task install
task init-db
task run
```

The app uses SQLite by default and creates `instance/easy_social.sqlite`.

Useful environment variables:

```bash
SECRET_KEY=change-me
DATABASE_URL=sqlite:////absolute/path/to/db.sqlite
```

To load sample users, follows, posts, comments, and reposts:

```bash
task import-fake-data
```

## Tests

The default test task runs unit and Flask integration tests. Selenium UI tests
are excluded from the default pytest configuration.

```bash
task test
```

Tests are split with pytest markers so new tests can join CI by marker:

```bash
task test-unit
task test-integration
task test-ui
```

The Selenium UI tests run against a temporary live Flask server. By default they
use headless Chrome. Set `SELENIUM_BROWSER=firefox` for Firefox or
`SELENIUM_HEADLESS=0` to watch the browser.

## CI

GitHub Actions runs separate workflows:

- `Unit Tests` installs dependencies with `task install` and runs `task test-unit`.
- `Integration Tests` installs dependencies with `task install`, runs
  `task test-integration`, then runs Selenium with `task test-ui`.
