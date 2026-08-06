# Bush Bash CTF 2026 - \langle\rangle\langle\rangle

Tool: Python 3, Z3 Solver (`z3-solver`), Visual Studio Code / Text Editor

Flag: **bushbash{d1d_y0U_Us3_z3?}**

---

## 1. Xác Định Cấu Trúc File & Mã Nguồn C++

Đầu tiên, tiến hành mở file mã nguồn `message.cpp` được cung cấp trong bài toán để phân tích định dạng, kỹ thuật obfuscation và cấu trúc tổng quan.

Kết quả thu được như sau:

* **Định dạng file:** C++ Source Code (`.cpp`)
* **Kỹ thuật áp dụng:** C++ Template Metaprogramming (SFINAE & `std::enable_if_t`)
* **Số lượng biến cần tìm:** 214 biến nguyên (`flag_0` đến `flag_213`) đại diện cho các ký tự trong chuỗi thông điệp.
* **Cấu trúc kiểm tra:** Các dòng `using Constraint_X = ...;` (kéo dài đến hơn 500 constraint).
* **Cơ chế xác thực:** Macro `FLAGMESSAGE` nhận vào 214 tham số. Nếu các giá trị này không thỏa mãn toàn bộ các constraint được định nghĩa thông qua C++ Template, trình biên dịch sẽ báo lỗi Compile-Time Error.

### Nhận xét

Từ kết quả phân tích có thể đưa ra một số nhận xét:

* Bài toán không yêu cầu reverse engineering file thực thi binary (`.exe` hay ELF) thông thường, mà kiểm tra logic trực tiếp trên mã nguồn C++ ở thời điểm biên dịch (Compile-Time Validation).
* Chương trình định nghĩa các kiểu dữ liệu Template đóng vai trò là các phép toán đại số ($<$, $\le$, $>$, $\ge$, $\%$, $+$, $\times$).
* Do có 214 ẩn số với hơn 500 phương trình và bất phương trình ràng buộc chéo lẫn nhau, việc giải bằng tay hoặc brute-force vét cạn thông thường là hoàn toàn vô vọng.
* Phương pháp tối ưu nhất là trích xuất toàn bộ hệ phương trình này và đưa vào một công cụ **SMT Solver** (như Microsoft Z3 Solver) để tự động giải hệ phương trình tuyến tính/phi tuyến.

---

## 2. Phân Tích Logic & Các Điều Kiện Ràng Buộc (Constraints)

Đi sâu vào phân tích các định nghĩa Template trong mã nguồn C++, ta xác định được quy tắc chuyển đổi từ Template C++ sang các phép toán đại số tương ứng:

1. **`FlagValue<N>::Value`**: Đại diện cho giá trị ASCII của ký tự thứ `N` trong flag (`flag_N`).
2. **`Lt<L, R>`**: Phép so sánh nhỏ hơn ($L < R$).
3. **`Lteq<L, R>`**: Phép so sánh nhỏ hơn hoặc bằng ($L \le R$).
4. **`Gt<L, R>`**: Phép so sánh lớn hơn ($L > R$).
5. **`Gteq<L, R>`**: Phép so sánh lớn hơn hoặc bằng ($L \ge R$).
6. **`Divides<L, R>`**: Phép toán chia hết / Modulo ($L \bmod R = 0$).
7. **`Equ<c1, c2, t1, v1, v2, v3, v4, v5>`**: Phương trình tuyến tính kết hợp 5 biến:

$$c_1 \cdot v_1 + c_2 \cdot v_2 + t_1 \cdot v_3 = v_4 + v_5$$



Tất cả các điều kiện này được khai báo dưới dạng các dòng kiểu:

```cpp
using Constraint_1 = Lt<FlagValue<0>::Value, FlagValue<1>::Value>;
using Constraint_2 = Equ<2, 3, 1, FlagValue<12>::Value, FlagValue<40>::Value, FlagValue<99>::Value, FlagValue<3>::Value, FlagValue<100>::Value>;

```

---

## 3. Xây Dựng Script Giải Bằng Z3 Solver

