# Writeup: Shortcut

**Flag:** `LYKNCTF{1a5adf28e9474e28b4b2d3a3c694df13}`

## Challenge Overview
We are provided with a Python script that generates a vulnerable RSA public/private key pair and encrypts a flag using AES-GCM. Along with the public key $(N, e)$ and the AES-encrypted payload, the script provides several mathematical "leakages":
* $p-1 \equiv R_1 \pmod{M_1}$
* $q-1 \equiv R_2 \pmod{M_2}$
* $S = \gcd(p+q, \text{small\_value})$
* $\lambda_n \equiv \lambda_{mod} \pmod{M_3}$

The challenge implies that we need to use these leakages, likely through Coppersmith's method or lattice reduction, to factor $N$ or recover the private exponent $d$.

## Vulnerability Analysis
While the leakages point toward a complex lattice attack, inspecting the RSA generation function in the source code reveals a critical shortcut:

```python
d_target_bits = int(bits * 0.205)
# ...
wiener_bound = isqrt(isqrt(N)) // 3
if d >= wiener_bound:
    continue
