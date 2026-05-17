from __future__ import annotations

import secrets
from hmac import compare_digest

CAPTCHA_SESSION_KEY = "registration_captcha_answer"
CAPTCHA_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_captcha_code(length: int = 5) -> str:
    alphabet = CAPTCHA_ALPHABET
    return "".join(secrets.choice(alphabet) for _ in range(length))


def captcha_svg(code: str) -> str:
    lines = []
    for index, char in enumerate(code):
        x = 24 + index * 30
        y = 48 + (index % 2) * 5
        rotation = -8 if index % 2 == 0 else 7
        lines.append(
            f'<text x="{x}" y="{y}" transform="rotate({rotation} {x} {y})">{char}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="190" height="72" viewBox="0 0 190 72" role="img" aria-label="CAPTCHA image">
  <rect width="190" height="72" rx="8" fill="#eef6f7"/>
  <path d="M12 22 C38 6, 62 45, 92 24 S146 12, 178 36" fill="none" stroke="#8cb8bf" stroke-width="3"/>
  <path d="M10 52 C42 36, 68 66, 104 48 S150 34, 181 54" fill="none" stroke="#d29a7e" stroke-width="2"/>
  <g fill="#17343a" font-family="Consolas, Menlo, monospace" font-size="34" font-weight="800" letter-spacing="4">
    {"".join(lines)}
  </g>
</svg>
"""


def captcha_answer_matches(expected: str | None, submitted: str | None) -> bool:
    if not expected or not submitted:
        return False
    normalized_expected = expected.strip().upper()
    normalized_submitted = submitted.strip().upper()
    return compare_digest(normalized_expected, normalized_submitted)
