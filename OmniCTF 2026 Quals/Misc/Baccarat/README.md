# Baccarat Duel Betting Challenge - Programming & Applied Math

Tool: Python (Socket, SSL), tournament_stats.py

Flag: **omni{baccarat_kelly_goes_brrrr_6da7b1f}**

---

## 1. Xác Định Cấu Trúc & Phân Tích Logic

Đầu tiên, qua việc đọc mã nguồn và các file đính kèm của bài CTF, em xác định được cấu trúc và luật chơi của server Baccarat này:

* **Giao thức:** Kết nối qua TCP/SSL (Port 1337).
* **Mục tiêu:** Nhân số vốn (Bankroll) từ `1000` lên `100000` trong vòng tối đa **180 giây**.
* **Luật Baccarat cơ bản:** Tỉ lệ trả thưởng là 1:1 (Even money). Các ván hòa (Tie) sẽ được đánh lại cho đến khi có kết quả phân thắng bại.
* **AI Matchups (Các cặp đấu):** Game không dùng bài ngẫu nhiên hoàn toàn mà cho các Bot (AI) đấu với nhau. Tên của `BankerAI` và `PlayerAI` sẽ được hiển thị trước mỗi ván. Có tất cả 12 cặp đấu được xoay vòng ngẫu nhiên.

### Nhận xét

Từ những dữ kiện trên, bài toán đòi hỏi chúng ta phải tìm ra **lợi thế thống kê (Edge)** của từng cặp AI và áp dụng công thức quản lý vốn để tối đa hóa lợi nhuận trước khi hết thời gian.

---

## 2. Chạy Thử Phần Mềm & Vấn Đề Gặp Phải

Khi em viết script Python chạy thử để bot tự động tính toán xác suất thắng trực tiếp (Dynamic calculation) trên server dựa vào lịch sử ván bài, kết quả cho thấy:

```text
=== Table 8 | Round 6/12 | Resolved Bets 90 ===
BankerAI :: VoltaicAI
PlayerAI :: OmniCybr
Bankroll :: 828
Bet side [player/banker]:

```

Dù có lợi thế, Bankroll liên tục trồi sụt quanh mức 1,000 - 3,000 rồi từ từ cạn kiệt. Nguyên nhân là do **Độ lệch chuẩn (Variance)** của game Baccarat quá cao.
Một mẫu thử (sample size) khoảng 50-100 ván trên server là không đủ để tính chính xác win rate. Nếu tính sai win rate mà đặt cược lớn, bankroll sẽ bốc hơi rất nhanh.

---

## 3. Bypass Variance Bằng "Sniper Kelly"

Để giải quyết vấn đề nhiễu loạn thống kê, em chú ý đến file `tournament_stats.py` được cung cấp kèm theo mã nguồn.

Chạy file này ở local (giả lập 10,000 ván đấu cho mỗi cặp AI), ta có thể lấy được **Tỉ lệ thắng chính xác tuyệt đối (True Edge)** của tất cả 12 cặp đấu. Ví dụ:

* `BlackShard` (Banker) vs `OmniCybr` (Player) => Player thắng **57.7%**.
* `VoltaicAI` (Banker) vs `OmniCybr` (Player) => Player thắng **52.8%**.

Có được True Edge, em áp dụng **Tiêu chuẩn Kelly (Kelly Criterion)** để tính toán số tiền cược tối ưu cho mỗi ván:


$$f = 2p - 1$$


*(Trong đó $f$ là phần trăm vốn cần cược, $p$ là xác suất thắng thực tế).*

**Chiến thuật Sniper (Bắn tỉa):**
Tuy nhiên, nếu cược Kelly ở các bàn có win rate thấp (như 52.8%), vốn sẽ bị ngâm rất lâu hoặc bay màu do xui xẻo. Vì server chỉ cho 180 giây, em chia logic như sau:

* **Bàn yếu (Edge < 55%):** Đặt cược mức tối thiểu là `1` để nhanh chóng qua ván mà không mất tiền.
* **Bàn mạnh (Edge > 55%):** Nhồi Full Kelly (cược số tiền lớn) để Bankroll tăng theo cấp số nhân.

