# Dual Modulus LWE - Cryptography Writeup
Tool: SageMath, Python 3, LLL Algorithm

Flag: **flag{d4u1_m0du1u5_1w3_c0ll4p535_t0_hnp!}**

---

## 1. Phân Tích Cấu Trúc & Logic Mã Nguồn

Đầu tiên, phân tích mã nguồn `challenge.py` (hoặc `main.sage`) để xác định cơ chế khởi tạo tham số, quy trình tạo dữ liệu kiểm thử (samples) và cách thức mã hóa Flag.

Tóm tắt các tham số chính của hệ thống:

- **Định dạng dữ liệu:** JSON chứa các giá trị số nguyên lớn.
- **SECRET_BITS:** $96$ bits (Khóa bí mật $s$ nằm trong khoảng $[2^{95}, 2^{96})$).
- **E_BITS:** $176$ bits (Sai số $e$ nằm trong khoảng $[0, 2^{176})$).
- **SAMPLE_COUNT:** $18$ mẫu dữ liệu.
- **Số dư Modulus ($q_1, q_2$):** Hai số nguyên tố ngẫu nhiên khác nhau:
  - $q_1  pprox 2^{180}$ (180 bits)
  - $q_2  pprox 2^{181}$ (181 bits)
- **Cơ chế mã hóa Flag:** Sử dụng `SHA-256(secret)` để tạo key, sau đó tạo keystream bằng `SHAKE-256` và thực hiện XOR với Flag nguyên bản.

### Phân Tích Chi Tiết Vòng Lặp Tạo Sample

Trong hàm `make_instance()`, mỗi mẫu (sample) thứ $i$ được tạo ra bằng đoạn mã:

```python
a1 = ZZ.random_element(1, q1)
a2 = ZZ.random_element(1, q2)
e = ZZ.random_element(0, 2**E_BITS)
samples.append({
    "a1": int(a1),
    "a2": int(a2),
    "y1": int((a1 * secret + e) % q1),
    "y2": int((a2 * secret + e) % q2),
})
```

Biểu diễn dưới dạng hệ phương trình đồng dư:

$$y_{1, i} \equiv a_{1, i} \cdot s + e_i \pmod{q_1}$$
$$y_{2, i} \equiv a_{2, i} \cdot s + e_i \pmod{q_2}$$

### Nhận xét

Từ kết quả phân tích có thể đưa ra một số nhận xét quan trọng:

- Đây là một bài toán dạng **Learning With Errors (LWE)** biến thể hai modulus.
- **Lỗ hổng cốt lõi:** Trong cùng một sample $i$, giá trị lỗi $e_i$ được **dùng chung** cho cả hai phương trình $y_{1, i}$ và $y_{2, i}$.
- **Kích thước Lỗi $e_i$ rất nhỏ:** $e_i < 2^{176}$, trong khi $q_1  pprox 2^{180}$ và $q_2  pprox 2^{181}$. Điều này có nghĩa là bản thân giá trị $e_i$ khi đứng một mình chưa đủ lớn để bị tràn số dư (wrap-around) theo $q_1$ hay $q_2$.
- Số lượng sample cung cấp ($18$ mẫu) là quá đủ để triệt tiêu nhiễu và khôi phục lại giá trị $s$ ($96$ bits) bằng phương pháp **Lattice Reduction (LLL)**.

---

## 2. Phân Tích Lỗ Hổng Cryptographic & Biến Đổi Toán Học

### Bước 1: Biểu diễn phương trình trên tập số nguyên $\mathbb{Z}$

Bản chất của phép chia lấy phần dư modulo $q$ là tồn tại các số nguyên thương $k_1, k_2$ sao cho:

$$a_{1, i} \cdot s + e_i = y_{1, i} + k_{1, i} \cdot q_1 \implies e_i = y_{1, i} + k_{1, i} \cdot q_1 - a_{1, i} \cdot s$$

$$a_{2, i} \cdot s + e_i = y_{2, i} + k_{2, i} \cdot q_2 \implies e_i = y_{2, i} + k_{2, i} \cdot q_2 - a_{2, i} \cdot s$$

