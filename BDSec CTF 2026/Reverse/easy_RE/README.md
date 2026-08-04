# BDSEC CTF - Reverse Engineering Challenge Easy_RE

Tool: Detect It Easy, IDA Pro, Python 3

Flag: **BDSEC{e4SY_r3v3rS3_eNg1N33r1nG_cH4LL4ng3}**

---

## 1. Xác Định Cấu Trúc File

Đầu tiên, em sử dụng công cụ **Detect It Easy (DIE)** để phân tích sơ bộ file thực thi nhằm xác định định dạng, kiến trúc, trình biên dịch và các thông tin cơ bản trước khi đưa vào các công cụ phân tích tĩnh.

Kết quả thu được như sau:

* **Định dạng file:** ELF64 (Executable and Linkable Format 64-bit) / PE64
* **Kiến trúc:** AMD64 (x86-64)
* **Loại chương trình:** Console Application
* **Hệ điều hành mục tiêu:** Linux / Windows 64-bit
* **Compiler:** GCC / Clang (x86_64)
* **Tùy chọn tối ưu:** O2 / O3 Optimization (Phát hiện các tập lệnh SIMD / XMM và phép nhân tối ưu hóa cho phép chia)
* **Thông tin Debug:** Dữ liệu symbol bị strip một phần, tuy nhiên các nhãn chuỗi hằng số (`.rodata`) vẫn giữ nguyên tên biến toàn cục.

<img width="901" height="651" alt="image" src="https://github.com/user-attachments/assets/de64a8f2-43a2-44cb-8e05-e0fa04c6a91b" />

### Nhận xét

Từ kết quả phân tích có thể đưa ra một số nhận xét:

* Chương trình được biên dịch cho kiến trúc **64-bit**, toàn bộ thao tác truyền tham số và tính toán sẽ sử dụng hệ thống thanh ghi 64-bit (`RAX`, `RDI`, `RSI`, `R8`-`R13`).
* Trình biên dịch có bật chế độ tối ưu hóa mã nguồn, dẫn đến việc các vòng lặp tính toán $i \pmod N$ được thay thế bằng phép nhân với hằng số magic (như `4924924924924925h` cho modulo 7 và `0C7CE0C7CE0C7CE0Dh` cho modulo 41).
* Việc so sánh kết quả sử dụng các thanh ghi SIMD 128-bit (`XMM`), do đó dữ liệu hằng số kiểm tra sẽ được lưu trữ dưới dạng `xmmword` trong vùng nhớ `.rodata`.

---

## 2. Chạy Thử & Phát Hiện "Bẫy" Chiều Dài (Length Check Trap)

Khi tiến hành chạy thử file thực thi trên terminal, chương trình yêu cầu nhập Flag:

```c
[*] Your lucky number: 11082
Enter the flag: 

```

Nếu nhập thử một chuỗi bất kỳ, chương trình lập tức kết thúc hoặc thông báo sai Flag.

### Phân tích Luồng Kiểm Tra Trong IDA Pro

Đưa file vào **IDA Pro**, tại hàm `main`, chương trình ban đầu thực hiện kiểm tra độ dài chuỗi đầu vào. Ban đầu có một nhánh so sánh độ dài với `26` (`0x1A`), nếu không khớp sẽ nhảy qua lệnh `jz loc_5555555552FB`.

Tuy nhiên, khi truy vết nhánh chuyển hướng `loc_5555555552FB`, em phát hiện ra đây mới chính là luồng kiểm tra Flag thật sự của bài toán với độ dài yêu cầu chính xác là **41 ký tự (`0x29`)**.

---

## 3. Khắc Phục Lỗi Anti-Decompilation / Misaligned Bytes

Khi bấm **F5** tại địa chỉ `loc_5555555552FB`, IDA Decompiler bị lỗi và chỉ hiển thị đúng một dòng mã giả truncated:

```c
memset(v70, 0, 0x29u);

```

### Nguyên nhân

Quan sát trực tiếp tại cửa sổ Disassembly (`IDA View-A`), ngay sau các lệnh khởi tạo thanh ghi là một đoạn Byte đệm căn chỉnh memory (Padding NOPs):

```assembly
.text:0000555555555341                 nop     dword ptr [rax+00h]
.text:0000555555555345                 db      66h, 66h, 2Eh
.text:0000555555555345                 nop     word ptr [rax+rax+00000000h]

```

Do có sự đè lấp byte `db 66h, 66h, 2Eh` ngay giữa luồng mã máy, Decompiler không thể xác định được biên độ lệnh và dừng dịch ngược.

### Cách xử lý

1. Đặt con trỏ tại địa chỉ `.text:0000555555555345`, nhấn phím **`U`** (**Undefine**) để hủy bỏ định dạng cũ.
2. Di chuyển xuống dòng byte thực thi tiếp theo, nhấn phím **`C`** (**Code**) để ép IDA phân tích lại mã máy.
3. Nhấn **`F5`** lại, luồng Decompile hoàn chỉnh của thuật toán mã hóa đã xuất hiện đầy đủ.

