#!/usr/bin/env python3

with open("key", "rb") as keyf:
    key = keyf.read()

if not key:
    raise ValueError("The key file is empty")

with open("flag.txt", "rb") as flagf:
    flag = flagf.read()

encrypted = bytes(
    byte ^ key[i % len(key)]
    for i, byte in enumerate(flag)
)

with open("flag.enc", "wb") as flagencf:
    flagencf.write(encrypted)
