import os
from datetime import datetime, timedelta
from typing import Dict

from dotenv import load_dotenv
from jose import JWTError, jwt
from litestar.connection import Request
from litestar.exceptions import NotAuthorizedException

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = "HS256"
JWT_EXP_MINUTES = 30

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set")


def generate_token(data: Dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> Dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except JWTError:
        raise NotAuthorizedException("Invalid or expired token")


def require_auth(request: Request) -> Dict:
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise NotAuthorizedException("Missing token")
    return decode_token(auth.removeprefix("Bearer ").strip())
