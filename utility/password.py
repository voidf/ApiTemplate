from config import secret
import hashlib
def encrypt(s: str) -> str:
    return hashlib.sha256((s + secret.auth_salt).encode('utf-8')).hexdigest()
