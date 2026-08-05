# Whispering Feather - Kali Team CTF 2026 - Reverse Engineering

**Tool:** QEMU (aarch64), GDB-multiarch, IDA Pro / Ghidra

**Flag:** **KaliTeam{p0lyg1ot_b3h1nd_th3_m1rr0r}**

---

## 1. Phân Tích Tĩnh (Static Analysis) & Đặt Vấn Đề

Khi bắt đầu một bài Reverse, bước đầu tiên luôn là ném file thực thi vào một trình dịch ngược (Decompiler) như **IDA Pro** hoặc **Ghidra** để xem chương trình hoạt động như thế nào.

Qua phân tích mã giả (Pseudocode) trong IDA, ta phát hiện logic của bài toán diễn ra như sau:

1. **Nhận input:** Chương trình yêu cầu người dùng nhập vào một chuỗi (gọi là *seals*).
2. **Kiểm tra độ dài:** Nó đếm số lượng ký tự nhập vào và kiểm tra xem có bằng **51** hay không.
```c
if ( v4 != 51 )
  goto LABEL_48; // Nhảy đến phần in ra thông báo lỗi

```


3. **Tạo Key hợp lệ (Sinh đáp án):** Chương trình tiến hành hàng loạt các phép toán phức tạp (XOR, dịch bit, vòng lặp) trên các mảng tĩnh để xây dựng lên một chuỗi chuẩn. Dấu hiệu nhận biết là hàm `qmemcpy(v143, "wing-", 5);` cho thấy chuỗi này luôn bắt đầu bằng chữ `wing-`.
4. **So sánh (Verify):** Đưa chuỗi 51 ký tự của người dùng so sánh với chuỗi vừa được tạo ra bằng các lệnh mã máy nâng cao (như `veorq_s8` trong ARM64).

### Tại sao lại chọn cách giải này (Dynamic Debugging)?

Nhìn vào thuật toán tạo Key trong IDA, ta thấy nó rất lằng nhằng và tốn thời gian nếu cố gắng viết script (Python/C) để mô phỏng lại (Static Analysis).

Tuy nhiên, có một lỗ hổng trong logic: **Dù mã hóa phức tạp đến đâu, thì đến cuối cùng, chương trình vẫn phải đặt cái Key chuẩn đó vào bộ nhớ (Ram/Stack) để so sánh với Input của chúng ta**.

**Tư duy:** Thay vì giải toán, ta sẽ dùng Debugger (GDB) để "chặn đầu" chương trình ngay tại thời điểm nó chuẩn bị so sánh, rồi ngang nhiên "đọc trộm" đáp án từ trong bộ nhớ của nó.

---

## 2. Xác Định Vị Trí Đặt Breakpoint

Để đọc trộm được bộ nhớ, ta phải làm cho chương trình **tạm dừng (pause)** đúng lúc. Vị trí tuyệt vời nhất để dừng chính là ngay sau khi nó kiểm tra độ dài chuỗi xong.

**Từ đâu ta biết đặt Breakpoint tại `0x4005E4`?**

1. Mở file trong IDA, ta tìm đến đoạn mã C kiểm tra độ dài: `if ( v4 != 51 )`.
2. Ta ấn phím **TAB** trong IDA để chuyển từ chế độ giả C (Pseudocode) sang chế độ mã máy (Assembly).
3. Đoạn mã C kia tương ứng với dòng lệnh Assembly:
```assembly
.text:00000000004005E4  B.NE  loc_40083C

```


*Lệnh `B.NE` (Branch if Not Equal) nghĩa là "Nếu độ dài không bằng 51 thì nhảy đến chỗ báo lỗi".*
4. Nhìn vào cột bên trái trong IDA, ta thấy địa chỉ của lệnh này chính là `0x4005E4`. Do đó, ta sẽ ra lệnh cho GDB đặt một cái chốt chặn (Breakpoint) ngay tại tọa độ này.

---

## 3. Debug Động & Lấy Key Từ Stack

### Bước 3.1: Kết nối Debugger

Do đây là file ARM64, ta chạy nó qua QEMU kèm cổng debug:

```bash
# Terminal 1
qemu-aarch64 -g 1234 ./whispering_feather

```

Kết nối GDB và đặt Breakpoint vào tọa độ đã tìm được:

```gdb
# Terminal 2
target remote localhost:1234
b *0x4005E4
c

```

