# Password - Bush Bash CTF 2026 - Reverse Engineering / Hardware

Tool: Python 3, Pwntools, COBS Library, Netcat

Flag: **bushbash{i_l0v3_C0bs}**

---

## 1. Xác Định Cấu Trúc Và Giao Thức

Đầu tiên, em thực hiện phân tích thông tin mô tả bài toán và thông số kết nối được cung cấp nhằm xác định phương thức giao tiếp và cơ chế mã hóa của thiết bị nhúng mục tiêu.

Thông tin thu được như sau:

* **Địa chỉ kết nối:** `34.40.133.67:6768` (Giao thức TCP)
* **Tài khoản cung cấp:** Username: `admin`, Password: `password`
* **Môi trường thiết bị:** Mô phỏng thiết bị phần cứng kết nối qua cổng USB / Serial Console.
* **Gợi ý quan trọng từ đề bài:** "cobbled mess" (thông tin bị trộn lẫn) và "maybe something's missing?" (thiếu ký tự báo hiệu định dạng).
* **Công cụ phân tích:** Python 3.13, thư viện `pwntools`, thư viện `cobs`.

### Nhận xét

Từ các dữ kiện ban đầu, em đưa ra một số nhận xét quan trọng:

* Lời gọi kết nối mạng mô phỏng giao tiếp phần cứng qua chuẩn nối tiếp (UART/USB Serial).
* Cụm từ **"cobbled"** trong đề bài là một chi tiết chơi chữ (pun) trực tiếp nhắc đến thuật toán mã hóa **COBS (Consistent Overhead Byte Stuffing)** – một chuẩn mã hóa gói tin cực kỳ phổ biến trong các hệ thống nhúng và thiết bị USB.
* Thuật toán COBS có cơ chế loại bỏ toàn bộ các byte NULL (`0x00`) bên trong chuỗi dữ liệu và chỉ sử dụng duy nhất một byte `0x00` ở cuối gói tin làm ký tự báo hiệu kết thúc packet (**Sentinel Value**).
* Vì vậy, nếu gửi các dữ liệu chuỗi ASCII thông thường qua Netcat mà không mã hóa COBS và không có byte `0x00` ở cuối, thiết bị sẽ không thể nhận diện được điểm dừng của lệnh và dẫn đến hiện tượng treo hoặc tràn bộ đệm.

---

## 2. Chạy Thử Và Ghi Nhận Hiện Tượng

Khi em tiến hành chạy thử lệnh kết nối trực tiếp bằng Netcat:

```bash
nc 34.40.133.67 6768

```

Màn hình xuất hiện dòng thông báo:

```c
------------Waiting for username...

```

Sau đó em nhập `admin` và ấn Enter, nhưng terminal lập tức rơi vào trạng thái treo (hang) và không nhận thêm bất kỳ phản hồi nào từ phía server.

**Tuy Nhiên**, khi em chuyển sang sử dụng script Python kết hợp thư viện `pwntools` để tương tác trực tiếp và gửi các lệnh chuỗi thô (`ls`, `id`, `cat flag.txt`), chương trình lập tức bị ngắt kết nối và trả về thông báo lỗi từ server:

```text
More than 20 bytes received without sentinel value. Data is likely not encoded correctly. Stopping attempts...

```

Như vậy đúng như dự đoán, server giới hạn bộ đệm nhận là 20 bytes. Nếu nhận quá 20 bytes dữ liệu thô mà không tìm thấy ký tự dừng **sentinel value (`\x00`)**, thiết bị sẽ xác định dữ liệu sai định dạng mã hóa và chủ động ngắt kết nối (`EOFError`).

---

## 3. Phân Tích Giao Thức & Debug COBS

Để xác định chính xác cấu trúc gói tin mà thiết bị gửi/nhận, em kích hoạt chế độ Debug trong `pwntools` bằng lệnh `context.log_level = 'debug'`.

Khi kết nối vừa được thiết lập, thanh ghi dữ liệu nhận về dạng Hex Dump hiển thị như sau:

```text
[DEBUG] Received 0x35 bytes:
    00000000  0d 50 6c 65  61 73 65 20  4c 6f 67 69  6e 00 0d 2d  │·Ple│ase │Logi│n··-│
    00000010  2d 2d 2d 2d  2d 2d 2d 2d  2d 2d 2d 00  18 57 61 69  │----│----│---·│·Wai│
    00000020  74 69 6e 67  20 66 6f 72  20 75 73 65  72 6e 61 6d  │ting│ for│ use│rnam│
    00000030  65 2e 2e 2e  00                                     │e...│·│

```

Phân tích các byte Hex nhận được:

