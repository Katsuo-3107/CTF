# Forensics Worldcup1 & 2 CTF - Writeup
Tool: strings, binwalk -e

Flag Worldcup1: LYKNCTF{Argentina3-2CaboVerde}
Flag Worldcup2: LYKNCTF{RespectToCaboVerde}

* So this 2 challenge give me 2 pictures about WORLDCUP 2026 but something very interesting

**String Worldcup1:**
'tEXtFlag_Hint
Look deeper in the red pixelsO++
*tEXtComment
The score was 3-2 after extra timey
4tEXtDescription
Argentina vs Cabo Verde - World Cup 2026
IDATx
HIDDEN_DATA_STARTPassword hint: What was the final score? Format: X-Y

**String Worldcup2:**
8BIM
bFBMD0a000a4e020000569a00004f1101007920010007350100c7950100c591020029b602000acc0200e3e20200e4530400
#A$5pBCE
ATO3b
flag_hidden.txt
flag_hidden.txtPK
RESPECT_TO_CABO_VERDE
The warriors fought bravely
Check the file structure

*  That give me all the info, using binwalk to know the file structure and any hidden file:
**Binwalk Worldcup2:**
 binwalk -e worldcup2_challenge.png

DECIMAL       HEXADECIMAL     DESCRIPTION
283620        0x453E4         Zip archive data, at least v2.0 to extract, compressed size: 29, uncompressed size: 27, name: flag_hidden.txt

WARNING: One or more files failed to extract: either no utility was found or it's unimplemented

* Unzip the file and we have flag.txt
cat flag_hidden.txt                  
LYKNCTF{RespectToCaboVerde}

*  But for worldCup1 there a little bit different
*  So from strings they say we need to look deeper in the red pixel -> thats mean i need to isolate the red pixel and then take all the bit ( 8 bit -> 1 byte )
*  With password and scripts python to have flag !!!
python3 scriptredpix.py
/mnt/hgfs/CYBERKNIGHT/LYKNCTF 2026/Forensics/scriptredpix.py:4: DeprecationWarning: Image.Image.getdata is deprecated and will be removed in Pillow 14 (2027-10-15). Use get_flattened_data instead.
  pixels = list(img.getdata())
bytearray(b'LYKNCTF{Argentina3-2CaboVerde}\xff\xfe\x9e\xb6\xf4\xea3\x0b%W\xc6\xb0\x19\xc6\xd2\x8c\x7fZ\xce\xe1j\x9c1f\x93\x128S\x12V\xc7u\xb9S\x94\xa2q\x1fK+\xdc\xc9H%\xa2r+G\x92\xf2\x0b\xc2\x07\xfd\x12BL\xe9\x96\xcc-K\x0b\xab5\x1e\x1d\x84u9')
