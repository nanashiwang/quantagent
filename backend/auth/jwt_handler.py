import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_HOURS", "24"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REMEMBER_ME_EXPIRE_DAYS = int(os.getenv("JWT_REMEMBER_ME_EXPIRE_DAYS", "30"))
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
_INSECURE_SECRET_VALUES = {
    "",
    "quant-trading-secret-key-change-in-production",
    "change-this-to-a-long-random-secret",
    "your-super-secret-jwt-key",
}

# 新密码优先使用 bcrypt_sha256，避免 bcrypt 原生 72 字节限制；
# 同时保留 bcrypt 以兼容已存在的旧密码哈希。
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_secret_key() -> str:
    secret_key = os.getenv("JWT_SECRET_KEY", "").strip()
    if secret_key in _INSECURE_SECRET_VALUES:
        raise RuntimeError("必须配置安全的 JWT_SECRET_KEY 环境变量")
    return secret_key


def validate_jwt_config():
    get_secret_key()


def get_access_token_expires_delta() -> timedelta:
    return timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)


def get_refresh_token_expires_delta(remember_me: bool = False) -> timedelta:
    if remember_me:
        return timedelta(days=REMEMBER_ME_EXPIRE_DAYS)
    return timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)


def _create_token(
    data: dict,
    *,
    token_type: str,
    expires_delta: timedelta,
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": uuid4().hex,
        "token_type": token_type,
    })
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def create_access_token(
    data: dict,
    *,
    remember_me: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    payload = data.copy()
    payload.setdefault("remember_me", remember_me)
    return _create_token(
        payload,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=expires_delta or get_access_token_expires_delta(),
    )


def create_refresh_token(
    data: dict,
    *,
    remember_me: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    payload = data.copy()
    payload.setdefault("remember_me", remember_me)
    return _create_token(
        payload,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=expires_delta or get_refresh_token_expires_delta(remember_me),
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[dict]:
    payload = decode_token(token)
    if payload is None:
        return None
    token_type = payload.get("token_type")
    if token_type not in (None, ACCESS_TOKEN_TYPE):
        return None
    return payload


def decode_refresh_token(token: str) -> Optional[dict]:
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("token_type") != REFRESH_TOKEN_TYPE:
        return None
    return payload