Để tự động hóa quá trình giải, ta viết một script Python sử dụng **Regex** để parse file `message.cpp`, chuyển đổi các Template C++ thành các biểu thức toán học tương ứng và thêm vào **Z3 Solver**.

### Lưu ý về Môi Trường (Troubleshooting)

Khi cài đặt thư viện Z3 trên Python, cần lưu ý cài đúng package `z3-solver`. Tránh cài nhầm package `z3` gốc trên PyPI vì sẽ gây ra lỗi `ImportError: cannot import name 'Solver' from 'z3'`.

Thực hiện cài đặt lại môi trường:

```bash
pip uninstall z3
pip uninstall z3-solver
pip install z3-solver

```

### Mã Nguồn Script Giải (`Decoding_angle_langle.py`)

```python
import re
from z3 import Solver, Int, sat

def solve_flag():
    # Load file C++ chua cac constraint
    with open("message.cpp", "r") as f:
        cpp_code = f.read()

    solver = Solver()
    
    # Khoi tao 214 bien Z3 tuong ung voi flag_0 den flag_213
    env = {"flags": [Int(f'flag_{i}') for i in range(214)]}

    # Gioi han mien gia tri trong pham vi cac ky tu ASCII in duoc (32 -> 126)
    for f in env["flags"]:
        solver.add(f >= 32, f <= 126)

    # Chuyen doi 'FlagValue<X>::Value' thanh 'flags[X]'
    def parse_val(v_str):
        v_str = v_str.strip()
        return re.sub(r'FlagValue<(\d+)>::Value', r'flags[\1]', v_str)

    # Parse tung dong constraint
    for line in cpp_code.splitlines():
        line = line.strip()
        if not line.startswith("using Constraint_"):
            continue
            
        # Trich xuất ten op va danh sach tham so
        match = re.search(r'=\s*([A-Za-z]+)<(.+)>;', line)
        if not match:
            continue
            
        op = match.group(1)
        args = match.group(2).split(',')
        
        # Chuyen doi logic template sang bieu thuc Z3
        if op == "Equ":
            c1, c2, t1 = map(int, args[0:3])
            v1, v2, v3, v4, v5 = map(parse_val, args[3:8])
            expr = f"{c1} * {v1} + {c2} * {v2} + {t1} * {v3} == {v4} + {v5}"
            solver.add(eval(expr, {}, env))
            
        elif op in ["Lt", "Lteq", "Gt", "Gteq", "Divides"]:
            left = parse_val(args[0])
            right = parse_val(args[1])
            if op == "Lt":
                solver.add(eval(f"{left} < {right}", {}, env))
            elif op == "Lteq":
                solver.add(eval(f"{left} <= {right}", {}, env))
            elif op == "Gt":
                solver.add(eval(f"{left} > {right}", {}, env))
            elif op == "Gteq":
                solver.add(eval(f"{left} >= {right}", {}, env))
            elif op == "Divides":
                solver.add(eval(f"{left} % {right} == 0", {}, env))

    # Kiem tra tinh thoa man va in ket qua
    if solver.check() == sat:
        m = solver.model()
        flag_chars = [chr(m[env["flags"][i]].as_long()) for i in range(214)]
        print("Agent Message / Flag:", "".join(flag_chars))
    else:
        print("Error: Constraints unsatisfiable.")

if __name__ == "__main__":
    solve_flag()

```

---

## 4. Giải Bài & Khôi Phục Flag

Thực thi script Python vừa khởi tạo:

```bash
└─$ python3 Decoding_angle_langle.py

```

Kết quả đầu ra của chương trình:

```text
Agent Message / Flag: Congratulations on solving the challenge! (Yes I am having more text in here to make the challenge harder). I can't believe somebody beat a similar challenge last ctf manually. The flag is bushbash{d1d_y0U_Us3_z3?}

```

Z3 Solver đã giải thành công hệ constraint trong thời gian dưới 1 giây. Chuỗi thông điệp thu được hoàn chỉnh bao gồm văn bản dẫn nhập của tác giả và chuỗi Flag ở cuối.

### Flag Thu Được:

**`bushbash{d1d_y0U_Us3_z3?}`**
