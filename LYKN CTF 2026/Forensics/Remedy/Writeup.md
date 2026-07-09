# Forensics Remedy CTF - Writeup
Tool: Strings ( Any platform that can see info pictures file )

Flag: LYKNCTF{Would_Be_Nice_If_Someone_Grow_Up_One_Day}

---

*  So the challenge just give me a simple pictures of an anime girl :v 
*  When i looking at strings info of pictures, there is some suspicous tEXtDescription:
*  "ASCII
Gnxvat Cubgbf Znlor Sha
ntEXtDescription
6d14166842b6ecb67622284a65bde8a87e03344564bde3ab7e1e324b648dc4a87e0a2f4976bdffbd7e0233435ea6cbb45c
biCCPicc"
*  So i think the bytes maybe the flag but it encoded, so i search up
**Ciphertext (Hex):** `6d14166842b6ecb67622284a65bde8a87e03344564bde3ab7e1e324b648dc4a87e0a2f4976bdffbd7e0233435ea6cbb45c`

**Known Format:** `LYKNCTF{...}`

## The Concept: Known Plaintext Attack (KPA) on XOR
*  When a repeating-key XOR cipher is used, we can easily recover the key if we know a portion of the plaintext. The XOR operation has a reversible property:
*  If `Plaintext ⊕ Key = Ciphertext`, then `Ciphertext ⊕ Plaintext = Key`.

*  Since we know the first 8 characters of the plaintext (`LYKNCTF{`), and the flag format is exactly 8 bytes long, it is highly likely that the XOR key is also 8 bytes long.

## Step-by-Step Solution

### Step 1: Extract the Key
*  We take the first 8 bytes of the ciphertext and XOR them with the known plaintext bytes.

1. **Ciphertext (first 8 bytes):** `6d 14 16 68 42 b6 ec b6`
2. **Known Plaintext (`LYKNCTF{`):** `4c 59 4b 4e 43 54 46 7b`
3. **Derived Key:** `21 4d 5d 26 01 e2 aa cd`

### Step 2: Decrypt the Remaining Blocks
*  Now that we have the 8-byte key (`214d5d2601e2aacd`), we can repeatedly XOR it against the entire ciphertext to reveal the hidden flag.

| Block | Ciphertext (Hex) | XOR Key | Decrypted Text |
| :--- | :--- | :--- | :--- |
| 1 | `6d 14 16 68 42 b6 ec b6` | `21 4d 5d 26 01 e2 aa cd` | **`LYKNCTF{`** |
| 2 | `76 22 28 4a 65 bd e8 a8` | `21 4d 5d 26 01 e2 aa cd` | **`Would_Be`** |
| 3 | `7e 03 34 45 64 bd e3 ab` | `21 4d 5d 26 01 e2 aa cd` | **`_Nice_If`** |
| 4 | `7e 1e 32 4b 64 8d c4 a8` | `21 4d 5d 26 01 e2 aa cd` | **`_Someone`** |
| 5 | `7e 0a 2f 49 76 bd ff bd` | `21 4d 5d 26 01 e2 aa cd` | **`_Grow_Up`** |
| 6 | `7e 02 33 43 5e a6 cb b4` | `21 4d 5d 26 01 e2 aa cd` | **`_One_Day`** |
| 7 | `5c` | `21` | **`}`** |

*  Using script python to decrypt
