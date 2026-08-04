# Xored - WEEK 8 - 9 Cryptography cơ bản
Tool: Python 3

Flag: **bushbash{to-x0r-or-nOt-To-Xor}**

---
## 1. Xác Định Cấu Trúc File

Đầu tiên, phân tích file mã nguồn Python `xored.py` được cung cấp để xác định cơ chế mã hóa và các thành phần dữ liệu trong bài toán.

Nội dung mã nguồn gốc `xored.py`:

```python
#!/usr/bin/env python3

with open("key", "rb") as keyf:
    key = keyf.read()

if not key:
    raise ValueError("The key file is empty")

with open("flag.txt", "rb") as flagf:
    flag = flagf.read()

encrypted = bytes(
    byte ^ key[i % len(key)]
    for i, byte in enumerate(flag)
)

with open("flag.enc", "wb") as flagencf:
    flagencf.write(encrypted)

```

Kết quả phân tích sơ bộ thu được như sau:

* **Định dạng file:** Python Script (`xored.py`) & Encrypted Binary Data (`flag.enc`)
* **Thuật toán mã hóa:** Repeating-Key XOR (Mã hóa XOR lặp khóa)
* **Độ dài khóa (Key Length):** Chưa biết (file `key` không được cung cấp)
* **Đầu ra:** File đã mã hóa `flag.enc`

### Nhận xét

Từ kết quả phân tích mã nguồn có thể đưa ra một số nhận xét:

* Chương trình thực hiện mã hóa từng byte của `flag` với byte tương ứng của `key` theo chu kỳ $i \pmod{\vert{}K\vert{}}$.
* Phép toán XOR ($\oplus$) có tính chất đảo (Self-Inverse): nếu $C = P \oplus K$ thì $P = C \oplus K$ và $K = C \oplus P$.
* Do định dạng flag chuẩn của giải đấu luôn tuân theo mẫu `bushbash{...}`, ta hoàn toàn có thể áp dụng kỹ thuật **Known-Plaintext Attack** để khôi phục khóa mà không cần có file `key` ban đầu.

---

## 2. Phân Tích Toán Học (Mathematical Foundations)

Để giải quyết triệt để bài toán mã hóa XOR lặp khóa, ta cần nắm rõ các tính chất đại số cơ bản của phép toán Exclusive-OR ($\oplus$).

### 2.1 Bảng Chân Trị & Tính Chất Cơ Bản

Phép XOR làm việc trên từng bit dữ liệu theo quy tắc:

$$0 \oplus 0 = 0$$

$$0 \oplus 1 = 1$$

$$1 \oplus 0 = 1$$

$$1 \oplus 1 = 0$$

Đối với các chuỗi byte $A, B, C$, phép XOR thỏa mãn các tiên đề đại số:

1. **Giao hoán (Commutativity):**

$$A \oplus B = B \oplus A$$


2. **Kết hợp (Associativity):**

$$(A \oplus B) \oplus C = A \oplus (B \oplus C)$$


3. **Phần tử trung hòa ($0$):**

$$A \oplus 0 = A$$


4. **Tính chất tự đảo (Self-Inverse Property):**

$$A \oplus A = 0$$



### 2.2 Chứng Minh Giải Mã

Cho byte rõ thứ $i$ là $P_i$ và byte khóa tương ứng là $K_{i \pmod{\vert{}K\vert{}}}$, byte mã hóa $C_i$ được tính bằng:

$$C_i = P_i \oplus K_{i \pmod{\vert{}K\vert{}}}$$

Để giải mã, ta XOR byte mã $C_i$ với đúng byte khóa $K_{i \pmod{\vert{}K\vert{}}}$ đó:

$$C_i \oplus K_{i \pmod{\vert{}K\vert{}}} = (P_i \oplus K_{i \pmod{\vert{}K\vert{}}}) \oplus K_{i \pmod{\vert{}K\vert{}}}$$

Áp dụng tính chất kết hợp và tự đảo:

$$= P_i \oplus (K_{i \pmod{\vert{}K\vert{}}} \oplus K_{i \pmod{\vert{}K\vert{}}})$$

$$= P_i \oplus 0$$

$$= P_i$$

Như vậy, **mã hóa và giải mã XOR là hai thao tác hoàn toàn giống nhau**.

### 2.3 Khôi Phục Khóa Từng Phần (Known-Plaintext Attack)

Nhờ tính chất tự đảo, nếu biết trước một đoạn Plaintext $P_{0 \dots m-1}$ (ví dụ tiền tố flag `bushbash{`), ta suy ra trực tiếp các byte khóa tương ứng bằng cách XOR Plaintext đã biết với Ciphertext:

$$C_i \oplus P_i = (P_i \oplus K_{i \pmod{\vert{}K\vert{}}}) \oplus P_i = K_{i \pmod{\vert{}K\vert{}}}$$

---

## 3. Quá Trình Khai Thác & Bypass Khóa

