import base64
import hashlib
import secrets
import string

def generate_code_verifier()-> str:
    """Random String PKCE uses as the 'secret' proof """
    allowed_chars = string.ascii_letters + string.digits + "-._~"
    return "".join(secrets.choice(allowed_chars) for _ in range(128))

def generate_code_challenge(verifier: str) -> str:
    """SHA256 hash of the verifier, base64url-encoded, no padding."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")
