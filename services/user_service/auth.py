"""
Authentication and authorization utilities
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import jwt
import os
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Configure bcrypt with proper settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    bcrypt__ident="2b",  # Use bcrypt version 2b
    deprecated="auto"
)

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def get_password_hash(password: str) -> str:
    """Hash a password (bcrypt has 72 byte limit, so truncate if necessary)"""
    # Ensure password is a string
    if not isinstance(password, str):
        password = str(password)
    
    # Bcrypt has a 72 byte limit - ALWAYS truncate to 72 bytes to avoid errors
    # This is safe because we're truncating before hashing
    password_bytes = password.encode('utf-8')
    
    # Truncate to exactly 72 bytes if longer (bcrypt's hard limit)
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    elif len(password_bytes) == 72:
        # If exactly 72 bytes, ensure it's properly handled
        password = password_bytes.decode('utf-8', errors='ignore')
    
    # Hash the password - passlib will handle the rest
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (truncate if necessary for bcrypt limit)"""
    # Bcrypt has a 72 byte limit, truncate password if it's longer
    if isinstance(plain_password, str):
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

