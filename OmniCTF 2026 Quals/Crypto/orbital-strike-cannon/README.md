# Orbital-Strike-Cannon - Crypto / Math

Tool: Python 3, ncat, OpenSSL

Flag: **OmniCTF{Wemmbu_h4s_destroy3d_th3_law_hell_nawhh_where-is_you_eggcha~}**

---

## 1. Xác Định Cấu Trúc Bức Toán & Mã Nguồn

Đầu tiên, em tiến hành đọc và phân tích mã nguồn Python của challenge (`cannon.py`) để xác định các cơ chế toán học, thuật toán mã hóa và luồng hoạt động của bài toán:

* **Môi trường:** Python 3 (sử dụng duy nhất các thư viện chuẩn như `hashlib`, `json`, `secrets`, `dataclasses`).
* **Trường hữu hạn (Finite Field):** Mọi phép toán số học đều hoạt động trên modulo số nguyên tố Mersenne $P = 2^{127} - 1$.
* **Cấu trúc đại số Octonion:** Bài toán xây dựng hệ thống số Octonion 8 chiều theo Cayley-Dickson over $\mathbb{F}_P$. Tính chất đặc biệt được lưu ý trong mã nguồn là **không có tính kết hợp** (non-associative):

$$(R_i \times M_i) \times \alpha \neq R_i \times (M_i \times \alpha)$$


* **Thuật toán sinh số ngẫu nhiên (Broken RNG):** Sử dụng một Linear Congruential Generator (LCG) với phương trình:

$$S_{n+1} = (u \cdot S_n + v) \pmod P$$



Các giá trị $u, v, S_0$ là bí mật, nhưng danh sách `rng_beacons` công khai trong file JSON lại chứa hàng loạt đầu ra của RNG này.
* **Hệ thống Vệ Tinh (Satellites Oracle):** Có tổng cộng 7 vệ tinh thu thập dữ liệu, tuy nhiên chỉ có 5 vệ tinh là thật (`REAL_SATELLITES = 5`), 2 vệ tinh còn lại là nhiễu ngẫu nhiên.
* **Cơ chế mã hóa Flag:** Động cơ mã hóa sử dụng **SHAKE-256** hoạt động như Stream Cipher. Key mã hóa là băm SHA-256 của chuỗi byte chứa các tham số khởi tạo $[M_0, X_0, u, v]$.

### Nhận xét

Từ kết quả phân tích mã nguồn có thể đưa ra các điểm mấu chốt:

* Mặc dù phép nhân Octonion không có tính kết hợp, nhưng nó vẫn **tuân theo tính chất phân phối** (distributive). Nhờ đó, ta hoàn toàn có thể tuyến tính hóa các bước chuyển trạng thái thành các phép nhân ma trận $10 \times 10$ trên trường $\mathbb{F}_P$.
* Thuật toán LCG bị lộ các số đầu ra (`rng_beacons`). Chỉ cần 3 số liên tiếp $S_0, S_1, S_2$ là đủ để giải hệ phương trình tìm lại $u$ và $v$.
* Việc 2/7 vệ tinh bị lỗi (nhiễu dữ liệu) có thể xử lý dễ dàng bằng cách thử kết hợp từng cặp vệ tinh và chạy phép khử Gauss (Gaussian Elimination).

---

## 2. Chạy Thử Server

Khi tiến hành kết nối đến server thông qua `ncat`:

```bash
ncat --ssl orbital-7a8bc3ee25d9.inst.omnictf.com 1337

```

Server sẽ hiển thị Banner `ORBITAL STRIKER CANNON`, in ra toàn bộ cấu hình telemetry dưới dạng JSON (bao gồm $P$, $\alpha$, $\beta$, `outer_a`, `rng_beacons`, các vệ tinh `satellites`, và `ciphertext`) sau đó dừng lại yêu cầu nhập `firing code`.

Nếu nhập mã không đúng, kernel sẽ bị sụp đổ ("unstable kernel collapse detected") và server lập tức ngắt kết nối.

<img width="1810" height="906" alt="image" src="https://github.com/user-attachments/assets/3056cde2-a2d9-4b56-aa22-07f0acd317c1" />

