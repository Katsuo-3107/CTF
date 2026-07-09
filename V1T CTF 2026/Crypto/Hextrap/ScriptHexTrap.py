import math
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

n = 14884800451955950069113725819582523452585625680964352925405287702945124871438012573975746640883842103042984750487942943421571681652252352348393111535120212824144300409490952092961805337273025660675021221223760281669849366431560452175211927388902210616902198236233541611572685032003626072414569507837860098262478925981342654902998086422642563797070782607595233706836044689489106803015979
e = 65537
c = 0x25fed2dac3d3562dc8824679a10693b6fef217da7eff6148837c4e5cf26ad9a7a5bb61de9cf0acbc260fb217cfd41d3b106b5c60de887e46645f2d8ab209e13ed9fdb2e1775353772976a8741da05b11931c881a763b6ac41e5516e323fd2db3001a1a4c0fe55bd31071cd9f81e830b49a80846a7c859b669cfdbfe41951fe46fdf529b3dc6924f949264641cc0b9429f423c2d2a8334a5dbb879f32c918a87b

# This exception is our "trapdoor" to catch the factor during scalar multiplication
class FoundFactor(Exception):
    def __init__(self, p):
        self.p = p

def invert(v, n):
    """
    Attempts to find the modular inverse. If gcd(v, n) is not 1, 
    we have successfully factored n!
    """
    g = math.gcd(v, n)
    if 1 < g < n:
        raise FoundFactor(g)
    if g == n:
        raise ValueError("Division by zero mod n")
    return pow(v, -1, n)

def ec_add(P, Q, n):
    """Adds two points on the elliptic curve y^2 = x^3 + D."""
    if P is None: return Q
    if Q is None: return P
    
    x1, y1 = P
    x2, y2 = Q
    
    if x1 == x2 and y1 != y2:
        return None
    
    if x1 == x2:
        # Point doubling: lambda = (3x^2) / (2y)
        num = (3 * x1 * x1) % n
        den = (2 * y1) % n
    else:
        # Point addition: lambda = (y2 - y1) / (x2 - x1)
        num = (y2 - y1) % n
        den = (x2 - x1) % n
    
    lam = (num * invert(den, n)) % n
    
    x3 = (lam * lam - x1 - x2) % n
    y3 = (lam * (x1 - x3) - y1) % n
    return (x3, y3)

def ec_mul(k, P, n):
    """Multiplies a point P by scalar k using double-and-add."""
    R = None
    Q = P
    while k > 0:
        if k & 1:
            R = ec_add(R, Q, n)
        Q = ec_add(Q, Q, n)
        k >>= 1
    return R

def primes_upto(limit):
    """Generates primes up to a given limit using a basic sieve."""
    sieve = [True] * (limit + 1)
    for p in range(2, math.isqrt(limit) + 1):
        if sieve[p]:
            for i in range(p * p, limit + 1, p):
                sieve[i] = False
    return [p for p in range(2, limit + 1) if sieve[p]]

SMOOTH_BOUND = 2**15

print("[*] Computing smooth multiplier (M)...")
primes = primes_upto(SMOOTH_BOUND)
M = 1
for p_smooth in primes:
    power = 1
    while p_smooth ** (power + 1) <= SMOOTH_BOUND:
        power += 1
    M *= (p_smooth ** power)

print("[*] Starting pure Python ECM search...")
p = None
y_val = 2

# We test random curves y^2 = x^3 + D by picking a point (1, y_val)
# and letting D = y_val^2 - 1. We just iterate y_val until we hit the right trace.
while p is None:
    try:
        P = (1, y_val)
        # Attempt scalar multiplication; if the order is smooth, invert() will fail and throw the factor
        _ = ec_mul(M, P, n)
        y_val += 1
    except FoundFactor as e:
        p = e.p
        print(f"[+] Found factor p: {p}")

# Now that we have p, derive q and the private key
q = n // p
phi = (p - 1) * (q - 1)
d = pow(65537, -1, phi)

key = RSA.construct((n,65537, d, p, q))
cipher = PKCS1_OAEP.new(key)
flag = cipher.decrypt(bytes.fromhex(f"{c:x}"))

print("-" * 30)
print(f"[+] Flag: {flag.decode()}")
