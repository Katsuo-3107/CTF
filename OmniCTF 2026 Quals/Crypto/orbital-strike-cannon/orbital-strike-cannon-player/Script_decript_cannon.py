#!/usr/bin/env python3
import socket
import json
import hashlib
import ssl
import copy

P = (1 << 127) - 1
N_STATES = 34

# --- Octonion & Field Arithmetic ---
def add(a, b): return [(x + y) % P for x, y in zip(a, b)]
def sub(a, b): return [(x - y) % P for x, y in zip(a, b)]
def q_conj(a): return [a[0], (-a[1]) % P, (-a[2]) % P, (-a[3]) % P]
def q_mul(a, b):
    a0, a1, a2, a3 = a
    b0, b1, b2, b3 = b
    return [
        (a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3) % P,
        (a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2) % P,
        (a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1) % P,
        (a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0) % P,
    ]
def o_conj(x): return q_conj(x[:4]) + [(-v) % P for v in x[4:]]
def o_mul(x, y):
    a, b = x[:4], x[4:]
    c, d = y[:4], y[4:]
    left = sub(q_mul(a, c), q_mul(q_conj(d), b))
    right = add(q_mul(d, a), q_mul(b, q_conj(c)))
    return left + right

def basis(i):
    out = [0] * 8
    out[i] = 1
    return out

def transpose(m): return [list(row) for row in zip(*m)]
def mat_left(o): return transpose([o_mul(o, basis(i)) for i in range(8)])
def mat_right(o): return transpose([o_mul(basis(i), o) for i in range(8)])
def mat_mul(a, b):
    rows, inner, cols = len(a), len(b), len(b[0])
    return [[sum(a[i][k] * b[k][j] for k in range(inner)) % P for j in range(cols)] for i in range(rows)]

def rng_octonion(r, i):
    a, b, c, d = r[i], r[i + 1], r[i + 2], r[i + 3]
    return [1, a, b, c, d, (a * b + c) % P, (b * c + d) % P, (a * d + b * c + 7) % P]

# --- State Reconstruction ---
def build_state_expressions(alpha, beta, outer_a, rng_values):
    states = []
    cur = [[1 if i == j else 0 for j in range(10)] for i in range(10)]
    states.append(cur)

    for i in range(N_STATES + 3):
        r_oct = rng_octonion(rng_values, i)
        transition = mat_mul(mat_right(alpha), mat_left(r_oct))

        step = [[0] * 10 for _ in range(10)]
        for row in range(8):
            for col in range(8):
                step[row][col] = transition[row][col]
            step[row][9] = beta[row]

        for col in range(8):
            step[8][col] = 1
        step[8][8] = outer_a
        step[8][9] = rng_values[i]
        step[9][9] = 1

        cur = mat_mul(step, cur)
        states.append(cur)
    return states

def feature_rows(states, i):
    rows = [states[i][j] for j in range(8)]
    rows.append(states[i][8])
    rows.append(states[i + 1][8])
    rows.append(states[i + 2][8])
    return rows

# --- Gaussian Elimination ---
def solve_linear_system(matrix, num_vars):
    M = copy.deepcopy(matrix)
    rows = len(M)
    cols = num_vars + 1
    
    r_idx = 0
    for col in range(num_vars):
        pivot = -1
        for r in range(r_idx, rows):
            if M[r][col] != 0:
                pivot = r
                break
        if pivot == -1: continue
        
        M[r_idx], M[pivot] = M[pivot], M[r_idx]
        inv_val = pow(M[r_idx][col], P - 2, P)
        for c in range(col, cols):
            M[r_idx][c] = (M[r_idx][c] * inv_val) % P
            
        for r in range(rows):
            if r != r_idx and M[r][col] != 0:
                factor = M[r][col]
                for c in range(col, cols):
                    M[r][c] = (M[r][c] - factor * M[r_idx][c]) % P
        r_idx += 1
        
    if r_idx < num_vars: return None
    for r in range(r_idx, rows):
        if M[r][num_vars] != 0: return None
    return [M[r][num_vars] for r in range(num_vars)]

