with open("flag.enc", "rb") as f:
    encrypted = f.read()

# The true 8-byte key extracted from your previous run
real_key = b':;\xeb\xb3\x19\x91H\x18'

# Decrypt using the correct key length
decrypted = bytes(
    byte ^ real_key[i % len(real_key)]
    for i, byte in enumerate(encrypted)
)

print(f"Decrypted Flag: {decrypted.decode('utf-8', errors='ignore')}")