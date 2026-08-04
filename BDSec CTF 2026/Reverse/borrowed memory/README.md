# Borrowed Memory - BDSec CTF 2026 - Reverse Engineering

Tool: Detect It Easy, IDA Pro / Ghidra, Python 3

Flag: **BDSEC{p01nt3rs_l13_bUt_0ffs3ts_r3m3mb3r}**

---

## 1. Xác Định Cấu Trúc File

Đầu tiên, em sử dụng công cụ **Detect It Easy (DIE)** để phân tích sơ bộ file thực thi `borrowed_memory.bdsec` nhằm xác định định dạng, kiến trúc và các cơ chế bảo vệ trước khi tiến hành phân tích mã nguồn.

Kết quả thu được như sau:

* **Định dạng file:** ELF64 (Executable and Linkable Format 64-bit)
* **Kiến trúc:** AMD64 (x86-64)
* **Loại chương trình:** Console Application / Dynamically Linked
* **Hệ điều hành mục tiêu:** GNU/Linux 64-bit
* **Compiler:** GCC / Clang
* **Bảo vệ:** Stack Canary (`__readfsqword(0x28u)`), NX (No-Execute) Enabled, PIE (Position Independent Executable)
* **Thông tin bổ sung:** File không bị nén hay mã hóa bởi các công cụ packer như UPX.

<img width="905" height="657" alt="image" src="https://github.com/user-attachments/assets/20fe204e-7f6d-41af-b001-79a661db56a2" />

### Nhận xét

Từ kết quả phân tích có thể đưa ra một số nhận xét:

* Chương trình được biên dịch cho hệ điều hành Linux trên kiến trúc **64-bit**, thao tác truyền tham số sẽ tuân theo System V AMD64 ABI (rdi, rsi, rdx, rcx, r8, r9).
* Chương trình có sử dụng **Stack Canary** để chống tràn bộ đệm tại biến `v55`.
* File không dùng packer/protector nên có thể đưa trực tiếp vào **IDA Pro** hoặc **Ghidra** để decompile và đọc mã giả C.

---

## 2. Chạy Thử Phần Mềm

Khi em chạy thử chương trình `./borrowed_memory.bdsec` trên Terminal, giao diện in ra một banner ASCII art và yêu cầu nhập dữ liệu:

```text
        _________________________________________
       /                                         \
      /          B D S e c   C T F   2 0 2 6      \
     /_____________________________________________\
     |                                             |
     |              BORROWED MEMORY                |
     |                                             |
     |        0x???? -> 0x???? -> 0x????           |
     |_____________________________________________|

Return what was borrowed.
> 

```

Khi em thử nhập một chuỗi bất kỳ hoặc một số ngẫu nhiên, chương trình ngay lập tức phản hồi:

```text
rejected

```

### Nhận xét ban đầu

* Banner `0x???? -> 0x???? -> 0x????` gợi ý về một cấu trúc **Danh sách liên kết (Linked List)** hoặc chuỗi các địa chỉ con trỏ bộ nhớ.
* Thông điệp *"Return what was borrowed"* yêu cầu chúng ta phải trả lại đúng chuỗi địa chỉ bộ nhớ theo thứ tự liên kết mà chương trình đã tạo ra.

---

## 3. Phân Tích Chi Tiết Luồng Thực Thi (Reverse Engineering)

Đưa file vào **IDA Pro**, em thu được đoạn mã giả C ở hàm `main` với các giai đoạn chính như sau:

### Giai đoạn 1: Khởi tạo vùng nhớ PRNG (`byte_555555558080`)

Chương trình tạo một mảng bộ nhớ đệm gồm 2048 byte (`0x800` bytes) bằng thuật toán sinh số giả ngẫu nhiên (PRNG) với seed ban đầu `-1847521883`:

```c
v5 = -1847521883;
v4 = 0;
do
{
  v6 = (v5 + v4 + 73244475) ^ ((v5 + (_DWORD)v4 + 73244475) << 13);
  v5 = (32 * ((v6 >> 17) ^ v6)) ^ (v6 >> 17) ^ v6;
  byte_555555558080[v4++] = v5 >> 11;
}
while ( v4 != 2048 );

```

### Giai đoạn 2: Khởi tạo các Node ẩn trong Memory Pool

