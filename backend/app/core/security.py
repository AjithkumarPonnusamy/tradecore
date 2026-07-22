from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
import bcrypt
import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def get_fernet() -> Fernet:
    base_key = settings.ENCRYPTION_KEY or settings.JWT_SECRET_KEY
    try:
        # Check if base_key is a valid pre-generated Fernet key (32 bytes decoded)
        decoded = base64.urlsafe_b64decode(base_key.encode())
        if len(decoded) == 32:
            return Fernet(base_key.encode())
    except Exception:
        pass
    # Otherwise derive a base64 encoded 32-byte key using SHA-256 of the base_key
    key_hash = hashlib.sha256(base_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    return Fernet(fernet_key)

def encrypt_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    try:
        f = get_fernet()
        return f.encrypt(value.encode()).decode()
    except Exception as e:
        print(f"Encryption failed: {e}")
        return value

def decrypt_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    try:
        f = get_fernet()
        return f.decrypt(value.encode()).decode()
    except Exception as e:
        # If decryption fails (e.g. value was plain text), return original value
        print(f"Decryption failed, returning plain value: {e}")
        return value
