import secrets
import requests
import re

DEFAULT_SERVER = "https://ntfy.sh"
TOPIC_PREFIX = "exam-countdown-"

_URL_RE = re.compile(r"(https?://[^/\s]+)(?:/\S*)?")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]{20,}")


def redact(text: str) -> str:
    """Mask URL paths/queries and long token-like substrings before sending.
    Best-effort: ntfy topic is essentially a shared secret, and error messages
    may carry access tokens, webhook URLs, or Cloudinary IDs. We strip the
    obvious shapes so a leaked topic doesn't immediately leak credentials.
    """
    if not text:
        return text
    text = _URL_RE.sub(lambda m: f"{m.group(1)}/***", text)
    text = _TOKEN_RE.sub(lambda m: f"***({len(m.group(0))} chars)***", text)
    return text


def generate_random_topic() -> str:
    return TOPIC_PREFIX + secrets.token_urlsafe(8)


def send_ntfy(
    topic: str,
    title: str,
    message: str,
    *,
    priority: int = 4,
    tags: str = "warning",
    server: str = DEFAULT_SERVER,
) -> None:
    url = f"{server.rstrip('/')}/{topic}"
    res = requests.post(
        url,
        data=redact(message).encode("utf-8"),
        headers={
            "Title": title,
            "Priority": str(priority),
            "Tags": tags,
        },
        timeout=10,
    )
    res.raise_for_status()


def test_ntfy(topic: str) -> tuple[bool, str, str | None]:
    try:
        send_ntfy(
            topic,
            title="Exam Countdown - Test Notification",
            message="This is a test notification. If you see this, ntfy is working.",
            priority=3,
            tags="white_check_mark",
        )
        return True, f"Test sent to topic '{topic}'", None
    except Exception as e:
        return False, "Failed to send test notification", str(e)
