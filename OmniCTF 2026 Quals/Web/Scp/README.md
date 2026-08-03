# Scp - Web Exploitation (Request Smuggling & SSTI)
Tool: Burp Suite Professional, Web Browser

Flag: **CTF{ganzir_was_already_in_the_fire_plan}**

---
## 1. Phân Tích Chức Năng Cửa Ngõ (Employee Access Relay)

Khi truy cập vào hệ thống, ta được đưa đến một trang cấu hình hệ thống nội bộ, cụ thể là phần **Employee Access Relay** như trong file `image_567334.png`. Tại đây, hệ thống rò rỉ một số thông tin cực kỳ quan trọng về kiến trúc mạng:

*   **Edge Parser (Proxy phía ngoài):** Xử lý request HTTP và ưu tiên đọc header `Transfer-Encoding: chunked`.
*   **Bridge Parser (Máy chủ backend):** Ưu tiên đọc header `Content-Length` trước khi chuyển tiếp các byte còn lại.
*   **Mục tiêu:** Cần truy cập vào endpoint `GET /employee/session` kèm theo header `X-Employee-Gate: internal` để mở khóa phiên làm việc (session). Do cơ chế bảo mật, proxy phía ngoài sẽ chặn việc truy cập trực tiếp vào endpoint này.

Sự bất đồng bộ trong cách xử lý request giữa **Edge** và **Bridge** (một bên dùng TE, một bên dùng CL) chính là điều kiện hoàn hảo để khai thác lỗ hổng **HTTP Request Smuggling (TE.CL)**.

<img width="2397" height="872" alt="image" src="https://github.com/user-attachments/assets/e8e55f25-2264-444b-a191-fbfc250e0011" />

---
## 2. Khai Thác HTTP/2 Downgrade Request Smuggling (H2.TE)

Bởi vì hệ thống hỗ trợ giao thức HTTP/2 ở mặt ngoài nhưng lại hạ cấp (downgrade) xuống HTTP/1.1 khi giao tiếp với máy chủ backend, ta có thể tiến hành tấn công **H2.TE Request Smuggling**. 

Em sử dụng công cụ **Burp Suite** để cấu hình và gửi một HTTP/2 request giả mạo nhằm "buôn lậu" (smuggle) một request thứ hai vào bên trong. Như được thể hiện trong file `image_56731a.png`, payload khai thác được xây dựng như sau:

```http
POST /employee HTTP/2
Host: ganzir-73b52e085462.inst.omnictf.com
Content-Type: text/plain
Content-Length: 236

POST /employee HTTP/1.1
Host: ganzir-73b52e085462.inst.omnictf.com
Transfer-Encoding: chunked
Content-Length: 4

0

GET /employee/session HTTP/1.1
Host: ganzir-73b52e085462.inst.omnictf.com
X-Employee-Gate: internal
Foo: x

```

<img width="1845" height="466" alt="image" src="https://github.com/user-attachments/assets/ff9d8ebc-9627-4ebb-a416-a53252ca682e" />

**Giải thích quá trình hoạt động:**

* **Proxy mặt ngoài (Edge):** Chuyển đổi HTTP/2 thành HTTP/1.1 và giữ nguyên header `Transfer-Encoding: chunked` do ta tiêm vào. Nó đọc đến chunk `0` và cho rằng request thứ nhất đã kết thúc, sau đó chuyển toàn bộ gói tin ra phía sau.
* **Máy chủ Backend (Bridge):** Nó nhìn thấy `Content-Length: 4`, do đó nó chỉ đọc đến ngay sau số `0`.
* Phần dữ liệu còn sót lại trong bộ đệm của backend chính là request thứ hai `GET /employee/session...`. Backend sẽ coi đây là khởi đầu của một request mới hợp lệ đi từ mạng nội bộ vào.

Kết quả của cuộc tấn công này là hệ thống xử lý request bí mật của ta và trả về một **JSON Web Token (JWT)** cấp quyền truy cập hợp lệ cho người dùng `cassie`, như được thấy trong tab JSON Web Token của Burp Suite ở file `image_567316.png`.

<img width="887" height="560" alt="image" src="https://github.com/user-attachments/assets/ebaaf7b4-53d4-490e-a53f-bac79bb47d8f" />

---

## 3. Phân Tích Lỗ Hổng SSTI (Renderer)

Sau khi có được session hợp lệ, hệ thống cấp cho ta quyền truy cập vào chức năng **Renderer** (Dùng để xem trước các mẫu thông báo khẩn cấp).

Tại giao diện này (tham khảo file `image_5672fa.png`), phần **Operator Notes** để lộ các thông tin của backend:

* **Engine:** Jinja2 (Template engine của Python).
* **Variables:** `wave`, `vector`.
* **Helper:** `read_file(path)` (Hàm tùy chỉnh được truyền thẳng vào môi trường template).
* **Mục tiêu (Flag copy):** `/flag.txt`.

Vì ứng dụng cho phép người dùng nhập trực tiếp dữ liệu vào ô "Template source" và engine Jinja2 sẽ render dữ liệu này, hệ thống dính lỗ hổng **Server-Side Template Injection (SSTI)**.

---

## 4. Lấy Flag (Giải Bài)

Thay vì phải dùng các payload Object Traversal phức tạp để bypass sandbox (như `__class__.__base__...`), ta có thể lợi dụng trực tiếp hàm helper `read_file(path)` mà backend đã cung cấp sẵn trong ngữ cảnh của template.

Ta chèn payload sau vào ô **Template source**:

```jinja2
wave: {{ read_file('/flag.txt') }}
vector: Ganzir lower transit spine

```

Nhấn nút **Render Template**. Cú pháp `{{ }}` sẽ ra lệnh cho engine Jinja2 thực thi hàm `read_file` với đường dẫn là `/flag.txt`. Kết quả trả về sẽ được in thẳng ra màn hình hiển thị.

Nhìn vào phần **Rendered Preview** trong file `image_5672fa.png`, ta đã thu được cờ thành công!

**Flag:** `CTF{ganzir_was_already_in_the_fire_plan}`

```

```
