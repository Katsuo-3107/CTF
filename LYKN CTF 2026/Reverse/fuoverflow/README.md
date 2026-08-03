# Writeup CTF: Thử thách Anti-Screenshot (Reverse Engineering)

## 🎯 Mục tiêu của thử thách
Tìm tên hàm (function) trong chương trình ngăn cản việc chụp ảnh màn hình (screenshot). 
Định dạng Flag: `LYKNCTF{tên_hàm_viết_thường}`

---

## 🧠 Kiến thức cơ bản cho người mới (Beginner's Guide)
Trong Reverse Engineering (dịch ngược) trên hệ điều hành Windows, các chương trình (file `.exe`) không tự mình làm mọi thứ. Để tương tác với hệ điều hành (ví dụ: tạo cửa sổ, đọc file, kết nối mạng, chặn chụp màn hình...), chúng phải gọi các hàm có sẵn của Windows. Các hàm này được gọi là **Windows API (WinAPI)**.

Danh sách các hàm mà một file `.exe` "mượn" của Windows để sử dụng được lưu trong một bảng gọi là **Import Table** (Bảng Imports). Khi phân tích một file lạ, việc đầu tiên của Reverser là nhìn vào bảng Imports này để đoán xem chương trình có thể làm được những trò gì.

---

## 🛠️ Các bước giải quyết (Step-by-Step)

### Bước 1: Phân tích hành vi (Behavioral Analysis)
Đề bài cung cấp một manh mối cực kỳ quan trọng: *"app is transparent to my screen. I can see it, but I can’t capture it"* (Ứng dụng tàng hình khi chụp màn hình, nhìn bằng mắt thì thấy nhưng không thể chụp lại).
Đây là một hành vi đặc trưng của tính năng chống chụp màn hình trên Windows. 

### Bước 2: Sử dụng IDA Pro để tìm hàm
Thay vì phải đọc code Assembly phức tạp ngay từ đầu, chúng ta sẽ đi tìm tên hàm API gây ra hiện tượng này.
1. Mở file `fuoverflow_learning.exe` bằng **IDA Pro** (như bạn đã làm trong ảnh).
2. Nhìn lên thanh tab ở phía trên cùng, tìm và bấm vào tab **Imports** (Nếu không thấy, bạn có thể nhấn tổ hợp phím `Shift + F1`).
   - *Tab Imports liệt kê TẤT CẢ các hàm WinAPI mà chương trình này sử dụng.*
3. Bấm tổ hợp `Ctrl + F` (hoặc click vào bảng và gõ trực tiếp) để tìm kiếm các từ khóa liên quan đến cửa sổ (Window) hoặc màn hình hiển thị (Display). 

### Bước 3: Xác định hàm mục tiêu
Nếu bạn search trên Google với từ khóa: *"Windows API prevent screenshot"*, kết quả đầu tiên trả về sẽ chỉ đích danh hàm: **`SetWindowDisplayAffinity`**.
- Hàm này nằm trong thư viện `user32.dll`.
- Khi chương trình gọi hàm này và truyền vào tham số `WDA_EXCLUDEFROMCAPTURE` (hoặc `WDA_MONITOR`), Windows Manager sẽ tự động che đi cửa sổ này khi có lệnh chụp ảnh màn hình.

Khi bạn tìm kiếm tên hàm này trong tab **Imports** của IDA, bạn sẽ thấy nó xuất hiện.

### Bước 4: Lấy Flag
Đề bài yêu cầu lấy tên hàm, viết thường toàn bộ và không có khoảng trắng.
- Tên hàm: `SetWindowDisplayAffinity`
- Chuyển thành chữ thường: `setwindowdisplayaffinity`

Ghép vào định dạng của đề bài, ta có Flag cuối cùng:
**`LYKNCTF{setwindowdisplayaffinity}`**

---

## 💡 Bài học rút ra (Takeaways)
1. **Đừng vội đọc code Assembly:** Khi mới làm quen với Reverse, hãy tập phân tích hành vi chương trình trước.
2. **Imports là bạn đồng hành:** Bảng Imports trong IDA Pro hoặc x64dbg nói cho bạn biết rất nhiều về mục đích của một chương trình.
3. **Kỹ năng Google:** "Biết cách search" là một kỹ năng sinh tồn trong ngành An toàn thông tin. Mô tả hiện tượng bằng tiếng Anh trên Google thường sẽ đưa bạn trực tiếp đến tài liệu của Microsoft (MSDN).