Sau vòng lặp PRNG, chương trình ghi đè liên tiếp các giá trị `byte`, `word`, `dword` vào các offset cụ thể bên trong mảng `byte_555555558080`:

```c
word_5555555580A0 = 32149;
word_555555558224 = 5879;
byte_555555558226 = 91;
...

```

Mặc dù IDA decompile thành các biến toàn cục riêng lẻ (`word_...`, `byte_...`), thực chất đây là việc khởi tạo thủ công các trường (fields) của từng **Node** thuộc danh sách liên kết được đặt ẩn bên trong bộ nhớ đệm 2048 byte.

### Giai đoạn 3: Kiểm tra định dạng Input từ người dùng

Chương trình thực hiện vòng lặp `do-while` bắt người dùng nhập vào các giá trị:

```c
v16 = strtoul(v10, &endptr, 0);
...
if ( (_BYTE)v20 || v18 - 0x4000 > 0x7FF )
{
LABEL_8:
  puts("rejected");
  ...
}
*(_WORD *)v8 = v18;
v8 += 2;

```

Đoạn mã trên cho thấy:

1. Dữ liệu nhập vào được chuyển thành số bằng `strtoul` (chấp nhận cả dạng Hex `0x...` lẫn Decimal).
2. Kiểm tra điều kiện: $v18 - 0x4000 \le 0x7FF$. Điều này ép buộc mọi địa chỉ do người dùng nhập vào phải thuộc vùng nhớ ảo từ **`0x4000` đến `0x47FF**`.
3. Công thức ánh xạ địa chỉ:

{Input Address} = 0x4000 + {Offset} (v25)



### Giai đoạn 4: Vòng lặp duyệt Danh sách liên kết & Kiểm tra Checksum

Chương trình bắt đầu duyệt node đầu tiên tại offset:


v25 = {word\_5555555580A0} \oplus 0x7C31 = 32149 \oplus 0x7C31 = 0x01A4

Tại mỗi node $v25$:

1. **Khớp địa chỉ nhập:** So sánh địa chỉ người dùng nhập với $v25 + 0x4000$.
2. **Xác định loại Node ($v28$):** Tính $v28 = \text{byte}[v25] \oplus (v25 \gg 3)$.
3. **Tính toán Node tiếp theo ($v34$):**
* **Loại 0 (`0xC0`):** Xoay bit (`__ROL2__`) và lấy đảo bit (`~`) dữ liệu tại offset $v25+5, v25+6$.
* **Loại 1 (`0xC1`):** Tra cứu phi tuyến vào mảng PRNG kết hợp phép nhân `4919` và constant `0xA55A`.
* **Loại 2 (`0xC2`):** XOR dữ liệu tại offset $v25+2, v25+3$ với biến trạng thái `v22`.
* **Loại 3 (`0xC3`):** Cộng offset $v25$ với biến trạng thái `v48`.


4. **Kiểm tra Checksum ($v35$):** Tính giá trị checksum $v35$ và so sánh với 2 byte chữ ký lưu tại $[v25 + 8]$ và $[v25 + 9]$. Nếu không trùng khớp, chương trình sẽ báo `rejected`.
5. **Cập nhật Key:** Mỗi bước duyệt sẽ cập nhật các biến mã hóa `v26`, `v23`, `v22`, `v48` và ghi lại vào mảng `v52`, `v53`.

Vòng lặp chạy đúng 12 lần cho đến khi $v22 == 0xB223$ và offset tiếp theo $v34 == 0xFFFF$ (con trỏ NULL).

### Giai đoạn 5: Giải mã Flag

Nếu cả 12 địa chỉ nhập vào đều chính xác, chương trình sẽ kết hợp các địa chỉ đã nhập (`v50`), mảng key tích lũy (`v52`, `v53`) và mảng dữ liệu tĩnh `byte_555555556220` để giải mã từng ký tự của flag:

```c
do
{
  v45 = 7 * v44;
  v46 = (v52[v44 % 12] >> (8 * (v44 & 3))) ^ v53[(5 * v44 + 1) % 12] ^ (29 * v44) ^ byte_555555556220[v44];
  ++v44;
  putc(v50[2 * ((v45 + 3) % 12)] ^ v46, stdout);
}
while ( v44 != 40 );

```

---

## 4. Giải Bài & Lấy Flag

