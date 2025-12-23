import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

def hash_password(raw_password: str) -> str:
    return pwd_context.hash(raw_password)

def verify_password(raw_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    Supports both old SHA256 hashes (for migration) and new argon2 hashes.
    """
    # Check if it's an old SHA256 hash (64 hex characters, no $ prefix)
    if len(hashed_password) == 64 and all(c in '0123456789abcdef' for c in hashed_password.lower()):
        # Old SHA256 format - verify using SHA256
        computed_hash = hashlib.sha256(raw_password.encode()).hexdigest()
        return computed_hash == hashed_password.lower()
    
    # New argon2 format - verify using passlib
    try:
        return pwd_context.verify(raw_password, hashed_password)
    except Exception:
        # If passlib can't identify the hash, return False
        return False
