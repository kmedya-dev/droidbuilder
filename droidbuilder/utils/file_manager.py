import os
import hashlib
import shutil

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

def move_files(source_dir, dest_dir):
    """Move files, normalizing the directory structure."""
    source_items = os.listdir(source_dir)

    # If the source directory contains a single directory, move that directory to the destination.
    # This is a common case for archives that extract to a single root folder.
    if len(source_items) == 1:
        inner_path = os.path.join(source_dir, source_items[0])
        if os.path.isdir(inner_path):
            shutil.move(inner_path, dest_dir)
            return

    # Otherwise, move all items from the source to the destination.
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    for item in source_items:
        shutil.move(os.path.join(source_dir, item), dest_dir) 
