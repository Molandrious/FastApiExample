import hashlib


def hash_string(input_string) -> str:
    input_bytes = input_string.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input_bytes)
    return sha256_hash.hexdigest()