---

## 4. Phân Tích Thuật Toán Mã Hóa & Giải Bài

Mã giả C sau khi khắc phục lỗi decompilation có dạng như sau:

```c
memset(v70, 0, 0x29u);
v30 = 0;
do
{
  ++v28;
  v31 = v30;
  v32 = (unsigned __int8)(*(v28 - 1) ^ key_part_b_4[v30 & 7] ^ key_part_a_5[v30 & 7]);
  ++v30;
  v33 = 41 * (v27 / 0x29);
  v34 = v27;
  v27 += 13LL;
  v35 = v34 - v33;
  LOBYTE(v33) = v29;
  v29 += 11;
  v70[0].m128i_i8[v35] = (v33 ^ 0x23) + __ROL1__(v32, v31 % 7 + 1);
}
while ( v30 != 41 );

```

### Chi Tiết Các Bước Mã Hóa Từng Ký Tự $s[i]$ ($i = 0 \rightarrow 40$)

1. Trộn khóa tuần hoàn (Lớp khóa XOR tĩnh)
Chương trình đọc từng ký tự đầu vào từ chuỗi bạn nhập. Để che giấu ký tự gốc, chương trình thực hiện phép toán XOR ký tự đó lần lượt với 2 mảng khóa cố định nằm trong bộ nhớ.

Vì mỗi mảng khóa chỉ dài 8 byte trong khi chuỗi đầu vào dài 41 byte, chương trình sẽ lấy khóa theo kiểu xoay vòng: dùng từ byte thứ 0 đến byte thứ 7, sau đó quay lại byte thứ 0 và lặp lại liên tục cho đến hết chuỗi.

2. Xoay bit linh hoạt (Xoay bit sang trái)
Byte dữ liệu thu được sau bước trộn khóa sẽ tiếp tục bị làm biến dạng ở cấp độ bit. Chương trình dịch chuyển tuần hoàn các bit của byte này sang bên trái.

Số lượng bit bị dịch chuyển không cố định mà thay đổi liên tục theo vị trí của ký tự trong chuỗi: ký tự đầu tiên bị xoay 1 bit, ký tự tiếp theo bị xoay nhiều bit hơn, tăng dần từ 1 đến 7 bit rồi quay lại chu kỳ từ 1. Điều này đảm bảo dù các ký tự giống nhau xuất hiện ở các vị trí khác nhau thì kết quả xoay bit vẫn hoàn toàn khác biệt.

3. Cộng giá trị nhiễu biến đổi (Cộng Salt động)
Ở bước này, chương trình tự tạo ra một giá trị "nhiễu" (Salt) riêng biệt cho từng lượt mã hóa. Giá trị nhiễu này được tính toán dựa trên chỉ số vòng lặp hiện tại (giá trị tăng dần theo từng bước) kết hợp với một hằng số cố định.

Sau đó, byte dữ liệu đã xoay bit ở bước 2 sẽ được cộng trực tiếp với giá trị nhiễu này. Nếu kết quả phép cộng bị tràn quá giới hạn lưu trữ của 1 byte (lớn hơn 255), chương trình sẽ chỉ giữ lại phần giá trị nằm trong phạm vi chuẩn 1 byte (từ 0 đến 255).

4. Xáo trộn vị trí lưu trữ (Hoán vị chỉ số)
Sau khi một ký tự đã trải qua đủ 3 bước biến đổi về mặt giá trị, chương trình không lưu byte kết quả vào đúng thứ tự ban đầu của nó.

Thay vào đó, nó nhảy vị trí lưu theo quy luật "nhảy cách": vị trí lưu mới được tính bằng cách lấy chỉ số hiện tại nhân với 13, sau đó chia lấy phần dư cho tổng độ dài chuỗi là 41. Việc này làm cho các byte dữ liệu sau khi mã hóa bị xáo trộn thứ tự hoàn toàn trên bộ nhớ Stack trước khi đưa đi so sánh với mảng đáp án.
---

## 5. Trích Xuất Dữ Liệu Hằng Số & Xử Lý Little-Endian

Cuối hàm, chương trình so sánh mảng `v70` với dữ liệu đệm trong `.rodata`:

```c
v37 = _mm_or_si128(
        _mm_xor_si128(_mm_load_si128((const __m128i *)&xmmword_555555556460), v70[0]),
        _mm_xor_si128(_mm_load_si128((const __m128i *)&xmmword_555555556470), v70[1]));

```

### Kiểm Tra Vùng Nhớ `.rodata` Trong IDA:

