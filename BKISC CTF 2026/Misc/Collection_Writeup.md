# Write-up CTF: Misc - Emoji Morse Code

## 1. Thông tin thử thách
- **Thể loại:** Misc
- **Tên thử thách:** Emoji Code
- **Định dạng Flag:** `BKISC{...}`
- **Input:**
```text
^💢😭😭😭 ^💢😭💢 ^😭😭 ^😭😭😭 ^💢😭💢😭 💢💢💢😭💢😭 😭💢💢😭 😭😭😭😭 😭😭😭😭💢 😭😭 😭😭💢💢😭💢 💢😭💢😭 😭😭😭😭 😭💢💢💢💢 💢😭 😭😭😭😭 😭😭💢💢😭💢 💢😭😭 💢💢💢💢💢 💢😭 💢😭💢😭💢💢 💢😭💢😭💢💢 💢😭💢😭💢💢 💢💢💢😭😭💢
```

## 2. Phân tích bài toán
Dữ liệu được cung cấp dưới dạng các cụm Emoji phân cách bởi khoảng trắng. Dựa vào flag mẫu `BKISC{...}`, ta tiến hành phân tích các cụm đầu tiên:

- **Cụm 1:** `💢😭😭😭` (Tương ứng với ký tự **B**)
- **Cụm 2:** `💢😭💢` (Tương ứng với ký tự **K**)
- **Cụm 3:** `😭😭` (Tương ứng với ký tự **I**)

Nhận thấy cấu trúc này trùng khớp hoàn toàn với **Mã Morse** (Morse Code) nếu ta thực hiện phép gán:
- 💢 = `-` (Dấu gạch / Dash)
- 😭 = `.` (Dấu chấm / Dot)

## 3. Quá trình giải mã
Tiến hành thay thế các emoji và tra bảng mã Morse quốc tế:


| Emoji | Morse | Ký tự |
| :--- | :--- | :--- |
| `💢😭😭😭` | `-...` | **B** |
| `💢😭💢` | `-.-` | **K** |
| `😭😭` | `..` | **I** |
| `😭😭😭` | `...` | **S** |
| `💢😭💢😭` | `-.-.` | **C** |
| `💢💢💢😭💢😭` | `---.-.` | **{** |
| `😭💢💢😭` | `. -- .` | **P** |
| `😭😭😭😭` | `....` | **H** |
| `😭😭😭😭💢` | `....-` | **4** |
| `😭😭` | `..` | **I** |
| `😭😭💢💢😭💢` | `..--.-` | **\_** |
| `💢😭💢😭` | `-.-.` | **C** |
| `😭😭😭😭` | `....` | **H** |
| `😭💢💢💢💢` | `.----` | **1** |
| `💢😭` | `-.` | **N** |
| `😭😭😭😭` | `....` | **H** |
| `😭😭💢💢😭💢` | `..--.-` | **\_** |
| `💢😭😭` | `-..` | **D** |
| `💢💢💢💢💢` | `-----` | **0** |
| `💢😭` | `-.` | **N** |
| `💢😭💢😭💢💢` | `-.-.--` | **!** |
| `💢😭💢😭💢💢` | `-.-.--` | **!** |
| `💢😭💢😭💢💢` | `-.-.--` | **!** |
| `💢💢💢😭😭💢` | `---..-` | **}** |

## 4. Kết quả
Ghép các ký tự lại, ta được thông điệp: `BKISC{PH4I_CH1NH_D0N!!!}`. 
Thử nghiệm với định dạng chữ thường theo yêu cầu của hệ thống:

**Flag:** `BKISC{ph4i_ch1nh_d0n!!!}`
