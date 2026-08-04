def solve_real_flag():
    # =========================================================================
    # 1. Populated Target Ciphertext Bytes (Parsed from Little-Endian)
    # =========================================================================
    
    # Extracted right-to-left from 32F47EA0EB7DB2880F84C16C1B790523h
    xmm_6460 = [
        0x23, 0x05, 0x79, 0x1B, 0x6C, 0xC1, 0x84, 0x0F, 
        0x88, 0xB2, 0x7D, 0xEB, 0xA0, 0x7E, 0xF4, 0x32
    ] # First 16 bytes
    
    # Extracted right-to-left from 17456A6A3A3642DD16BF26C5C170F5C6h
    xmm_6470 = [
        0xC6, 0xF5, 0x70, 0xC1, 0xC5, 0x26, 0xBF, 0x16, 
        0xDD, 0x42, 0x36, 0x3A, 0x6A, 0x6A, 0x45, 0x17
    ] # Next 16 bytes
    
    # Taken from .rodata starting at index 32 (address 0x555555556440)
    expected_3 = [
        0xF4, 0x4C, 0xCD, 0x84, 0xAE, 0x27, 0x8C, 0xC8, 0x38
    ] # Final 9 bytes

    # Merge all components together into the 41-byte target ciphertext array
    v70 = xmm_6460 + xmm_6470 + expected_3

    # Hardcoded XOR key arrays found in the binary
    key_part_b_4 = [0x5B, 0x75, 0xB4, 0x7B, 0xCB, 0x5D, 0x73, 0xE6]
    key_part_a_5 = [0x19, 0xA4, 0xC7, 0x52, 0x6E, 0x01, 0x9B, 0xF0]

    flag = [0] * 41

    # Reverse the operations from the final step back to the beginning
    for i in range(41):
        # 1. Find where the character was shuffled to on the stack
        dest_idx = (i * 13) % 41
        encrypted_byte = v70[dest_idx]
        
        # 2. Re-calculate the exact dynamic salt used for index i
        salt = (i * 11) ^ 0x23
        
        # 3. Undo the Salt Addition (keeping within 8-bit bounds)
        rotated_byte = (encrypted_byte - salt) & 0xFF
        
        # 4. Undo Bit Rotation Left (ROL) by executing a Bit Rotation Right (ROR)
        shift = (i % 7) + 1
        v32 = ((rotated_byte >> shift) | (rotated_byte << (8 - shift))) & 0xFF
        
        # 5. Undo the structural XOR key streaming
        flag[i] = v32 ^ key_part_b_4[i & 7] ^ key_part_a_5[i & 7]

    print("\n[+] Success! Decrypted Flag:")
    print("".join(chr(x) for x in flag))

if __name__ == "__main__":
    solve_real_flag()