```assembly
.rodata:0000555555556450 key_part_b_4    db 5Bh, 75h, 0B4h, 7Bh, 0CBh, 5Dh, 73h, 0E6h
.rodata:0000555555556458 key_part_a_5    db 19h, 0A4h, 0C7h, 52h, 6Eh, 1, 9Bh, 0F0h
.rodata:0000555555556460 xmmword_555555556460 xmmword 32F47EA0EB7DB2880F84C16C1B790523h
.rodata:0000555555556470 xmmword_555555556470 xmmword 17456A6A3A3642DD16BF26C5C170F5C6h
.rodata:0000555555556420 expected_3     db 23h, 5, 79h, ...

```

> **Lưu ý về Little-Endian:** Do kiến trúc x86-64 lưu trữ byte thấp trước, các giá trị `xmmword` hiển thị dưới dạng số Hex lớn cần được đảo ngược chuỗi byte (đọc từ phải sang trái) để thu được đúng thứ tự byte trong bộ nhớ:
> * `xmmword_6460`: `0x23, 0x05, 0x79, 0x1B, 0x6C, 0xC1, 0x84, 0x0F, 0x88, 0xB2, 0x7D, 0xEB, 0xA0, 0x7E, 0xF4, 0x32`
> * `xmmword_6470`: `0xC6, 0xF5, 0x70, 0xC1, 0xC5, 0x26, 0xBF, 0x16, 0xDD, 0x42, 0x36, 0x3A, 0x6A, 0x6A, 0x45, 0x17`
> * 9 byte cuối của `expected_3` (từ offset 32): `0xF4, 0x4C, 0xCD, 0x84, 0xAE, 0x27, 0x8C, 0xC8, 0x38`
> 
> 

---

## 6. Python Solve Script

Do toàn bộ thuật toán mã hóa là các phép toán thuận nghịch $1-1$, ta viết script Python để thực hiện giải ngược từ bước cuối cùng về ban đầu:

```python
def solve_real_flag():
    # =========================================================================
    # 1. Dữ liệu Ciphertext mục tiêu (41 bytes) thu được từ bộ nhớ
    # =========================================================================
    
    # 16 byte đầu tiên (xmmword_555555556460 đảo ngược theo Little-Endian)
    xmm_6460 = [
        0x23, 0x05, 0x79, 0x1B, 0x6C, 0xC1, 0x84, 0x0F, 
        0x88, 0xB2, 0x7D, 0xEB, 0xA0, 0x7E, 0xF4, 0x32
    ]
    
    # 16 byte tiếp theo (xmmword_555555556470 đảo ngược theo Little-Endian)
    xmm_6470 = [
        0xC6, 0xF5, 0x70, 0xC1, 0xC5, 0x26, 0xBF, 0x16, 
        0xDD, 0x42, 0x36, 0x3A, 0x6A, 0x6A, 0x45, 0x17
    ]
    
    # 9 byte cuối cùng trích xuất từ expected_3 [index 32..40]
    expected_3_tail = [
        0xF4, 0x4C, 0xCD, 0x84, 0xAE, 0x27, 0x8C, 0xC8, 0x38
    ]

    # Ghép thành mảng Ciphertext hoàn chỉnh 41 bytes
    v70 = xmm_6460 + xmm_6470 + expected_3_tail

    # 2. Khóa XOR tĩnh trích xuất từ .rodata
    key_part_b_4 = [0x5B, 0x75, 0xB4, 0x7B, 0xCB, 0x5D, 0x73, 0xE6]
    key_part_a_5 = [0x19, 0xA4, 0xC7, 0x52, 0x6E, 0x01, 0x9B, 0xF0]

    flag = [0] * 41

    # 3. Giải ngược thuật toán
    for i in range(41):
        # Bước A: Khôi phục vị trí xáo trộn trên stack
        dest_idx = (i * 13) % 41
        encrypted_byte = v70[dest_idx]
        
        # Bước B: Tính lại Salt động cho vòng lặp i
        salt = (i * 11) ^ 0x23
        
        # Bước C: Đảo ngược phép cộng Salt
        rotated_byte = (encrypted_byte - salt) & 0xFF
        
        # Bước D: Đảo ngược ROL1 (Xoay trái) bằng ROR1 (Xoay phải)
        shift = (i % 7) + 1
        v32 = ((rotated_byte >> shift) | (rotated_byte << (8 - shift))) & 0xFF
        
        # Bước E: Đảo ngược phép XOR với các mảng khóa
        flag[i] = v32 ^ key_part_b_4[i & 7] ^ key_part_a_5[i & 7]

    print("\n[+] Success! Decrypted Flag:")
    print("".join(chr(x) for x in flag))

if __name__ == "__main__":
    solve_real_flag()

```

### Kết quả chạy script:

```bash
$ python3 solve.py

[+] Success! Decrypted Flag:
BDSEC{e4SY_r3v3rS3_eNg1N33r1nG_cH4LL4ng3}

```

<img width="902" height="218" alt="image" src="https://github.com/user-attachments/assets/45b9a1cc-4cbc-4f82-b443-0a3b8515ed68" />

Thử lại Flag vừa tìm được với chương trình:

**KẾT QUẢ: SUBMIT THÀNH CÔNG!**