# --- Cryptography ---
def int_to_bytes(x): return x.to_bytes(16, "big")
def vec_to_bytes(v): return b"".join(int_to_bytes(x % P) for x in v)
def shake_xor(key, data):
    stream = hashlib.shake_256(key + b"|stream").digest(len(data))
    return bytes(a ^ b for a, b in zip(data, stream))

# --- Main Exploit Flow ---
def connect_and_solve(host, port):
    print(f"[*] Connecting to {host}:{port} with SSL...")
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    secure_sock = context.wrap_socket(sock, server_hostname=host)
    secure_sock.connect((host, port))
    
    print("[*] Connected. Receiving telemetry...")
    buffer = b""
    while True:
        chunk = secure_sock.recv(4096)
        if not chunk: break
        buffer += chunk
        if b"Submit firing code:" in buffer:
            break
            
    output = buffer.decode()
    
    start_idx = output.find("{")
    end_idx = output.rfind("}") + 1
    data = json.loads(output[start_idx:end_idx])
    
    print("[+] Telemetry parsed. Cracking RNG...")
    S = data["rng_beacons"]
    # Recover secret LCG parameters (u, v)
    u = ((S[2] - S[1]) * pow(S[1] - S[0], P - 2, P)) % P
    v = (S[1] - u * S[0]) % P
    print(f"    u = {u}\n    v = {v}")

    print("[*] Modeling state transitions...")
    states = build_state_expressions(data["alpha"], data["beta"], data["outer_a"], S)

    print("[*] Constructing equations from satellites...")
    sat_equations = []
    for sid, sat in enumerate(data["satellites"]):
        eqs = []
        start, end, step = sat["arange"]
        indices = [start + step * t for t in range(5)]
        
        for t, idx in enumerate(indices):
            mask = S[sat["mask_offset"] + idx]
            inv_mask = pow(mask, P - 2, P)
            F_mat = feature_rows(states, idx) 
            
            for j in range(3):
                basis_row = sat["basis"][j]
                bias = sat["bias"][j]
                sample = sat["coords"][t][j]
                
                # Multiply basis by feature matrix to get LHS vector
                LHS_vec = [sum(basis_row[m] * F_mat[m][k] for m in range(11)) % P for k in range(10)]
                
                row = LHS_vec[:9]
                rhs = ((sample - bias) * inv_mask - LHS_vec[9]) % P
                row.append(rhs)
                eqs.append(row)
        sat_equations.append(eqs)

    print("[*] Filtering noisy satellites and solving system...")
    solution = None
    for s1 in range(7):
        for s2 in range(s1 + 1, 7):
            combined_matrix = sat_equations[s1] + sat_equations[s2]
            sol = solve_linear_system(combined_matrix, 9)
            if sol:
                solution = sol
                break
        if solution: break

    if not solution:
        print("[-] Exploit failed: No consistent satellite data found.")
        return

    moon0 = solution[:8]
    x0 = solution[8]
    print(f"[+] Initial state recovered!\n    x0 = {x0}")

    # Reconstruct the crypto key
    secret_material = vec_to_bytes(moon0 + [x0, u, v])
    key = hashlib.sha256(b"OSC-KEY|" + secret_material).digest()
    
    # Decrypt flag and generate firing code
    ciphertext = bytes.fromhex(data["ciphertext"])
    flag = shake_xor(key, ciphertext).decode('utf-8', errors='ignore')
    firing_code = hashlib.sha256(key + b"|fire").hexdigest()[:32]
    
    print(f"\n[+] Local Decryption Success!")
    print(f"    FLAG: {flag}")
    print(f"    CODE: {firing_code}")

    print("\n[*] Sending firing code to server...")
    secure_sock.sendall((firing_code + "\n").encode())
    
    response = secure_sock.recv(4096).decode()
    print("--- Server Response ---")
    print(response.strip())

if __name__ == "__main__":
    HOST = "orbital-7a8bc3ee25d9.inst.omnictf.com"
    PORT = 1337
    connect_and_solve(HOST, PORT)
