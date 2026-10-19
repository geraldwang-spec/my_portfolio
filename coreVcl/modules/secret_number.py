import secrets

def generate_random_number(start:int, end:int)->int:
    if end <= start:
        raise ValueError(f"end ({end}) must be > start ({start})")
    return start + secrets.randbelow(end-start+1)
