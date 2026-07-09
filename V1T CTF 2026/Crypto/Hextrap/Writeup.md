# CTF Writeup: Hextrap (V1t CTF 2026)

**Danh mục:** Mật mã học (Cryptography)  
**Flag:** `v1t{six_twists_one_smooth_order}`

## 1. Tổng quan về thử thách
Trong thử thách này, chúng ta được cung cấp một bản mã RSA tiêu chuẩn cùng với số mũ công khai $e$ và một module $n$ rất lớn. Thoạt nhìn, thiết lập RSA có vẻ hoàn toàn bình thường. Tuy nhiên, module $n$ đã được cấu trúc một cách đặc biệt với một lỗ hổng chí mạng liên quan đến các thừa số nguyên tố $p$ và $q$ của nó.

## 2. Lỗ hổng toán học
Chính nội dung của flag (`six_twists_one_smooth_order`) đã tiết lộ điểm yếu toán học cốt lõi. Các thừa số nguyên tố của $n$ được tạo ra sao cho một đường cong elliptic xác định trên trường hữu hạn $\mathbb{F}_p$ có một **bậc trơn (smooth order)**. Điều này nghĩa là số lượng các điểm trên đường cong là tích của nhiều số nguyên tố nhỏ.

Khi bậc của một đường cong elliptic là trơn bậc $B$ ($B$-smooth), chúng ta có thể khai thác nó bằng **Phương pháp Phân tích thừa số bằng Đường cong Elliptic của Lenstra (ECM)**. Bằng cách nhân một điểm trên đường cong với một vô hướng là hợp số lớn (tích của các số nguyên tố nhỏ), phép nhân vô hướng sẽ chạm tới "điểm vô cực" theo modulo $p$, nhưng *không* chạm theo modulo $q$.

Bởi vì phép cộng điểm trên đường cong elliptic đòi hỏi phải tìm nghịch đảo modulo của mẫu số của độ dốc, phép toán này sẽ thất bại chính xác tại thời điểm chúng ta chạm tới điểm vô cực đối với một trong các thừa số nguyên tố. Sự thất bại này xảy ra vì $\gcd(\text{mẫu số}, n)$ sẽ trả về chính thừa số nguyên tố $p$!

## 3. Chiến lược khai thác (Ý tưởng thuật toán)
Thay vì phụ thuộc vào các thư viện toán học nặng nề bên ngoài như SageMath, chúng ta có thể xây dựng một giải pháp gọn nhẹ bằng Python thuần theo các bước sau:

1. **Tạo Hệ số nhân Trơn (Smooth Multiplier):** Tính toán một số vô hướng lớn $M$ bằng cách nhân tất cả các lũy thừa của số nguyên tố lên đến một giới hạn nhất định (ví dụ: $2^{15}$).
2. **Xác định Đường cong Elliptic:** Sử dụng các đường cong có dạng $y^2 = x^3 + D$ và thử các giá trị tuần tự của $D$.
3. **Thiết lập Nghịch đảo Cửa sập (The Trapdoor Inverse):** Định nghĩa lại hàm tìm nghịch đảo modulo phục vụ cho phép cộng điểm. Thay vì chỉ báo lỗi khi xảy ra phép chia cho 0, hàm này sẽ liên tục kiểm tra xem $1 < \gcd(\text{mẫu số}, n) < n$ có đúng không. Ngay khi điều kiện này thỏa mãn, thuật toán sẽ lập tức "bắt" lấy và trả về thừa số nguyên tố $p$.
4. **Giải mã:** Ngay sau khi tìm ra $p$, chúng ta dễ dàng tính toán $q = n / p$ và số phi Euler $\phi = (p-1)(q-1)$. Từ đó, tính toán số mũ bí mật $d$ và giải mã bản mã PKCS1_OAEP để lấy flag.
WriteupHexTrap.md
4 KB
