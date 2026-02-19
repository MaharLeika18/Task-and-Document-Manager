import secrets
import string

def generate_secure_string(length=16):
    """Generates a cryptographically secure random string."""
    characters = string.ascii_letters + string.digits + string.punctuation
    secure_string = ''.join(secrets.choice(characters) for _ in range(length))
    return secure_string