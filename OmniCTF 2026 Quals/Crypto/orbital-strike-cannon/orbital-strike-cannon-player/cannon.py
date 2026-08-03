#!/usr/bin/env python3
"""
Orbital-Strike-Cannon core.

The hosted challenge intentionally uses only Python's standard library.  The
algebra is dramatic, but the instance stays tiny: no Sage, no NumPy, no crypto
package, and no large tables.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import secrets
from dataclasses import dataclass
from typing import Iterable


FLAG = b"OmniCTF{dummy}"
P = (1 << 127) - 1
N_STATES = 34
N_SATELLITES = 7
REAL_SATELLITES = 5
COORDS_PER_SAMPLE = 3
SAMPLES_PER_SATELLITE = 5


def add(a: list[int], b: list[int]) -> list[int]:
    return [(x + y) % P for x, y in zip(a, b)]


def sub(a: list[int], b: list[int]) -> list[int]:
    return [(x - y) % P for x, y in zip(a, b)]


def q_conj(a: list[int]) -> list[int]:
    return [a[0], (-a[1]) % P, (-a[2]) % P, (-a[3]) % P]


def q_mul(a: list[int], b: list[int]) -> list[int]:
    a0, a1, a2, a3 = a
    b0, b1, b2, b3 = b
    return [
        (a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3) % P,
        (a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2) % P,
        (a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1) % P,
        (a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0) % P,
    ]


def o_conj(x: list[int]) -> list[int]:
    return q_conj(x[:4]) + [(-v) % P for v in x[4:]]


def o_mul(x: list[int], y: list[int]) -> list[int]:
    """Cayley-Dickson octonion multiplication over F_P.

    x = (a, b), y = (c, d)
    x*y = (a*c - conj(d)*b, d*a + b*conj(c))

    This convention is intentionally non-associative.  The challenge transition
    uses ((R_i * M_i) * ALPHA), not R_i * (M_i * ALPHA).
    """

    a, b = x[:4], x[4:]
    c, d = y[:4], y[4:]
    left = sub(q_mul(a, c), q_mul(q_conj(d), b))
    right = add(q_mul(d, a), q_mul(b, q_conj(c)))
    return left + right


def basis(i: int) -> list[int]:
    out = [0] * 8
    out[i] = 1
    return out


def mat_left(o: list[int]) -> list[list[int]]:
    return transpose([o_mul(o, basis(i)) for i in range(8)])


def mat_right(o: list[int]) -> list[list[int]]:
    return transpose([o_mul(basis(i), o) for i in range(8)])


def transpose(m: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*m)]


def mat_mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    rows, inner, cols = len(a), len(b), len(b[0])
    return [
        [sum(a[i][k] * b[k][j] for k in range(inner)) % P for j in range(cols)]
        for i in range(rows)
    ]


def mat_vec(a: list[list[int]], v: list[int]) -> list[int]:
    return [sum(row[i] * v[i] for i in range(len(v))) % P for row in a]


def dot(a: list[int], b: list[int]) -> int:
    return sum(x * y for x, y in zip(a, b)) % P


def inv(x: int) -> int:
    return pow(x % P, P - 2, P)


def int_to_bytes(x: int) -> bytes:
    return x.to_bytes(16, "big")


def vec_to_bytes(v: Iterable[int]) -> bytes:
    return b"".join(int_to_bytes(x % P) for x in v)


def shake_xor(key: bytes, data: bytes) -> str:
    stream = hashlib.shake_256(key + b"|stream").digest(len(data))
    return bytes(a ^ b for a, b in zip(data, stream)).hex()


@dataclass
class Instance:
    public: dict
    firing_code: str
    flag: bytes


class BrokenRNG:
    def __init__(self, u: int, v: int, state: int):
        self.u = u % P
        self.v = v % P
        self.state = state % P

    def next(self) -> int:
        out = self.state
        self.state = (self.u * self.state + self.v) % P
        return out


def derive_seed(seed: str | bytes | None) -> int:
    if seed is None:
        seed = secrets.token_hex(32)
    if isinstance(seed, str):
        seed = seed.encode()
    return int.from_bytes(hashlib.sha256(b"OSC-SEED|" + seed).digest(), "big")


def rnd_vec(rng: random.Random, n: int) -> list[int]:
    return [rng.randrange(1, P) for _ in range(n)]


def rng_octonion(r: list[int], i: int) -> list[int]:
    a, b, c, d = r[i], r[i + 1], r[i + 2], r[i + 3]
    return [
        1,
        a,
        b,
        c,
        d,
        (a * b + c) % P,
        (b * c + d) % P,
        (a * d + b * c + 7) % P,
    ]


def build_state_expressions(alpha: list[int], beta: list[int], outer_a: int, rng_values: list[int]):
    """Return affine expressions for [M_i, X_i, 1] in terms of [M_0, X_0, 1]."""

    states = []
    cur = [[1 if i == j else 0 for j in range(10)] for i in range(10)]
    states.append(cur)

    for i in range(N_STATES + 3):
        r_oct = rng_octonion(rng_values, i)
        transition = mat_mul(mat_right(alpha), mat_left(r_oct))

        step = [[0] * 10 for _ in range(10)]
        for row in range(8):
            for col in range(8):
                step[row][col] = transition[row][col]
            step[row][9] = beta[row]

        for col in range(8):
            step[8][col] = 1
        step[8][8] = outer_a
        step[8][9] = rng_values[i]
        step[9][9] = 1

        cur = mat_mul(step, cur)
        states.append(cur)
    return states


def feature_rows(states: list[list[list[int]]], i: int) -> list[list[int]]:
    """Rows expressing [M_i..., X_i, X_{i+1}, X_{i+2}] from [M_0..., X_0, 1]."""

    rows = [states[i][j] for j in range(8)]
    rows.append(states[i][8])
    rows.append(states[i + 1][8])
    rows.append(states[i + 2][8])
    return rows


def feature_value(moons: list[list[int]], orbits: list[int], i: int) -> list[int]:
    return moons[i] + [orbits[i], orbits[i + 1], orbits[i + 2]]


def make_instance(seed: str | bytes | None = None, flag: bytes = FLAG) -> Instance:
    rng = random.Random(derive_seed(seed))

    alpha = rnd_vec(rng, 8)
    beta = rnd_vec(rng, 8)
    moon0 = rnd_vec(rng, 8)
    x0 = rng.randrange(1, P)
    outer_a = rng.randrange(2, P - 1)

    rng_u = rng.randrange(2, P - 1)
    rng_v = rng.randrange(2, P - 1)
    rng_s = rng.randrange(2, P - 1)
    broken = BrokenRNG(rng_u, rng_v, rng_s)
    rng_values = [broken.next() for _ in range(N_STATES + 8)]

    moons = [moon0]
    orbits = [x0]
    for i in range(N_STATES + 3):
        nxt = add(o_mul(o_mul(rng_octonion(rng_values, i), moons[-1]), alpha), beta)
        moons.append(nxt)
        orbits.append((outer_a * orbits[-1] + sum(moons[-2]) + rng_values[i]) % P)

    states = build_state_expressions(alpha, beta, outer_a, rng_values)
    secret_material = vec_to_bytes(moon0 + [x0, rng_u, rng_v])
    key = hashlib.sha256(b"OSC-KEY|" + secret_material).digest()
    ciphertext = shake_xor(key, flag)
    firing_code = hashlib.sha256(key + b"|fire").hexdigest()[:32]

    real_ids = set(rng.sample(range(N_SATELLITES), REAL_SATELLITES))
    satellites = []
    for sid in range(N_SATELLITES):
        start = rng.randrange(0, 5)
        step = rng.randrange(1, 4)
        basis_rows = [rnd_vec(rng, 11) for _ in range(COORDS_PER_SAMPLE)]
        bias = rnd_vec(rng, COORDS_PER_SAMPLE)
        coords = []
        indices = [start + step * t for t in range(SAMPLES_PER_SATELLITE)]

        for t, idx in enumerate(indices):
            mask = rng_values[idx + sid + 4]
            if sid in real_ids:
                fval = feature_value(moons, orbits, idx)
                sample = [
                    (mask * dot(row, fval) + bias[j]) % P
                    for j, row in enumerate(basis_rows)
                ]
            else:
                sample = rnd_vec(rng, COORDS_PER_SAMPLE)
            coords.append(sample)

        satellites.append(
            {
                "name": f"sat-{sid:02d}",
                "arange": [start, start + step * SAMPLES_PER_SATELLITE, step],
                "mask_offset": sid + 4,
                "basis": basis_rows,
                "bias": bias,
                "coords": coords,
            }
        )

    public = {
        "title": "Orbital-Strike-Cannon",
        "modulus": P,
        "notes": [
            "RNG beacons are known-bad.",
            "Cannon safety manual: associativity was disabled.",
            "Some satellites died before launch.",
        ],
        "alpha": alpha,
        "beta": beta,
        "outer_a": outer_a,
        "rng_beacons": rng_values[: N_STATES + 8],
        "satellites": satellites,
        "ciphertext": ciphertext,
    }
    return Instance(public=public, firing_code=firing_code, flag=flag)


def public_json(instance: Instance) -> str:
    return json.dumps(instance.public, indent=2, sort_keys=True)


def instance_from_env() -> Instance:
    seed = os.environ.get("TEAM_SEED")
    flag = os.environ.get("FLAG", FLAG.decode()).encode()
    return make_instance(seed, flag)