---

## 4. Giải Bài

Từ các phân tích trên, em lập bảng ánh xạ các cặp đấu (Hardcode Dictionary) và hoàn thiện đoạn script Python cuối cùng. Server sẽ bị vét sạch tiền chỉ sau vài giây chạm mặt các "Bàn mạnh".

**Mã nguồn Exploit:**

```python
import socket
import ssl
import sys

HOST = "baccarat-b1359a970862.inst.omnictf.com"
PORT = 1337

# Ánh xạ tỉ lệ thắng thực tế lấy từ tournament_stats.py
TRUE_EDGES = {
    ("BlackShard", "OmniCybr"): ("player", 0.577), 
    ("OmniCybr", "BlackShard"): ("banker", 0.560),
    ("BlackShard", "NorthStar"): ("player", 0.571),
    ("NorthStar", "BlackShard"): ("banker", 0.574),
    ("BlackShard", "NipCat"): ("player", 0.562),
    ("NipCat", "BlackShard"): ("banker", 0.555), 
    ("BlackShard", "VoltaicAI"): ("player", 0.549),
    ("VoltaicAI", "BlackShard"): ("banker", 0.525),
    ("VoltaicAI", "OmniCybr"): ("player", 0.528),
    ("OmniCybr", "VoltaicAI"): ("banker", 0.523),
    ("VoltaicAI", "NorthStar"): ("player", 0.521),
    ("NorthStar", "VoltaicAI"): ("banker", 0.526),
}

def solve():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    print(f"[*] Connecting to {HOST}:{PORT}...")
    with socket.create_connection((HOST, PORT)) as sock:
        with context.wrap_socket(sock, server_hostname=HOST) as ssock:
            f = ssock.makefile("r", encoding="ascii")
            
            banker = player = None
            bankroll = 0
            
            while True:
                line = f.readline()
                if not line: break
                    
                sys.stdout.write(line)
                sys.stdout.flush()
                
                # Bắt sự kiện
                if "FLAG ::" in line:
                    print("\n[+] Target reached! Check the flag above.")
                    break
                elif "Session result :: bankroll depleted" in line:
                    print("\n[-] Bankroll depleted due to variance. Run again.")
                    break
                elif "BankerAI ::" in line:
                    banker = line.split("::")[1].strip()
                elif "PlayerAI ::" in line:
                    player = line.split("::")[1].strip()
                elif "Bankroll ::" in line:
                    bankroll = int(line.split("::")[1].strip())
                    
                # Phản hồi chọn bên (player / banker)
                elif "Bet side [player/banker]:" in line:
                    pairing = (banker, player)
                    current_bet_side = TRUE_EDGES.get(pairing, ("player", 0.50))[0]
                    ssock.sendall(f"{current_bet_side}\n".encode('ascii'))
                    
                # Phản hồi số tiền cược (Áp dụng Sniper Kelly)
                elif "Bet amount" in line:
                    pairing = (banker, player)
                    if pairing in TRUE_EDGES:
                        current_bet_side, true_prob = TRUE_EDGES[pairing]
                        
                        if true_prob < 0.55:
                            bet_amount = 1 # Skip bàn yếu
                            print(f"[BOT] Skipping weak table. Betting {bet_amount}")
                        else:
                            # Full Kelly Criterion cho bàn mạnh
                            kelly = (2 * true_prob) - 1
                            bet_amount = max(1, int(bankroll * kelly))
                            print(f"[BOT] SNIPING strong table! Betting {bet_amount}")
                    else:
                        bet_amount = 1 
                        
                    ssock.sendall(f"{bet_amount}\n".encode('ascii'))

if __name__ == "__main__":
    solve()

```

Khi chạy kịch bản trên, Bot sẽ kiên nhẫn đánh `1` qua các bàn bất lợi và "bơm" cược từ mười mấy nghìn tiền vốn lên ngay khi gặp đối thủ yếu. Chỉ mất khoảng vài bàn mạnh, Bankroll cán mốc 100,000 và trả về flag!
