#!/usr/bin/env python3
from pwn import *
import math
from functools import reduce

def get_a(t, m):
    """Finds the multiplier 'a' using the first t_n coprime to m"""
    for i in range(len(t)-1):
        if math.gcd(t[i], m) == 1:
            return (t[i+1] * pow(t[i], -1, m)) % m
    raise Exception("Could not find a coprime difference.")

def solve():
    # Connect to the target server
    host, port = '51.79.140.18', 13470
    conn = remote(host, port)
    
    # Receive output until the list of numbers begins
    conn.recvuntil(b"Here are 12 consecutive outputs:\n")
    
    # Parse the 12 provided states
    s = []
    for i in range(12):
        line = conn.recvline().decode().strip()
        val = int(line.split(' = ')[1])
        s.append(val)
        
    print(f"[*] Recovered states: {s[:3]}...")
    
    # Step 1: Calculate differences t_n = s_{n+1} - s_n
    t = [s[i+1] - s[i] for i in range(len(s)-1)]
    
    # Step 2: Calculate u_n = t_{n+2}*t_n - t_{n+1}^2
    u = [t[i+2]*t[i] - t[i+1]**2 for i in range(len(t)-2)]
    
    # Step 3: Recover m (GCD of all u_n)
    m = reduce(math.gcd, u)
    print(f"[*] Recovered m: {m}")
    
    # Step 4: Recover a
    a = get_a(t, m)
    print(f"[*] Recovered a: {a}")
    
    # Step 5: Recover c
    c = (s[1] - a * s[0]) % m
    print(f"[*] Recovered c: {c}")
    
    # Step 6: Predict the 13th state (out[12])
    out12 = (a * s[-1] + c) % m
    print(f"[*] Predicted out[12]: {out12}")
    
    # Send the predicted state back to the server
    conn.recvuntil(b"out[12] = ")
    conn.sendline(str(out12).encode())
    
    # Print the resulting flag
    print("\n[+] Flag Output:")
    print(conn.recvall(timeout=2).decode())

if __name__ == "__main__":
    solve()
