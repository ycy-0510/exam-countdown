import os
import secrets
import bcrypt
from fastapi import Request, HTTPException

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

if not ADMIN_USER or not ADMIN_PASSWORD_HASH:
    raise RuntimeError("ADMIN_USER or ADMIN_PASSWORD_HASH is not set")


def require_login(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=303, headers={"Location": "/login"})


def verify_credentials(username: str, password: str) -> bool:
    assert ADMIN_USER and ADMIN_PASSWORD_HASH
    user_ok = secrets.compare_digest(ADMIN_USER, username)
    password_ok = bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH.encode())
    return user_ok and password_ok
