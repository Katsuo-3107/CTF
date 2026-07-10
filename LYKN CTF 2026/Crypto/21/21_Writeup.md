# LYKNCTF — 21 Writeup

A comprehensive walk-through on breaking a Linear Congruential Generator (LCG) when the raw internal states are leaked.

## Challenge Overview

* **Category:** Cryptography
* **Target:** `nc 51.79.140.18 13470`

### Description
The server presents us with a custom random number generator:
$$s_{n+1} = (a \cdot s_n + c) \pmod m$$

Where the parameters $a$, $c$, $m$, and the initial seed are completely secret. We are provided 12 consecutive outputs and tasked with predicting the 13th output (`out[12]`) before the server times out.

---

## Vulnerability Analysis

A **Linear Congruential Generator (LCG)** is entirely predictable if it outputs its raw internal states without truncation or hashing. Given 12 consecutive states $s_0, s_1, \dots, s_{11}$, we can mathematically recover all secret parameters ($m, a, c$) through a series of algebraic steps.

### Step 1: Eliminating the Increment ($c$)
By defining the differences between consecutive states as $t_n = s_{n+1} - s_n$, we can subtract the formulas to eliminate the constant offset $c$:
$$s_{n+2} - s_{n+1} = (a \cdot s_{n+1} + c) - (a \cdot s_n + c) \pmod m$$
$$t_{n+1} \equiv a \cdot t_n \pmod m$$

### Step 2: Eliminating the Multiplier ($a$)
Using the relation $t_{n+1} \equiv a \cdot t_n \pmod m$, we can look at consecutive differences to remove $a$:
$$t_{n+2} \equiv a \cdot t_{n+1} \pmod m$$
$$t_{n+1}^2 \equiv a^2 \cdot t_n^2 \equiv t_{n+2} \cdot t_n \pmod m$$

By rearranging, we define a sequence of values $u_n$:
$$u_n = |t_{n+2} \cdot t_n - t_{n+1}^2|$$

Because $t_{n+2} \cdot t_n - t_{n+1}^2 \equiv 0 \pmod m$, **every value $u_n$ must be an exact multiple of the secret modulus $m$**.

### Step 3: Recovering the Modulus ($m$)
Since every $u_n$ is a multiple of $m$, the true value of $m$ is simply the Greatest Common Divisor (GCD) of all calculated $u_n$ values:
$$m = \gcd(u_0, u_1, u_2, \dots, u_n)$$

### Step 4: Recovering Multiplier ($a$) and Increment ($c$)
Once $m$ is known, we find a difference $t_i$ that is coprime to $m$ ($\gcd(t_i, m) = 1$) to compute the modular inverse:
$$a = t_{i+1} \cdot t_i^{-1} \pmod m$$

With $a$ and $m$ recovered, $c$ is solved directly using the first state transition:
$$c = s_1 - (a \cdot s_0) \pmod m$$

---

## Exploit Automation Script

Because the target server enforces a rapid timeout, we automate the connection, calculation, and response using Python's `pwntools` library.

```python
#!/usr/bin/env python3
from pwn import *
import math
from functools import reduce

def get_modular_multiplier(t, m):
    """Finds the multiplier 'a' using the first t_n coprime to m"""
    for i in range(len(t) - 1):
        if math.gcd(t[i], m) == 1:
            return (t[i+1] * pow(t[i], -1, m)) % m
    raise ValueError("Could not find a difference coprime to the modulus m.")

def solve():
    # Connect to remote instance
    host, port = '51.79.140.18', 13470
    conn = remote(host, port)
    
    # Fast-forward to the data sequence
    conn.recvuntil(b"Here are 12 consecutive outputs:\n")
    
    # Parse out all 12 provided outputs
    states = []
    for _ in range(12):
        line = conn.recvline().decode().strip()
        val = int(line.split(' = ')[1])
        states.append(val)
        
    print(f"[*] Parsed {len(states)} internal states successfully.")
    
    # Step 1: Calculate state transitions (t_n)
    t = [states[i+1] - states[i] for i in range(len(states) - 1)]
    
    # Step 2: Formulate zero-congruences modulo m (u_n)
    u = [abs(t[i+2] * t[i] - t[i+1]**2) for i in range(len(t) - 2)]
    
    # Step 3: Recover the secret modulus m via GCD
    m = reduce(math.gcd, u)
    print(f"[+] Recovered Modulus (m): {m}")
    
    # Step 4: Recover the multiplier (a)
    a = get_modular_multiplier(t, m)
    print(f"[+] Recovered Multiplier (a): {a}")
    
    # Step 5: Recover the increment (c)
    c = (states[1] - a * states[0]) % m
    print(f"[+] Recovered Increment (c): {c}")
    
    # Step 6: Predict the next output state (out[12])
    predicted_next = (a * states[-1] + c) % m
    print(f"[*] Predicted out[12] state: {predicted_next}")
    
    # Submit prediction to server
    conn.recvuntil(b"out[12] = ")
    conn.sendline(str(predicted_next).encode())
    
    # Print the resulting flag output
    print("\n[+] Response from server:")
    print(conn.recvall(timeout=2).decode())

if __name__ == "__main__":
    solve()
