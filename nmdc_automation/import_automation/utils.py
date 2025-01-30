import hashlib
import os


def get_or_create_md5(fn: str) -> str:
    """
    Generate md5 hash for file, writing to file '.md5' if it doesn't exist.
    Return hash value.

    Args:
        fn (str): file name

    Returns:
        md5:  md5 hash of file
    """

    md5f = fn + ".md5"
    if os.path.exists(md5f):
        with open(md5f) as f:
            md5 = f.read().rstrip()
    else:
        md5 = hashlib.md5(open(fn, "rb").read()).hexdigest()
        with open(md5f, "w") as f:
            f.write(md5)
            f.write("\n")
    return md5


