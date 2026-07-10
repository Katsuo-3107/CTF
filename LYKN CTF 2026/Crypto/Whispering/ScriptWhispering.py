from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import HKDF
from Crypto.Util.Padding import unpad

# 1. Challenge Parameters
N = 127
q = 2048
q_prime = 2053
salt_str = "lyknctf-2026"

# 2. Reconstructing the Algebraic Signature from Side-Channel
f_sum = -6 + 1  # -5
g_sum = 3 + 11  # 14
V = (f_sum * g_sum) % q_prime  # 1983

# 3. Deriving the Key (Identical to challenge server)
ikm = (
    V.to_bytes(4, "big")
    + N.to_bytes(2, "big")
    + q.to_bytes(2, "big")
    + salt_str.encode("utf-8")
)

key = HKDF(
    master=ikm,
    key_len=32,
    salt=str(N).encode("utf-8"),
    hashmod=SHA256,
)

# 4. Decrypting the Flag from public.json
ciphertext = bytes.fromhex("5d1a0bfd64555969c3e0e08608d2c9fe731582cae0db12ad14e182897dda53103db13e73b5c653bfd042181d3c45c645")
iv = bytes.fromhex("d8322215dcb427164edf8b6b235c2508")

cipher = AES.new(key, AES.MODE_CBC, iv)
plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

print("[+] Decrypted Flag:", plaintext.decode("utf-8"))
