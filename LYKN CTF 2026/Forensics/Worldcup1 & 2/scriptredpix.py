from PIL import Image

img = Image.open("worldcup1_challenge.png").convert("RGB")
pixels = list(img.getdata())

bits = []
for r, g, b in pixels:
    bits.append(r & 1)   # lấy LSB của kênh đỏ

data = bytearray()
for i in range(0, len(bits) // 8 * 8, 8):
    byte = 0
    for bit in bits[i:i+8]:
        byte = (byte << 1) | bit
    data.append(byte)

print(data[:100])