Để giải bài này, em viết một script Python mô phỏng lại toàn bộ quá trình khởi tạo mảng PRNG, ghi đè byte dữ liệu và thuật toán chuyển trạng thái để tự động tìm ra chuỗi 12 địa chỉ node.

### Script Solver (`solve.py`)

```python
#!/usr/bin/env python3

def u32(x): 
    return x & 0xFFFFFFFF

def rol2(val, count):
    count %= 16
    val &= 0xFFFF
    return ((val << count) | (val >> (16 - count))) & 0xFFFF

# 1. Khởi tạo mảng PRNG 2048 bytes
BASE = 0x555555558080
v5 = -1847521883 & 0xFFFFFFFF
buf = bytearray(2048)

for v4 in range(2048):
    sum1 = u32(v5 + v4 + 73244475)
    v6 = u32(sum1 ^ u32(sum1 << 13))
    temp = u32(v6 >> 17) ^ v6
    v5 = u32(u32(32 * temp) ^ temp)
    buf[v4] = (v5 >> 11) & 0xFF

# Hàm hỗ trợ ghi đè dữ liệu bộ nhớ
def set_w(addr, val):
    off = addr - BASE
    buf[off] = val & 0xFF
    buf[off+1] = (val >> 8) & 0xFF

def set_b(addr, val):
    buf[addr - BASE] = val & 0xFF

def set_d(addr, val):
    off = addr - BASE
    for i in range(4):
        buf[off+i] = (val >> (8*i)) & 0xFF

# 2. Patch dữ liệu bộ nhớ theo đúng file C
set_w(0x5555555580A0, 32149)
set_w(0x555555558224, 5879)
set_w(0x55555555822B, -24901)
set_w(0x555555558372, -25156)
set_w(0x555555558377, 5199)
set_w(0x55555555810A, -14811)
set_w(0x5555555581CA, -11694)
set_w(0x55555555829D, -10880)
set_w(0x5555555582A4, -14203)
set_w(0x55555555852A, 27833)
set_w(0x55555555852F, -2850)
set_w(0x555555558116, 29532)
set_b(0x555555558226, 91)
set_b(0x55555555822D, 84)
set_b(0x555555558370, -100)
set_b(0x555555558379, -86)
set_b(0x5555555581C3, -23)
set_b(0x5555555581C7, 6)
set_b(0x5555555581CC, 9)
set_b(0x5555555583EC, -83)
set_d(0x5555555583F1, -1201983522)
set_b(0x5555555583F5, -118)
set_b(0x55555555829F, 92)
set_b(0x5555555582A6, 0x80)
set_b(0x555555558528, 87)
set_b(0x555555558531, 76)
set_b(0x555555558176, -33)
set_b(0x55555555817A, 61)
set_w(0x55555555817D, -23698)
set_b(0x55555555817F, 87)
set_b(0x5555555585DB, 107)
set_d(0x5555555585E0, 1157791348)
set_b(0x5555555585E4, -72)
set_w(0x555555558397, 6049)
set_w(0x55555555839E, -29950)
set_w(0x55555555870E, 3255)
set_w(0x555555558713, -20387)
set_w(0x55555555812E, 6363)
set_w(0x5555555582E1, -7732)
set_w(0x55555555813B, -26450)
set_w(0x555555558140, 25354)
set_w(0x555555558699, -11047)
set_w(0x555555558661, -8833)
set_w(0x555555558668, -16456)
set_w(0x555555558122, -6976)
set_b(0x555555558399, 97)
set_b(0x5555555583A0, 60)
set_b(0x55555555870C, 19)
set_b(0x555555558715, 109)
set_b(0x5555555582DA, -118)
set_b(0x5555555582DE, -19)
set_b(0x5555555582E3, -73)
set_b(0x5555555587BD, 39)
set_d(0x5555555587C2, 941162496)
set_b(0x5555555587C6, -123)
set_b(0x555555558139, -43)
set_b(0x555555558142, 69)
set_b(0x555555558692, 3)
set_b(0x555555558696, 98)
set_b(0x55555555869B, -119)
set_b(0x5555555584F0, 78)
set_d(0x5555555584F5, -1200103448)
set_b(0x5555555584F9, 102)
set_b(0x555555558663, -119)
set_b(0x55555555866A, 104)
set_b(0x555555558210, -16)
set_w(0x555555558212, -18085)
set_w(0x555555558217, 11715)
set_b(0x555555558219, -39)

# 3. Duyệt danh sách liên kết để tìm 12 địa chỉ
v22 = (-16657) & 0xFFFF
v48 = 23130 & 0xFFFFFFFF
v25 = 32149 ^ 0x7C31

inputs = []

for step in range(12):
    addr_input = v25 + 0x4000
    inputs.append(hex(addr_input))
    
    v28 = buf[v25] ^ (v25 >> 3)
    low_v48 = v48 & 0xFFFF
    v32 = (((low_v48 - 90) & 0xFF) % 7) + 1
    v31 = (v25 ^ (buf[v25 + 7] ^ ((76 - v22) & 0xFF))) & 0xFFFF
    
    if v28 == 0xC1:
        v41 = ((v31 ^ buf[v25 + 4]) ^ 0x6D) & 0xFF
        idx1 = (2 * v41 + 129) & 0x7FF
        idx2 = (2 * v41 + 128) & 0xFFFF
        v42 = (4919 * v41) ^ ((buf[idx1] << 8) | buf[idx2])
        v34 = (v42 ^ 0xA55A) & 0xFFFF
    elif v28 == 0xC0:
        v43 = (buf[v25 + 6] << 8) | buf[v25 + 5]
        v34 = (~rol2(v43, v32)) & 0xFFFF
    elif v28 == 0xC2:
        v33 = (v25 + 2) & 0xFFFF
        v34 = (v22 ^ (buf[v25 + 3] | (buf[v33] << 8))) & 0xFFFF
    else:
        v33 = (v25 + 2) & 0xFFFF
        v34 = (v25 + (low_v48 ^ (buf[v25 + 1] | (buf[v33] << 8)))) & 0xFFFF
        
    v22 = (v22 - 273) & 0xFFFF
    high_v48 = (((v48 >> 16) & 0xFFFF) + 573) & 0xFFFF
    low_v48 = (low_v48 + 257) & 0xFFFF
    v48 = (high_v48 << 16) | low_v48
    v25 = v34

print("Dãy 12 địa chỉ cần nhập:")
for i, addr in enumerate(inputs, 1):
    print(f"Node {i:2d}: {addr}")

```

