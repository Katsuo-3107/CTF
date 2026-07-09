from sage.all import *

p = 61996545789950044511807056126248141945304434838920379595334089328489467238193
F = GF(p)

# eigenvalues given
z2 = F['z'].gen()

lam1E = 60063441005095171597098858010795632629468865189663817083811738261468640425838*z2 + 18190931364402322785572512418893267163264663934344191594397727140941016963494
lam2E = 1933104784854872914708198115452509315835569649256562511522351067020826812355*z2 + 22576394155028824954295303146749596176130404633621215135608577696849350286187

# exponent
E = pow(1337,31337,p-1)
Einv = inverse_mod(E,p-1)

lam1 = lam1E^Einv
lam2 = lam2E^Einv

T = lam1 + lam2
D = lam1 * lam2

# brute missing digits of C entries
prefix00 = "504431219805193233494638855346643150"
prefix01 = "437561477922777662981107858757923689"

for s0 in range(10**6):
    C00 = F(int(prefix00 + str(s0).zfill(6)))
    for s1 in range(10**6):
        C01 = F(int(prefix01 + str(s1).zfill(6)))
        
        C = Matrix(F, [[C00,C01],[0,0]])  # rest solved automatically
        
        M = C^Einv
        
        a,b,c,d = M.list()
        flag_bytes = (int(a).to_bytes(16,'big') +
                      int(b).to_bytes(16,'big') +
                      int(c).to_bytes(16,'big') +
                      int(d).to_bytes(16,'big'))
        
        if all(32<=x<=126 for x in flag_bytes):
            print(b"BKISC{" + flag_bytes + b"}")
            exit()
            
