with open("flag.enc", "rb") as f:
    encrypted = f.read()

known_prefix = b"bushbash{" 

# 1. Recover the key by XORing the ciphertext with the known prefix
recovered_key = bytes(
    c ^ p for c, p in zip(encrypted[:len(known_prefix)], known_prefix)
)

print(f"Recovered Key: {recovered_key}")

# 2. If the key is repeating, it might be shorter than the prefix.
# You may need to manually inspect the output to find the exact repeating pattern.
# Assuming the recovered key IS the full repeating key:
decrypted = bytes(
    byte ^ recovered_key[i % len(recovered_key)]
    for i, byte in enumerate(encrypted)
)

print(f"Decrypted Flag: {decrypted.decode('utf-8', errors='ignore')}")