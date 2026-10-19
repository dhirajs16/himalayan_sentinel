import hashlib
import hmac
import secrets
import time

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, select

from . import db

bearer = HTTPBearer(auto_error=False)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    value = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1
    ).hex()
    return f"scrypt${salt}${value}"


def verify_password(password: str, stored: str) -> bool:
    _, salt, expected = stored.split("$")
    actual = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1
    ).hex()
    return hmac.compare_digest(actual, expected)


def new_session(conn, user_id):
    access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    conn.execute(
        db.sessions.insert().values(
            id=db.uid(),
            user_id=user_id,
            access_hash=digest(access),
            refresh_hash=digest(refresh),
            access_expires=time.time() + 900,
            refresh_expires=time.time() + 28800,
            revoked=False,
        )
    )
    return access, refresh


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Sign in required")
    with db.transaction() as conn:
        session = (
            conn.execute(
                select(db.sessions).where(
                    and_(
                        db.sessions.c.access_hash == digest(credentials.credentials),
                        db.sessions.c.revoked.is_(False),
                        db.sessions.c.access_expires > time.time(),
                    )
                )
            )
            .mappings()
            .first()
        )
        user = (
            conn.execute(select(db.users).where(db.users.c.id == session["user_id"]))
            .mappings()
            .first()
            if session
            else None
        )
    if not user or not user["active"]:
        raise HTTPException(401, "Session expired")
    return dict(user)


def role(required):
    def dependency(user=Depends(current_user)):
        if user["role"] != required:
            raise HTTPException(403, f"{required.title()} role required")
        return user

    return dependency


def jurisdiction(user, region):
    if user["role"] == "government" and region not in user["jurisdictions"]:
        raise HTTPException(403, "Outside assigned jurisdiction")


def throttle(request: Request, action: str, maximum: int, seconds: int = 3600):
    """Database-backed fixed windows; do not trust arbitrary X-Forwarded-For."""
    identity = request.client.host if request.client else "unknown"
    key = digest(f"{identity}:{action}:{int(time.time()) // seconds}")
    with db.transaction() as conn:
        # An atomic upsert avoids concurrent submissions resetting a counter.
        from sqlalchemy import text

        conn.execute(
            text(
                'INSERT INTO rate_limits (id, "window", count) VALUES (:key, :window, 1) ON CONFLICT (id) DO UPDATE SET count = rate_limits.count + 1'
            ),
            {"key": key, "window": int(time.time())},
        )
        count = conn.execute(
            select(db.limits.c.count).where(db.limits.c.id == key)
        ).scalar_one()
    if count > maximum:
        raise HTTPException(
            429,
            "Too many requests; please try later",
            headers={"Retry-After": str(seconds)},
        )
