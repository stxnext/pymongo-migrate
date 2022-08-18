import string
from random import choice


def generate_str(length=50, chars=None):
    if not chars:
        chars = string.ascii_uppercase + string.digits

    return "".join(choice(chars) for _ in range(length))  # nosec
