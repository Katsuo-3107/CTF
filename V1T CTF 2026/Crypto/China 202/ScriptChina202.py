import zlib

cipher_flag = bytes.fromhex(
    "72901442adade9c53b7cb386eeb8b6765d42dbc58ec6d442e77057b7d5d2724afc2f4e232df02f9ff050"
)

leak1 = [123, 38, 92, 78, 207, 178, 116, 75, 141, 163]
leak2 = [
    4226,
    36575,
    42265,
    42988,
    32134,
    53660,
    36202,
    48971,
    61905,
    20150,
    45745,
]
leak3 = [10, 18, 13, 17, 17, 19, 14, 13, 18, 16, 15]
partial_crc = 0x32C29A97

# Pad ciphertext to align with 11 32-bit words (44 bytes total)
padded_cf = cipher_flag + b"\x00\x00"
C = [int.from_bytes(padded_cf[i * 4 : (i + 1) * 4], "big") for i in range(11)]

# STEP 1: Recover independent word candidates
candidates = []
for i in range(11):
    valid = []
    is_last = (i == 10)
    c_val = C[i]

    for L in range(65536):
        P = (L * 0x45D9F3B) & 0xFFFF
        H = P ^ leak2[i]
        W = (H << 16) | L

        if bin(W).count("1") == leak3[i]:
            pt_int = W ^ c_val
            pt_bytes = pt_int.to_bytes(4, "big")
            if is_last:
                pt_bytes = pt_bytes[:2]  # Flag is 42 bytes; word 10 only uses 2

            if all(32 <= b <= 126 for b in pt_bytes):
                valid.append(W)
    candidates.append(valid)

# STEP 2: Depth-First Trellis Search via Leak 1
surviving_paths = []


def trellis_walk(idx, current_path):
    if idx == 11:
        surviving_paths.append(current_path)
        return

    prev_word = current_path[-1]
    target_leak = leak1[idx - 1]

    for next_word in candidates[idx]:
        # Evaluated using Python's native unbounded big-ints
        if (((prev_word ^ next_word) * 0x9E3779B1 >> 24) & 0xFF) == target_leak:
            trellis_walk(idx + 1, current_path + [next_word])


for w0 in candidates[0]:
    trellis_walk(1, [w0])

# STEP 3: Verify against partial CRC32
for path in surviving_paths:
    keystream = b"".join(w.to_bytes(4, "big") for w in path)[: len(cipher_flag)]
    flag = bytes(x ^ y for x, y in zip(cipher_flag, keystream))

    if zlib.crc32(flag[:16]) == partial_crc:
        print(f"\n[+] CRACKED FLAG: {flag.decode('ascii')}")
