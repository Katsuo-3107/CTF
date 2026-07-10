# Whispering - LYKNCTF 2026 Crypto Writeup

## Challenge Overview
* **Category:** Cryptography
* **Challenge Name:** Whispering
* **Flag:** `LYKNCTF{93158f897986434aaff0a9b22281e0d6}`

The challenge implements a custom **NTRU-like lattice cryptosystem**. The server generates a keypair consisting of two private ternary polynomials, $f(x)$ and $g(x)$, and derives a symmetric AES key from their properties to encrypt the flag.

We are given two endpoints:
1. `/public.json`: Public parameters ($N$, $q$, $q'$), the public key $h(x) \equiv g(x) \cdot f(x)^{-1} \pmod{q}$, and the AES-CBC encrypted flag payload.
2. `/side_channel.json`: Leaks structural information regarding the coefficient sums of the private keys.

---

## Deep-Dive Mathematical Analysis

While the challenge mimics an asymmetric NTRU lattice setup where an attacker would normally be forced to use lattice basis reduction (such as the LLL or BKZ algorithms) to recover the private keys from $h(x)$, a critical shortcut exists in the key derivation function.

### 1. The Algebraic Signature and Trace Map
The symmetric AES key is derived from an "algebraic signature" denoted as $V$. Looking at the source code, $V$ is defined as the sum of the coefficients of the polynomial product $f(x) \cdot g(x)$ computed over the field $\mathbb{Z}_{q'}$ where $q' = 2053$:

Let $P(x) = \sum_{i=0}^{N-1} c_i x^i$ be a polynomial in the ring $\mathbb{Z}[x]/(x^N - 1)$. Notice what happens when we evaluate this polynomial at $x = 1

$$P(1) = c_0(1)^0 + c_1(1)^1 + c_2(1)^2 + \dots + c_{N-1}(1)^{N-1} = \sum_{i=0}^{N-1} c_i$$

Evaluating a polynomial at $1$ is identical to summing its coefficients.

2. The Ring Homomorphism Property

Polynomial evaluation at a specific point $\alpha$ is a ring homomorphism from the polynomial ring $\mathbb{Z}[x]$ to the underlying base ring $\mathbb{Z}$ (or $\mathbb{Z}_{q'}$). This means that evaluation preserves both addition and multiplication operations.

For any two polynomials $f(x)$ and $g(x)$, if we define their product as $H(x) = f(x) \cdot g(x)$, the evaluation at $x=1$ satisfies:

$$H(1) = f(1) \cdot g(1)$$

Substituting our coefficient-sum identity into this property, we establish that:

$$\sum (f \cdot g) \equiv \left( \sum f \right) \cdot \left( \sum g \right) \pmod{q'}$$

Thus, to calculate the value $V$, we do not need to find the specific polynomials $f(x)$ and $g(x)$. We only need to find the scalar sum of their respective coefficients.

3. Resolving the Side-Channel and Center-Lifting

The /side_channel.json endpoint leaks the sums of the even-indexed and odd-indexed coefficients for both private keys modulo $127$:

```json
{
  "constraint_modulus": 127,
  "constraints": {
    "f_even_sum_mod_127": 121,
    "f_odd_sum_mod_127": 1,
    "g_even_sum_mod_127": 3,
    "g_odd_sum_mod_127": 11
  }
}
```

Since the polynomials $f(x)$ and $g(x)$ are generated as ternary polynomials, their coefficients are strictly restricted to the set $\{-1, 0, 1\}$. The maximum degree is $N = 127$.

Even if every single coefficient in a partition was maximum ($1$ or $-1$), the absolute value of the sum can never exceed the total number of coefficients ($\approx 127/2 = 63$ coefficients per even/odd partition). Because the true integer sum $S$ is strictly bounded by $|S| \le 63$, and the modular reduction happened modulo $M = 127$, the value has not wrapped around multiple times.

We can perform a standard center-lift to reconstruct the exact integer values from the modular values:

$$\text{If } x > \lfloor M/2 \rfloor, \quad x \leftarrow x - M$$

Applying this to our leaked values:

$f_{\text{even}} \equiv 121 \pmod{127} \implies 121 > 63 \implies 121 - 127 = -6$

$f_{\text{odd}} \equiv 1 \pmod{127} \implies 1 \le 63 \implies 1$

$g_{\text{even}} \equiv 3 \pmod{127} \implies 3 \le 63 \implies 3$

$g_{\text{odd}} \equiv 11 \pmod{127} \implies 11 \le 63 \implies 11$

4. Computing the Final Key Secret
   
With the precise integers recovered, we combine the partitions to compute the total coefficient sums $f(1)$ and $g(1)$:

$$\sum f = f_{\text{even}} + f_{\text{odd}} = -6 + 1 = -5$$

$$\sum g = g_{\text{even}} + g_{\text{odd}} = 3 + 11 = 14$$

Finally, we apply our homomorphic multiplication identity over $\mathbb{Z}_{2053}$:

$$V \equiv (\sum f) \cdot (\sum g) \pmod{2053}$$

$$V \equiv -5 \cdot 14 = -70 \pmod{2053}$$

$$V = 2053 - 70 = 1983$$

The public NTRU key lattice is completely bypassed.
