#!/usr/bin/env python3

def u32(x): return x & 0xFFFFFFFF
def rol2(val, count):
    count %= 16
    val &= 0xFFFF
    return ((val << count) | (val >> (16 - count))) & 0xFFFF

# 1. Generate PRNG buffer
BASE = 0x555555558080
v5 = -1847521883 & 0xFFFFFFFF
buf = bytearray(2048)

for v4 in range(2048):
    sum1 = u32(v5 + v4 + 73244475)
    v6 = u32(sum1 ^ u32(sum1 << 13))
    temp = u32(v6 >> 17) ^ v6
    v5 = u32(u32(32 * temp) ^ temp)
    buf[v4] = (v5 >> 11) & 0xFF

# Helper functions to patch memory
def set_w(addr, val):
    off = addr - BASE
    buf[off] = val & 0xFF
    buf[off+1] = (val >> 8) & 0xFF

def set_b(addr, val):
    buf[addr - BASE] = val & 0xFF

def set_d(addr, val):
    off = addr - BASE
    for i in range(4):
        buf[off+i] = (val >> (8*i)) & 0xFF

# 2. Apply all memory patches from decompiler
set_w(0x5555555580A0, 32149)
set_w(0x555555558224, 5879)
set_w(0x55555555822B, -24901)
set_w(0x555555558372, -25156)
set_w(0x555555558377, 5199)
set_w(0x55555555810A, -14811)
set_w(0x5555555581CA, -11694)
set_w(0x55555555829D, -10880)
set_w(0x5555555582A4, -14203)
set_w(0x55555555852A, 27833)
set_w(0x55555555852F, -2850)
set_w(0x555555558116, 29532)
set_b(0x555555558226, 91)
set_b(0x55555555822D, 84)
set_b(0x555555558370, -100)
set_b(0x555555558379, -86)
set_b(0x5555555581C3, -23)
set_b(0x5555555581C7, 6)
set_b(0x5555555581CC, 9)
set_b(0x5555555583EC, -83)
set_d(0x5555555583F1, -1201983522)
set_b(0x5555555583F5, -118)
set_b(0x55555555829F, 92)
set_b(0x5555555582A6, 0x80)
set_b(0x555555558528, 87)
set_b(0x555555558531, 76)
set_b(0x555555558176, -33)
set_b(0x55555555817A, 61)
set_w(0x55555555817D, -23698)
set_b(0x55555555817F, 87)
set_b(0x5555555585DB, 107)
set_d(0x5555555585E0, 1157791348)
set_b(0x5555555585E4, -72)
set_w(0x555555558397, 6049)
set_w(0x55555555839E, -29950)
set_w(0x55555555870E, 3255)
set_w(0x555555558713, -20387)
set_w(0x55555555812E, 6363)
set_w(0x5555555582E1, -7732)
set_w(0x55555555813B, -26450)
set_w(0x555555558140, 25354)
set_w(0x555555558699, -11047)
set_w(0x555555558661, -8833)
set_w(0x555555558668, -16456)
set_w(0x555555558122, -6976)
set_b(0x555555558399, 97)
set_b(0x5555555583A0, 60)
set_b(0x55555555870C, 19)
set_b(0x555555558715, 109)
set_b(0x5555555582DA, -118)
set_b(0x5555555582DE, -19)
set_b(0x5555555582E3, -73)
set_b(0x5555555587BD, 39)
set_d(0x5555555587C2, 941162496)
set_b(0x5555555587C6, -123)
set_b(0x555555558139, -43)
set_b(0x555555558142, 69)
set_b(0x555555558692, 3)
set_b(0x555555558696, 98)
set_b(0x55555555869B, -119)
set_b(0x5555555584F0, 78)
set_d(0x5555555584F5, -1200103448)
set_b(0x5555555584F9, 102)
set_b(0x555555558663, -119)
set_b(0x55555555866A, 104)
set_b(0x555555558210, -16)
set_w(0x555555558212, -18085)
set_w(0x555555558217, 11715)
set_b(0x555555558219, -39)

# 3. Simulate state loop and collect required inputs
v22 = (-16657) & 0xFFFF
v48 = 23130 & 0xFFFFFFFF
v25 = 32149 ^ 0x7C31

inputs = []

for step in range(12):
    addr_input = v25 + 0x4000
    inputs.append(hex(addr_input))
    
    v28 = buf[v25] ^ (v25 >> 3)
    low_v48 = v48 & 0xFFFF
    v32 = (((low_v48 - 90) & 0xFF) % 7) + 1
    v31 = (v25 ^ (buf[v25 + 7] ^ ((76 - v22) & 0xFF))) & 0xFFFF
    
    if v28 == 0xC1:
        v41 = ((v31 ^ buf[v25 + 4]) ^ 0x6D) & 0xFF
        idx1 = (2 * v41 + 129) & 0x7FF
        idx2 = (2 * v41 + 128) & 0xFFFF
        v42 = (4919 * v41) ^ ((buf[idx1] << 8) | buf[idx2])
        v34 = (v42 ^ 0xA55A) & 0xFFFF
    elif v28 == 0xC0:
        v43 = (buf[v25 + 6] << 8) | buf[v25 + 5]
        v34 = (~rol2(v43, v32)) & 0xFFFF
    elif v28 == 0xC2:
        v33 = (v25 + 2) & 0xFFFF
        v34 = (v22 ^ (buf[v25 + 3] | (buf[v33] << 8))) & 0xFFFF
    else:
        v33 = (v25 + 2) & 0xFFFF
        v34 = (v25 + (low_v48 ^ (buf[v25 + 1] | (buf[v33] << 8)))) & 0xFFFF
        
    v22 = (v22 - 273) & 0xFFFF
    high_v48 = (((v48 >> 16) & 0xFFFF) + 573) & 0xFFFF
    low_v48 = (low_v48 + 257) & 0xFFFF
    v48 = (high_v48 << 16) | low_v48
    v25 = v34

print("Extracted Sequence of 12 Addresses:")
print(" ".join(inputs))