import os
import hashlib

# -------------------- Hashing Utilities --------------------

def hash_file(file_path, algorithm='sha256'):
    """Compute the hash of a file."""
    h = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def verify_hash(file_path, expected_hash, algorithm='sha256'):
    """Verify the hash of a file."""
    return hash_file(file_path, algorithm) == expected_hash

def safe_join(base, *paths):
    """Safely join paths, preventing path traversal attacks."""
    path = os.path.realpath(os.path.join(base, *paths))
    base = os.path.realpath(base)
    if os.path.commonprefix((path, base)) != base:
        raise PermissionError("Path traversal attempt detected")
    return path