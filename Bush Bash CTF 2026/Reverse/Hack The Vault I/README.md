# Hack The Vault I - Reverse Engineering Cơ Bản

Tool: IDA Pro, Detect It Easy (DIE), Linux Terminal / GDB

Flag: **bushbash{th1s-is-just-th3-beginning!}**

---

## 1. Xác Định Cấu Trúc File

Đầu tiên, em sử dụng công cụ **Detect It Easy (DIE)** (hoặc lệnh `file` trên Linux) để phân tích sơ bộ file thực thi nhằm xác định định dạng, kiến trúc, trình biên dịch và các thông tin bảo vệ cơ bản trước khi tiến hành phân tích mã nguồn.

Kết quả thu được như sau:

* **Định dạng file:** ELF64 (Executable and Linkable Format 64-bit)
* **Kiến trúc:** AMD64 (x86-64)
* **Loại chương trình:** Console Application / Dynamic Executable
* **Hệ điều hành mục tiêu:** Linux 64-bit
* **Compiler:** GCC / Clang (C/C++)
* **Cơ chế bảo vệ:**
* **Stack Canary:** Đã được bật (`__readfsqword(0x28u)`)
* **NX (No-Execute):** Enabled


* **Thông tin Debug:** File đã bị strip một phần symbol, nhưng các hàm trong phần xử lý logic vẫn có thể định vị thông qua điểm nhập (`main`).

<img width="898" height="657" alt="image" src="https://github.com/user-attachments/assets/30b2cf9e-d45a-4a2d-94fb-2e35ac00e74c" />

### Nhận xét

Từ kết quả phân tích có thể đưa ra một số nhận xét:

* Chương trình được biên dịch cho kiến trúc **Linux 64-bit**, sử dụng các con trỏ và thanh ghi 64-bit (`RSP`, `RBP`, `RAX`,...).
* Không phát hiện dấu hiệu của các **Packer** hoặc **Protector** (như UPX, Themida,...), do đó có thể mở trực tiếp file trong **IDA Pro** hoặc **Ghidra** để tiến hành decompiling.
* Chương trình thiết lập `setvbuf` cho `stdin`, `stdout`, `stderr` về chế độ unbuffered (`_IONBF`), đây là thiết lập đặc trưng trong các bài CTF để đảm bảo dữ liệu không bị hoãn khi tương tác qua mạng.

---

## 2. Chạy Thử Phần Mềm

Khi tiến hành chạy thử phần mềm trên terminal, chương trình in ra lời thoại chuẩn bị cho thử thách và yêu cầu nhập mật khẩu:

```text
Enter the password: test_input
Better luck next time.

```

Khi nhập thử một chuỗi bất kỳ (`test_input`), phần mềm lập tức phản hồi `Better luck next time.` và kết thúc tiến trình.

**Nhận xét:** Chương trình thực hiện kiểm tra chuỗi nhập vào trực tiếp thông qua một hàm validation. Nếu đúng mật khẩu, chương trình sẽ chuyển sang nhánh thành công và trả về flag.

---

## 3. Phân Tích Logic Chương Trình (Decompile với IDA Pro)

Nạp file vào **IDA Pro** và truy cập vào hàm `main`, ta thu được đoạn mã giả C như sau:

```c
__int64 __fastcall main(int a1, char **a2, char **a3)
{
  setvbuf(stdin, nullptr, 2, 0);
  setvbuf(stdout, nullptr, 2, 0);
  setvbuf(stderr, nullptr, 2, 0);

  sub_11C9();
  if ( (unsigned int)sub_1233() )
  {
    puts(
      "It worked. The clues he left behind makes me believe that this case is not over just yet. We will need to continue"
      " our mission, and stop the Moss Man at all costs.");
    sub_1342();
  }
  else
  {
    printf("Better luck next time.");
  }
  return 0;
}

```

### Luồng xử lý của `main`:

1. Gọi `setvbuf` để tắt cơ chế buffer I/O.
2. Gọi hàm khởi tạo `sub_11C9()`.
3. Kiểm tra điều kiện qua hàm `sub_1233()`:
* Nếu `sub_1233()` trả về `1` (True): In ra thông báo thành công và gọi hàm `sub_1342()` (hàm thực thi in Flag).
* Nếu trả về `0` (False): In ra `Better luck next time.`.



---

### Phân tích hàm kiểm tra mật khẩu `sub_1233()`

Đi sâu vào phân tích hàm `sub_1233()`:

```c
_BOOL8 sub_1233()
{
  size_t n; // [rsp+0h] [rbp-120h]
  size_t v2; // [rsp+8h] [rbp-118h]
  char s[264]; // [rsp+10h] [rbp-110h] BYREF
  unsigned __int64 v4; // [rsp+118h] [rbp-8h]

  v4 = __readfsqword(0x28u); // Kiểm tra Stack Canary
  printf("Enter the password: ");
  fgets(s, 256, stdin);
  v2 = strlen(s2);
  n = strlen(s);
  if ( n && s[n - 1] == 10 )
    s[--n] = 0;
  return v2 == n && strncmp(s, s2, n) == 0;
}

```

#### Các bước xử lý trong `sub_1233()`:

1. **Kiểm tra Stack Canary:** Sử dụng `__readfsqword(0x28u)` để chống lỗi đè stack (Buffer Overflow).
2. **Nhập dữ liệu:** Dùng `fgets(s, 256, stdin)` đọc tối đa 255 ký tự từ người dùng vào biến `s`.
3. **Loại bỏ ký tự xuống dòng:**
```c
if ( n && s[n - 1] == 10 )
    s[--n] = 0;

```


Nếu ký tự cuối cùng là `10` (`\n` / ASCII Newline), chương trình ghi đè bằng `\0` (Null terminator) và giảm độ dài $n$ đi 1.
4. **So sánh mật khẩu:**
```c
return v2 == n && strncmp(s, s2, n) == 0;

```


Chương trình tính độ dài của chuỗi mẫu `s2` ($v2$) và độ dài chuỗi nhập $n$. Để hàm trả về `1`, cần đáp ứng đủ 2 điều kiện:
* Độ dài hai chuỗi phải bằng nhau (`v2 == n`).
* Hàm `strncmp(s, s2, n)` phải trả về `0` (hai chuỗi giống nhau hoàn toàn).



---

## 4. Bẫy Truncation Trong IDA Pro & Truy Tìm Password Đúng

Ta tiến hành kiểm tra biến global `s2` tại segment `.data`:

```assembly
.data:0000000000004068 s2              dq offset aTh3m0ssm4ni5h3
.data:0000000000004068                                         ; DATA XREF: sub_1233+49↑r
.data:0000000000004068                                         ; sub_1233:loc_12FC↑r
.data:0000000000004068 _data           ends                    ; "th3M0ssM4ni5h3re,y0uc4ntcatchm3"

```

### Phân tích bẫy Truncation:

* Khi nhìn vào tên nhãn tự động do IDA Pro tạo ra (`aTh3m0ssm4ni5h3`), chuỗi tưởng chừng như là `Th3m0ssm4ni5h3`.
* **Tuy nhiên**, IDA Pro thường tự động cắt ngắn (truncate) các tên nhãn string nếu chuỗi quá dài.
* Nhìn sang phần comment dữ liệu thực tế ở góc phải tại địa chỉ `.data:0000000000004068`, chuỗi đầy đủ được lưu trong bộ nhớ là:

```text
th3M0ssM4ni5h3re,y0uc4ntcatchm3

```

### Điểm khác biệt quan trọng:

1. **Độ dài chuỗi:** Chuỗi đầy đủ có độ dài $n = 30$ ký tự (thay vì 14 ký tự như tên nhãn bị cắt).
2. **Phân biệt chữ hoa/thường:** Chuỗi chuẩn bắt đầu bằng chữ `t` thường và chứa các ký tự `M` hoa (`th3M0ssM4n...`). Do `strncmp` phân biệt hoa/thường, việc nhập sai case sẽ khiến điều kiện so sánh bị thất bại.

---

## 5. Giải Bài & Lấy Flag

Sau khi đã xác định được Password chính xác là `th3M0ssM4ni5h3re,y0uc4ntcatchm3`, ta tiến hành nhập chuỗi này vào chương trình:

```text
Enter the password: th3M0ssM4ni5h3re,y0uc4ntcatchm3
It worked. The clues he left behind makes me believe that this case is not over just yet. We will need to continue our mission, and stop the Moss Man at all costs.
bushbash{th1s-is-just-th3-beginning!}

```

**Bypass & Kiểm tra điều kiện thành công!**

Chương trình vượt qua hàm `sub_1233()`, nhảy vào nhánh đúng và gọi `sub_1342()` để in ra Flag hoàn chỉnh của bài toán:

**Flag:** `bushbash{th1s-is-just-th3-beginning!}`