### Bước 1: Khai Thác Tiền Tố Flag (Prefix Leakage)

Flag của giải đấu có định dạng chuẩn là `bushbash{...}`. Đoạn tiền tố `bushbash{` có độ dài **9 bytes**:

* $P[0..8] =$ `b"bushbash{"`

Chạy đoạn script thử nghiệm để trích xuất 9 bytes khóa đầu tiên:

```python
#!/usr/bin/env python3

with open("flag.enc", "rb") as f:
    encrypted = f.read()

known_prefix = b"bushbash{"

recovered = bytes(c ^ p for c, p in zip(encrypted[:len(known_prefix)], known_prefix))
print(f"Recovered Key ({len(recovered)} bytes): {recovered}")

```

Kết quả thu được:

```text
Recovered Key (9 bytes): b':;\xeb\xb3\x19\x91H\x18:'

```

---

### Bước 2: Phân Tích Chu Kỳ Của Khóa (Key Length Determination)

Kiểm tra kỹ 9 bytes khóa vừa thu được:

| Chỉ số $i$ | Plaintext $P_i$ | Ciphertext $C_i$ | Byte khóa $K_i$ |
| --- | --- | --- | --- |
| 0 | `'b'` (`0x62`) | `0x58` | **`:`** (`0x3A`) |
| 1 | `'u'` (`0x75`) | `0x46` | `;` (`0x3B`) |
| 2 | `'s'` (`0x73`) | `0x98` | `\xeb` (`0xEB`) |
| 3 | `'h'` (`0x68`) | `0xDB` | `\xb3` (`0xB3`) |
| 4 | `'b'` (`0x62`) | `0x7B` | `\x19` (`0x19`) |
| 5 | `'a'` (`0x61`) | `0xF0` | `\x91` (`0x91`) |
| 6 | `'s'` (`0x73`) | `0x3B` | `H` (`0x48`) |
| 7 | `'h'` (`0x68`) | `0x70` | `\x18` (`0x18`) |
| 8 | `'{'` (`0x7B`) | `0x41` | **`:`** (`0x3A`) |

Dễ dàng nhận thấy $K_0 = \text{`':'`}$ và $K_8 = \text{`':'`}$.

Ký tự `:` lặp lại tại vị trí index 0 và index 8. Điều này khẳng định **độ dài thực sự của khóa $\vert{}K\vert{} = 8$**, và vị trí index 8 chính là bắt đầu của chu kỳ lặp khóa tiếp theo ($K_{8 \pmod 8} = K_0$).

Nếu sử dụng toàn bộ 9 bytes để giải mã, công thức $i \pmod 9$ sẽ làm lệch vị trí byte khóa từ byte thứ 9 trở đi, dẫn đến dữ liệu giải mã bị lỗi (`uuҸ}MsV|P`).

---

### Bước 3: Giải Mã Hoàn Chỉnh Với Khóa 8 Bytes

Sau khi xác định chính xác khóa mã hóa gồm **8 bytes** là `b':;\xeb\xb3\x19\x91H\x18'`, tiến hành viết script giải mã toàn bộ file `flag.enc`.

Mã nguồn giải mã đầy đủ (`solve.py`):

```python
#!/usr/bin/env python3

def main():
    # 1. Đọc dữ liệu file đã mã hóa
    with open("flag.enc", "rb") as f:
        encrypted = f.read()

    # 2. Khóa 8-byte chính xác đã khôi phục
    real_key = b':;\xeb\xb3\x19\x91H\x18'

    # 3. Giải mã Repeating-Key XOR
    decrypted = bytes(
        byte ^ real_key[i % len(real_key)]
        for i, byte in enumerate(encrypted)
    )

    # 4. In kết quả Flag
    flag = decrypted.decode('utf-8', errors='ignore')
    print(f"[+] Flag: {flag}")

if __name__ == "__main__":
    main()

```

Chạy chương trình thu được kết quả:

```text
[+] Flag: bushbash{to-x0r-or-nOt-To-Xor}
```

**GIẢI MÃ THÀNH CÔNG!**

---

## 4. Tổng Kết & Bài Học

1. **Không sử dụng XOR lặp khóa cho bảo mật:** Thuật toán Repeating-Key XOR hoàn toàn không có tính bảo mật ngữ nghĩa (Semantic Security). Khi một phần Plaintext bị lộ hoặc đoán được, toàn bộ khóa sẽ bị thu hồi dễ dàng.
2. **Căn chỉnh độ dài chu kỳ khóa:** Khi khôi phục khóa từ Known-Plaintext Attack, cần chú ý hiện tượng lặp lại byte khóa ở cuối chuỗi để xác định đúng độ dài $|K|$.
3. **Giải pháp thay thế:** Luôn ưu tiên các chuẩn mã hóa hiện đại như **AES-GCM** hoặc **ChaCha20-Poly1305** trong thực tế.