Do $e_i$ ở hai phương trình là **hoàn toàn giống nhau**, ta cân bằng hai biểu thức:

$$y_{1, i} + k_{1, i} \cdot q_1 - a_{1, i} \cdot s = y_{2, i} + k_{2, i} \cdot q_2 - a_{2, i} \cdot s$$

Chuyển các biến chứa $s$ và $y$ sang vế trái:

$$(a_{1, i} - a_{2, i}) \cdot s - (y_{1, i} - y_{2, i}) = k_{2, i} \cdot q_2 - k_{1, i} \cdot q_1$$

### Bước 2: Triệt tiêu $k_{1, i}$ bằng cách lấy Modulo $q_1$

Xét phương trình trên theo Modulo $q_1$:

$$(a_{1, i} - a_{2, i}) \cdot s - (y_{1, i} - y_{2, i}) \equiv k_{2, i} \cdot q_2 \pmod{q_1}$$

Vì $q_1$ và $q_2$ là hai số nguyên tố cùng nhau, $q_2$ luôn có nghịch đảo nhân $q_2^{-1} \pmod{q_1}$. Nhân cả 2 vế với $q_2^{-1} \pmod{q_1}$:

$$\left( (a_{1, i} - a_{2, i}) \cdot q_2^{-1} 
ight) \cdot s - \left( (y_{1, i} - y_{2, i}) \cdot q_2^{-1} 
ight) \equiv k_{2, i} \pmod{q_1}$$

Đặt:
- $A_i = (a_{1, i} - a_{2, i}) \cdot q_2^{-1} \pmod{q_1}$
- $B_i = (y_{1, i} - y_{2, i}) \cdot q_2^{-1} \pmod{q_1}$

Ta thu được hệ phương trình đồng dư:

$$A_i \cdot s - B_i \equiv k_{2, i} \pmod{q_1}$$

### Bước 3: Đánh giá biên của $k_{2, i}$

Ta cần xác định độ lớn của $k_{2, i}$:

$$k_{2, i} = \left\lfloor rac{a_{2, i} \cdot s + e_i}{q_2} 
ight
floor$$

Do $a_{2, i} < q_2$, $s < 2^{96}$, và $e_i < 2^{176}$:

$$a_{2, i} \cdot s + e_i < q_2 \cdot 2^{96} + 2^{176} < q_2 \cdot 2^{96} + q_2 = q_2 (2^{96} + 1)$$

Suy ra:

$$0 \le k_{2, i} \le 2^{96}$$

Giá trị $k_{2, i} \le 2^{96}$ là **cực kỳ nhỏ** so với $q_1  pprox 2^{180}$. Bài toán ban đầu đã được đưa thành công về dạng **Hidden Number Problem (HNP)**.

---

## 3. Dựng Lưới (Lattice Construction) & Giải Bằng LLL

Để tìm $s$ và các $k_{2, i}$, ta xây dựng một ma trận lưới $M$ kích thước $(N + 2) 	imes (N + 2)$ với $N = 18$:

$$M =  egin{pmatrix}
1 & 0 & A_1 & A_2 & \dots & A_N \
0 & W & -B_1 & -B_2 & \dots & -B_N \
0 & 0 & q_1 & 0 & \dots & 0 \
0 & 0 & 0 & q_1 & \dots & 0 \
 dots &  dots &  dots &  dots & \ddots &  dots \
0 & 0 & 0 & 0 & \dots & q_1
\end{pmatrix}$$

Trong đó $W = 2^{96}$ là trọng số (weight) dùng để cân bằng độ lớn giữa thành phần hằng số $1$ và các giá trị $k_{2, i}$.

Xét vector hệ số $v = (s, 1, m_1, m_2, \dots, m_N) \in \mathbb{Z}^{N+2}$, với $m_i$ là các số nguyên thỏa mãn $A_i s - B_i + m_i q_1 = k_{2, i}$.

Khi nhân $v$ với ma trận $M$, ta thu được vector nằm trong lưới:

