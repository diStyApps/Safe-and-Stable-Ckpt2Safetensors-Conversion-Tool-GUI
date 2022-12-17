
import hashlib
HASH_START = 0x100000
HASH_LENGTH = 0x10000
def get_file_hash(filename):
    with open(filename, "rb") as file:
        m = hashlib.sha256()
        file.seek(HASH_START)
        m.update(file.read(HASH_LENGTH))
        return m.hexdigest()[0:8]