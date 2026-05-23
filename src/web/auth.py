import secrets
import bcrypt
from fastapi import Request, HTTPException

from .repository import get_admin_user, get_admin_password_hash, is_first_run


def require_login(request: Request):
    if not request.session.get("user"):
        if is_first_run():
            raise HTTPException(status_code=303, headers={"Location": "/setup"})
        raise HTTPException(status_code=303, headers={"Location": "/login"})


def verify_credentials(username: str, password: str) -> bool:
    db_user = get_admin_user()
    db_hash = get_admin_password_hash()
    if not db_user or not db_hash:
        return False
    user_ok = secrets.compare_digest(db_user, username)
    password_ok = bcrypt.checkpw(password.encode(), db_hash.encode())
    return user_ok and password_ok
