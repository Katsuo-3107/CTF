# So when i nc to server its give me like this
nc 51.79.140.18 13470

My generator: s_{n+1} = (a*s_n + c) mod m  (a, c, m, seed all secret)

Here are 12 consecutive outputs:

out[0] = 200564991898233

out[1] = 128238004802751

out[2] = 35939749856488

out[3] = 78109908421325

out[4] = 205650255292159

out[5] = 93504096724301

out[6] = 269533145329248

out[7] = 15503613937838

out[8] = 88924333280014

out[9] = 80962367502167

out[10] = 199378512992121

out[11] = 185596447656806

Predict out[12] to earn the flag.

out[12] = 

Time out. Connection closed.

* This is a classic cryptography challenge involving a Linear Congruential Generator (LCG). Because the server provides raw internal states without any truncation, the LCG is completely predictable.
