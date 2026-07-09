# V1T{7fK9xL2mQp8ZrT5uWc3Yd6Hs0AaBbCcDdEeFf} - Crypto Writeup

## Challenge Overview
* **Category:** Crypto
* **Difficulty:** Medium
* **Description:** A ZUC-based stream cipher with three leaked internal state transformations.

## Vulnerability Analysis
The challenge uses a stream cipher but inadvertently leaks mathematical properties of the keystream words ($W_i$):
1. **`leak2` (Algebraic):** Allows recovery of 32-bit state words using a 16-bit brute force (due to modulo $2^{16}$ properties).
2. **`leak3` (Hamming Weight):** Reduces the state space by checking the number of '1' bits.
3. **`leak1` (Trellis/Transition):** Defines a state-transition relationship between $W_i$ and $W_{i+1}$.

## Exploitation Steps
1. **Pre-computation:** Iterate through all $2^{16}$ possible lower-half values for each word, applying `leak2` and `leak3` to filter valid 32-bit candidates.
2. **Trellis Pathfinding:** Use a Depth-First Search (DFS) to chain candidates that satisfy the `leak1` relationship.
3. **Verification:** Validate the candidate plaintexts against the provided `partial_crc`.