* **Đoạn 1:** `0d 50 6c 65 61 73 65 20 4c 6f 67 69 6e 00`
* Chuỗi ASCII: `"Please Login"` (độ dài 12 bytes).
* Byte đầu tiên `0x0d` (13): Trong quy tắc mã hóa COBS cho chuỗi không chứa byte NULL, byte đầu tiên chỉ offset độ dài `= độ dài chuỗi + 1` ($12 + 1 = 13 = 0x0D$).
* Byte cuối cùng `0x00`: Byte Sentinel kết thúc gói tin.


* **Đoạn 2:** `0d 2d 2d 2d 2d 2d 2d 2d 2d 2d 2d 2d 2d 00`
* Chuỗi ASCII: `"------------"` kết thúc bằng byte `0x00`.


* **Đoạn 3:** `18 57 61 69 74 69 6e 67 20 66 6f 72 20 75 73 65 72 6e 61 6d 65 2e 2e 2e 00`
* Chuỗi ASCII: `"Waiting for username..."` (độ dài 23 bytes, byte offset $23 + 1 = 24 = 0x18$), kết thúc bằng byte `0x00`.



### BẮT ĐƯỢC QUY LUẬT GIAO THỨC!

Toàn bộ quá trình truyền nhận giữa Client và Server phải tuân theo 2 quy tắc bắt buộc:

1. **Chiều gửi (Client -> Server):** Dữ liệu gửi đi phải được mã hóa qua hàm `cobs.encode()` và nối thêm byte `\x00` ở cuối payload.
2. **Chiều nhận (Server -> Client):** Đọc luồng dữ liệu cho đến khi gặp byte `\x00` (`io.recvuntil(b'\x00')`), cắt bỏ byte `\x00` ở cuối rồi giải mã bằng hàm `cobs.decode()`.

---

## 4. Giải Bài

Dựa trên cấu trúc giao thức COBS đã phân tích, em tiến hành xây dựng script tự động hóa quá trình đăng nhập và tương tác với thiết bị bằng ngôn ngữ Python.

### Mã Nguồn Exploitation Script (`Exploit_password.py`):

```python
from pwn import *
from cobs import cobs

context.log_level = 'info'

# Khởi tạo kết nối tới thiết bị mục tiêu
io = remote('34.40.133.67', 6768)

def recv_msg():
    """Hàm nhận gói tin từ server cho đến byte Sentinel \\x00 và giải mã COBS"""
    raw = io.recvuntil(b'\x00', timeout=3)
    if not raw:
        return None
    
    encoded = raw[:-1]  # Loại bỏ byte \x00 ở cuối
    if not encoded:
        return ""
        
    try:
        return cobs.decode(encoded).decode('utf-8', errors='ignore')
    except Exception as e:
        return f"[Decode error: {e}]"

def send_msg(text):
    """Hàm mã hóa COBS cho chuỗi văn bản và gửi kèm byte Sentinel \\x00"""
    payload = cobs.encode(text.encode('utf-8')) + b'\x00'
    io.send(payload)

# ==========================================
# 1. TIẾN HÀNH ĐĂNG NHẬP (COBS HANDSHAKE)
# ==========================================
print("[*] Đang đọc các banner ban đầu từ thiết bị...")
print(recv_msg()) # Nhận "Please Login"
print(recv_msg()) # Nhận "------------"
print(recv_msg()) # Nhận "Waiting for username..."

print("[*] Gửi Username (admin)...")
send_msg("admin")

print(recv_msg()) # Nhận "Waiting for password..."

print("[*] Gửi Password (password)...")
send_msg("password")

# ==========================================
# 2. XÁC NHẬN ĐĂNG NHẬP VÀ LẤY FLAG
# ==========================================
flag_response = recv_msg()
print(f"\n[+] Kết quả phản hồi từ thiết bị:\n{flag_response}")

io.close()

```

### Kết Quả Thực Thi

Chạy script trên terminal Kali Linux thu được kết quả như sau:

```bash
(base) ┌──(kali㉿kali)-[/mnt/hgfs/CYBERKNIGHT/Bush Bash CTF 2026/Reverse]
└─$ python3 Exploit_password.py
[+] Opening connection to 34.40.133.67 on port 6768: Done
[*] Đang đọc các banner ban đầu từ thiết bị...
Please Login
------------
Waiting for username...
[*] Gửi Username (admin)...
Waiting for password...
[*] Gửi Password (password)...

[+] Kết quả phản hồi từ thiết bị:
Your flag is bushbash{i_l0v3_C0bs}

[*] Closed connection to 34.40.133.67 port 6768

```

**LẤY FLAG THÀNH CÔNG!**

Flag của bài tập là: **`bushbash{i_l0v3_C0bs}`**
