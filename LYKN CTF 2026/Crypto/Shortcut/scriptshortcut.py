import math
import hashlib
from Crypto.Util.number import long_to_bytes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# --- 1. Wiener's Attack Implementation ---
def rational_to_contfrac(x, y):
    a = x // y
    pquotients = [a]
    while a * y != x:
        x, y = y, x - a * y
        a = x // y
        pquotients.append(a)
    return pquotients

def convergents_from_contfrac(frac):
    convs = []
    for i in range(len(frac)):
        a = frac[i]
        if i == 0:
            convs.append((a, 1))
        elif i == 1:
            convs.append((a * frac[0] + 1, a))
        else:
            p_n = a * convs[i-1][0] + convs[i-2][0]
            q_n = a * convs[i-1][1] + convs[i-2][1]
            convs.append((p_n, q_n))
    return convs

def wiener_attack(e, n):
    frac = rational_to_contfrac(e, n)
    convs = convergents_from_contfrac(frac)
    for (k, d) in convs:
        if k == 0 or (e * d - 1) % k != 0:
            continue
        phi = (e * d - 1) // k
        b = n - phi + 1
        disc = b * b - 4 * n
        if disc >= 0:
            s = math.isqrt(disc)
            if s * s == disc:
                return d
    return None

# --- 2. Factoring N given d ---
def factor_n(N, e, d):
    k = e * d - 1
    t = k
    while t % 2 == 0:
        t //= 2
    a = 2
    while True:
        x = pow(a, t, N)
        if x == 1 or x == N - 1:
            a += 1
            continue
        while x != 1 and x != N - 1:
            y = x
            x = pow(x, 2, N)
        if x == 1:
            p = math.gcd(y - 1, N)
            q = N // p
            return p, q
        a += 1

def main():
    print("[*] Loading target parameters...")
    # Challenge Inputs
    N = 1761398828897161773351494447963071804253036770612185670452688562297055880855800694234750500773555573618264387691075934148131227572629768789339813317016093872546764388655483446386436319556259080624501055135143999821125931763148615500520535479327412586045428746876306413967467145922134452603929752699558750772743548515628911926083619332491157843578510657646379148120839802831301710471309190777589037852384005646500179109842135245730289123802195501266305598950481539
    e = 1235673825013887766151259644616999138649243594988340250948861559998942182086684902524862558975271742926525214027674919602240936754737254410948965388500096983171591906082794954276208669629135144720068242614045036687786097407340148932415197739028876572911825250177257773242037545918834446797810269812387901185912722894234658377420599268550075051613280243438031162584823237992695066523820949633336708113187342384760279037345310147210420946788632987149935571609637273
    ct_hex = "e7d613d2b53968d319bba1ec94042d4cbfc161d5a1354ca1369e6bfdbf98762116009450a12f01e436"
    nonce_hex = "b55f1c4834e434a1bac8bfbf"
    tag_hex = "ff7fa497919eea9723db131d722552f1"
    
    # --- 3. Execute Wiener's Attack ---
    print("[*] Executing Wiener's Attack to recover d...")
    d = wiener_attack(e, N)
    if not d:
        print("[-] Wiener's attack failed.")
        return
    print(f"[+] Recovered d: {d}")

    # --- 4. Factor N and calculate missing parameters ---
    print("\n[*] Factoring N to find p and q...")
    p, q = factor_n(N, e, d)
    print(f"[+] Recovered p: {p}")
    print(f"[+] Recovered q: {q}")

    g = math.gcd(p - 1, q - 1)
    lambda_n = ((p - 1) * (q - 1)) // g
    
    small_value = 110100480
    S = math.gcd(p + q, small_value)

    # --- 5. Derive AES Key ---
    print("\n[*] Deriving AES key...")
    d_bytes = long_to_bytes(d)
    V_int = d_bytes[:16]

    H1 = hashlib.sha256(V_int).digest()
    H2 = hashlib.sha256(long_to_bytes(S)).digest()
    H3 = hashlib.sha256(long_to_bytes(lambda_n)).digest()

    IKM = H1 + H2 + H3
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"FastLane-RSA-2024",
        info=b"FastLane-AES-Key"
    )
    aes_key = hkdf.derive(IKM)

    # --- 6. Decrypt Flag ---
    print("[*] Decrypting AES-GCM Payload...")
    aesgcm = AESGCM(aes_key)
    
    ct_bytes = bytes.fromhex(ct_hex)
    tag_bytes = bytes.fromhex(tag_hex)
    nonce_bytes = bytes.fromhex(nonce_hex)
    
    full_ciphertext = ct_bytes + tag_bytes
    try:
        flag = aesgcm.decrypt(nonce_bytes, full_ciphertext, None)
        print("\n" + "="*50)
        print(f"FLAG RECOVERED: {flag.decode('utf-8')}")
        print("="*50)
    except Exception as exc:
        print(f"[-] Decryption failed: {exc}")

if __name__ == "__main__":
    main()