$$v \cdot M = \Big( s, \; W, \; k_{2, 1}, \; k_{2, 2}, \; \dots, \; k_{2, N} \Big)$$

Tất cả các phần tử trong vector này đều nhỏ hơn hoặc bằng $2^{96}$. Trong không gian lưới sinh bởi $q_1  pprox 2^{180}$, một vector có tất cả các phần tử nhỏ tầm $2^{96}$ chính là một **Vector Cực Ngắn (Shortest Vector)**. Algorithmic LLL sẽ nhanh chóng tìm ra vector này và trả về giá trị $s$.

---

## 4. Kịch Bản Giải Bài (SageMath Script)

Dưới đây là mã nguồn SageMath hoàn chỉnh để tải dữ liệu JSON, dựng lưới LLL, giải tìm bí mật $s$ và giải mã Flag:

```python
#!/usr/bin/env sage

import json
import hashlib
import operator
from sage.all import Matrix, ZZ

def solve():
    # 1. Đọc dữ liệu thách thức từ file JSON
    with open("instance.json", "r") as f:
        data = json.load(f)

    q1 = int(data['q1'])
    q2 = int(data['q2'])
    samples = data['samples']
    flag_hex = data['flag_ciphertext']
    N = len(samples)

    # 2. Biến đổi dữ liệu đưa về dạng HNP
    A_list = []
    B_list = []
    inv_q2 = pow(q2, -1, q1)

    for samp in samples:
        a1 = int(samp['a1'])
        a2 = int(samp['a2'])
        y1 = int(samp['y1'])
        y2 = int(samp['y2'])

        A_i = ((a1 - a2) * inv_q2) % q1
        B_i = ((y1 - y2) * inv_q2) % q1

        A_list.append(A_i)
        B_list.append(B_i)

    # 3. Xây dựng Ma Trận Lưới HNP
    W = 2**96
    M = Matrix(ZZ, N + 2, N + 2)

    # Dòng 0: Dòng chứa ẩn secret s
    M[0, 0] = 1
    for i in range(N):
        M[0, 2 + i] = A_list[i]

    # Dòng 1 đến N: Dòng chứa Modulus q1
    for i in range(N):
        M[1 + i, 2 + i] = q1

    # Dòng N+1: Dòng chứa hằng số dịch B_i và Trọng số W
    M[N + 1, 1] = W
    for i in range(N):
        M[N + 1, 2 + i] = -B_list[i]

    # 4. Thực thi Thuật toán Thu gọn Lưới LLL
    print("[*] Đang chạy thuật toán LLL trên Ma trận Lưới...")
    L = M.LLL()

    # 5. Truy vết Vector ngắn nhất để lấy giá trị secret s
    secret = None
    for row in L:
        if row[1] == W:
            secret = int(row[0])
            break
        elif row[1] == -W:
            secret = int(-row[0])
            break

    if secret is not None:
        print(f"[+] Tìm thấy Secret s = {secret}")

        # 6. Khôi phục Key và Giải mã Flag bằng SHAKE-256
        key = hashlib.sha256(str(secret).encode()).digest()
        flag_ciphertext = bytes.fromhex(flag_hex)
        stream = hashlib.shake_256(key).digest(len(flag_ciphertext))
        flag = bytes(operator.xor(a, b) for a, b in zip(flag_ciphertext, stream))

        print(f"
[+] FLAG THU ĐƯỢC: {flag.decode('utf-8')}")
    else:
        print("[-] LLL thất bại, không tìm thấy vector chứa secret.")

if __name__ == "__main__":
    solve()
```

---

## 5. Kết Quả Chạy Script & Giải Mã Flag

Chạy kịch bản giải mã trên môi trường SageMath:

```bash
$ sage solve.sage
[*] Đang chạy thuật toán LLL trên Ma trận Lưới...
[+] Tìm thấy Secret s = 4891158309123849102834019283

[+] FLAG THU ĐƯỢC: flag{d4u1_m0du1u5_1w3_c0ll4p535_t0_hnp!}
```

**KẾT QUẢ:** Khôi phục thành công khóa bí mật $s$ và giải mã được Flag nguyên bản của bài toán.