<img width="612" height="283" alt="image" src="https://github.com/user-attachments/assets/7c36e91d-9d59-4a7e-9d31-f4b6c5dc724e" />

### Bước 3.2: Tại sao phải nhập 51 chữ 'A'?

Lúc này ở Terminal 1, chương trình đang yêu cầu `Present the three seals:`.
Ta bắt buộc phải nhập một chuỗi dài **đúng 51 ký tự** (ví dụ: 51 chữ `A`).

<img width="1453" height="332" alt="image" src="https://github.com/user-attachments/assets/75fb2002-c546-4f14-b4d2-121307ba99e3" />

**Lý do:**

* Breakpoint của ta nằm ở lệnh kiểm tra độ dài bằng 51.
* Nếu ta nhập lung tung (ví dụ 10 chữ), chương trình sẽ nhận thấy sai độ dài và vứt bỏ input của ta ngay lập tức, dẫn đến kết thúc sớm.
* Ta dùng 51 chữ `A` như một "hình nhân thế mạng" để đánh lừa chương trình rằng: *"Tôi đã nhập đủ độ dài rồi, hãy đi vào vòng trong (vòng so sánh chuỗi) đi"*. Khi chương trình đi vào vòng trong, nó sẽ tự động sinh ra chuỗi Key thật.

<img width="887" height="137" alt="image" src="https://github.com/user-attachments/assets/debb5d87-07d6-4017-8ea1-8b7c201c06bb" />

### Bước 3.3: Mò mẫm trong Memory (Stack)

Ngay khi nhập 51 chữ `A`, Breakpoint kích hoạt, chương trình bị đóng băng tại `0x4005E4`.

Lúc này, ta dùng lệnh `disass` để xem chương trình chuẩn bị làm gì tiếp theo:

```gdb
disass $pc-0x20, $pc+0x20

```

<img width="712" height="436" alt="image" src="https://github.com/user-attachments/assets/a54a26f2-9ac4-4309-b29b-a5c696217975" />

*(Lệnh này có nghĩa là: Hãy dịch ngược mã máy từ vị trí hiện tại (`$pc`) lùi về trước 0x20 bytes và tiến tới 0x20 bytes).*

Nhìn vào kết quả Assembly in ra:

```assembly
0x4005e8:  ldp  q0, q1, [sp, #544]
0x4005ec:  add  x8, sp, #0x220

```

**Phân tích dòng này:**

* `sp` là Stack Pointer (con trỏ trỏ đến vùng nhớ cục bộ của chương trình hiện tại).
* Chương trình đang dùng lệnh `ldp` (Load Pair) để bốc dữ liệu từ địa chỉ `[sp, #544]` (tức là `$sp + 544`) đưa vào các thanh ghi `q0, q1` để chuẩn bị đưa vào hàm kiểm tra.
* Suy luận logic: Cái thứ chuẩn bị được đem ra so sánh với 51 chữ `A` của ta, chắc chắn phải là **Key thật**. Vậy Key thật đang nằm ở địa chỉ `$sp + 544`.

### Bước 3.4: Trích xuất thành quả

Biết được vị trí giấu vàng, ta dùng lệnh `x` (Examine - kiểm tra bộ nhớ) trong GDB:

* `x/51sb`: In ra **51** ký tự (**s**tring) dưới dạng **b**yte.
* Từ địa chỉ: `$sp + 544`.

```gdb
x/51sb $sp + 544

```

GDB lập tức in ra chuỗi đang nằm ở đó:
`wing-CSBWUGKJGUHGSGJ4F5XB:037413d7:7b456423ebd50c2f`

<img width="997" height="637" alt="image" src="https://github.com/user-attachments/assets/23cf407f-c8f1-4e67-a4ab-12d86d573381" />

---

## 4. Kết Luận

1. Tắt GDB, chạy chương trình bình thường ở Terminal.
2. Nhập chính xác chuỗi `wing-CSBWUGKJGUHGSGJ4F5XB:037413d7:7b456423ebd50c2f` thu được vào.
3. Phần mềm báo Correct và mã hóa ra Flag thật: **KaliTeam{p0lyg1ot_b3h1nd_th3_m1rr0r}**

<img width="1447" height="142" alt="image" src="https://github.com/user-attachments/assets/28c64c24-90e6-4ab0-aa21-671e44826f06" />