Kết quả thu được chuỗi 12 địa chỉ:

| Bước | Offset ($v25$) | Địa chỉ cần nhập (Hex) |
| --- | --- | --- |
| **1** | `0x01a4` | `0x41a4` |
| **2** | `0x02f0` | `0x42f0` |
| **3** | `0x0143` | `0x4143` |
| **4** | `0x036c` | `0x436c` |
| **5** | `0x021d` | `0x421d` |
| **6** | `0x04a8` | `0x44a8` |
| **7** | `0x00f6` | `0x40f6` |
| **8** | `0x055b` | `0x455b` |
| **9** | `0x0317` | `0x4317` |
| **10** | `0x068c` | `0x468c` |
| **11** | `0x025a` | `0x425a` |
| **12** | `0x073d` | `0x473d` |

<img width="1280" height="1295" alt="image" src="https://github.com/user-attachments/assets/cbfaa965-407f-4a37-af0a-361516ab7de9" />

### Thực thi lấy Flag

Sử dụng lệnh `printf` pipe chuỗi 12 địa chỉ vào chương trình:

```bash
printf "0x41a4\n0x42f0\n0x4143\n0x436c\n0x421d\n0x44a8\n0x40f6\n0x455b\n0x4317\n0x468c\n0x425a\n0x473d\n" | ./borrowed_memory.bdsec

```

Kết quả chương trình chấp nhận cả 12 địa chỉ và in ra flag:

```text
        _________________________________________
       /                                         \
      /          B D S e c   C T F   2 0 2 6      \
     /_____________________________________________\
     |                                             |
     |              BORROWED MEMORY                |
     |                                             |
     |        0x???? -> 0x???? -> 0x????           |
     |_____________________________________________|

Return what was borrowed.
> > > > > > > > > > > > [+] BDSEC{p01nt3rs_l13_bUt_0ffs3ts_r3m3mb3r}

```

<img width="1452" height="351" alt="image" src="https://github.com/user-attachments/assets/0845542e-5c4d-4627-ab75-42d68f7f4498" />

**Flag thu được:** **`BDSEC{p01nt3rs_l13_bUt_0ffs3ts_r3m3mb3r}`**