---

## 3. Phân Tích Lỗ Hổng & Bẻ Khóa Thuật Toán

### Bước 1: Khôi phục LCG (Khôi phục $u$ và $v$)

Từ mảng `rng_beacons` lấy được từ telemetry, gọi 3 giá trị đầu tiên là $S_0, S_1, S_2$. Ta có hệ phương trình:


$$S_1 = (u \cdot S_0 + v) \pmod P$$

$$S_2 = (u \cdot S_1 + v) \pmod P$$

Trừ hai phương trình cho nhau để triệt tiêu $v$:


$$S_2 - S_1 = u \cdot (S_1 - S_0) \pmod P$$

$$\Rightarrow u = (S_2 - S_1) \cdot (S_1 - S_0)^{-1} \pmod P$$

$$\Rightarrow v = (S_1 - u \cdot S_0) \pmod P$$

### Bước 2: Ma trận hóa biểu diễn trạng thái (Linearization)

Mỗi trạng thái $i$ gồm vector Octonion $M_i \in \mathbb{F}_P^8$ và vĩ độ $X_i \in \mathbb{F}_P$. Do phép nhân Octonion tuyến tính theo từng tham số, ta dựng ma trận chuyển trạng thái $10 \times 10$ để biểu diễn $[M_i, X_i, 1]$ dưới dạng biểu thức Affine theo trạng thái ban đầu $[M_0, X_0, 1]$.

### Bước 3: Loại bỏ nhiễu Vệ tinh & Giải hệ phương trình tuyến tính

Dữ liệu mỗi mẫu từ vệ tinh có dạng:


$$\text{Sample} = (\text{mask} \cdot (\text{basis} \cdot F_i) + \text{bias}) \pmod P$$


Trong đó $F_i = [M_i, X_i, X_{i+1}, X_{i+2}]$. Vì $F_i$ phụ thuộc tuyến tính vào $[M_0, X_0]$, mỗi phép đo cho ta một phương trình tuyến tính bậc nhất theo 9 ẩn số $[M_0^{(0..7)}, X_0]$.

Ta duyệt qua các cặp vệ tinh và đưa vào thuật toán **Gaussian Elimination** over $\mathbb{F}_P$. Cặp vệ tinh thật sẽ cho ra nghiệm duy nhất đúng cho $M_0$ và $X_0$.

---

## 4. Giải Bài & Kết Quả

Em tiến hành viết script `Script_decript_cannon.py` thực thi toàn bộ luồng khai thác tự động:

1. Kết nối SSL đến `orbital-7a8bc3ee25d9.inst.omnictf.com:1337`.
2. Parse dữ liệu telemetry JSON nhận được từ server.
3. Tính toán tìm $u$ và $v$ từ `rng_beacons`.
4. Dựng các ma trận chuyển trạng thái và hệ phương trình tuyến tính cho 7 vệ tinh.
5. Thực hiện khử Gauss loại bỏ 2 vệ tinh nhiễu, thu được $M_0$ và $X_0$.
6. Tái tạo secret key SHA-256 từ `moon0 + [x0, u, v]`, giải mã Flag bằng SHAKE-256 stream cipher và tính `firing_code`.
7. Gửi `firing_code` lên server để xác nhận LOCK CONFIRMED.

Chạy script giải bài:

**Kết quả thu được:**

* **Secret LCG Parameters:**
* $u = 91494671799922103210155029689383592639$
* $v = 120339847901033753724758095256937071221$


* **Initial Orbit State:** $X_0 = 10563564651973304801376431282413509545$
* **Firing Code:** `de878eb17b40b44ebb47c9f3f9e10bdf`
* **Server Response:** `LOCK CONFIRMED. CANNON FIRED.`

<img width="1261" height="490" alt="image" src="https://github.com/user-attachments/assets/58141c35-9bec-4a66-b039-6c120c847975" />

Flag cuối cùng thu được là: **OmniCTF{Wemmbu_h4s_destroy3d_th3_law_hell_nawhh_where-is_you_eggcha~}**
