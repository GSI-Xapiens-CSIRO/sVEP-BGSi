import os
import hashlib
from pathlib import Path

DIRECTORY = str(Path(__file__).resolve().parent)
HASH_FILE = ".hash.txt"


def sha1_of_file(filepath: str):
    sha = hashlib.sha1()
    sha.update(filepath.encode())

    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(2**10), b""):
            sha.update(block)
        return sha.hexdigest()


def hash_dir(dir_path: str):
    sha = hashlib.sha1()

    for path, _, files in os.walk(dir_path):
        # we sort to guarantee that files will always go in the same order
        for file in sorted(files):
            if file == HASH_FILE:
                continue
            file_hash = sha1_of_file(os.path.join(path, file))
            sha.update(file_hash.encode())
    hash = sha.hexdigest()
    with open(f"{DIRECTORY}/{HASH_FILE}", "w") as f:
        f.write(hash)
    return hash


if __name__ == "__main__":
    print(f""" {{ "hash": "{hash_dir(DIRECTORY)}" }} """)
