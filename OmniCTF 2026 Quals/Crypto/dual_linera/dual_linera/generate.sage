#!/usr/bin/env sage

import hashlib
import json
import operator
import os

SECRET_BITS = int(96)
E_BITS = int(176)
SAMPLE_COUNT = int(18)


def xor_stream(key, data):
    stream = hashlib.shake_256(key).digest(len(data))
    return bytes(operator.xor(a, b) for a, b in zip(data, stream))


def make_instance(flag):
    q1 = random_prime(2**180 - 1, lbound=2**179)
    q2 = random_prime(2**181 - 1, lbound=2**180)
    assert q1 != q2

    secret = ZZ.random_element(2 ** (SECRET_BITS - 1), 2**SECRET_BITS)
    samples = []

    for _ in range(SAMPLE_COUNT):
        a1 = ZZ.random_element(1, q1)
        a2 = ZZ.random_element(1, q2)
        e = ZZ.random_element(0, 2**E_BITS)
        samples.append({
            "a1": int(a1),
            "a2": int(a2),
            "y1": int((a1 * secret + e) % q1),
            "y2": int((a2 * secret + e) % q2),
        })

    key = hashlib.sha256(str(int(secret)).encode()).digest()
    flag_ciphertext = xor_stream(key, flag).hex()

    return {
        "q1": int(q1),
        "q2": int(q2),
        "secret_bits": SECRET_BITS,
        "e_bits": E_BITS,
        "sample_count": SAMPLE_COUNT,
        "flag_ciphertext": flag_ciphertext,
        "samples": samples,
    }


def main():
    flag = os.environ.get("FLAG", "flag{dummy}")
    print(json.dumps(make_instance(flag.encode()), indent=int(2)))


if __name__ == "__main__":
    main()
