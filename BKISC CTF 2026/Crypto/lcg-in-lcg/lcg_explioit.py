from Crypto.Util.number import inverse

# Challenge parameters
p = 110750405221341147348299960157556065401964017527107650662558305631455812884301
leak = [108908476491924270471763704266265921193324099421446275962047345684000246424425, 41831312271929358942124899537418348352592263818917588226232693352518679651688, 94519902780394054937666978814593203986291644569948732220394452536354012149278, 51331736145908713848778469811361166206647060890602271056424360454744579243048, 92974700499443402879840078141124235478667977341536608385909809428741240450399, 56686328625729495952283793664681642635634105823683513393940265022737641361222, 56797695928013514925924882798604005522171437636267966933052503404404108982448, 105487294514821350651499549506856519843234840931696956699391691312019545317492, 38612553725976910446185243591935925099635948477723012352218606068556156177216, 55537592641006418725348239555467603522090410375200478286486056070962731208328, 25055188624847265543458274367950453300857118220869210090871111776889736317419, 85122017670846560196150971903572914719223441962636833158747832355263536391784, 56037888555592629882129012515370029971591015194623349562817465689171087235694, 90732769342136294547106188689659033468135068053309759484884430540402989923190, 8504650354199046967844283260470081700537855650540473789576420164098954313105, 78067476552214778212316364861870625849796097805694653216502443955879510467667, 88124790206602873738123959574768208661008404410244526735976597647074872077605, 108071269438911928073628117092641485918890078210673620541699646128201726967125, 41583625254788942753241977388698101172205988974195089700478168316982740446682, 103281190838638397263930533038676454144183409512650853712818844600462297147722, 67085855782932692934423622563139914002693105585430996644838094440650636622208, 50459044078714163659087366048142490546234660367999889859955605372403276045953, 57496196498153816313804252958487546956624645450959519486075375214967472114647, 83875177680346788190712555035408557718930577220885464689684965606900249299277, 30409554383292487475051916068758319422656378412413213786007508096465251699045, 103903530465470256178351666563535984034293925270624137237009138250435358771621, 70468266705471704683261360248703415287707650491429331480781191724990042436914, 95818980413853781743310202782396656506864682259839540147915227761764790417030, 60858399618221963565223934455893611639311803926327814242535114103157609628550, 45870747248983041763905016813694868941558546523805225428850540879128186160163] # Insert your full leak array here
ct = [169, 228, 197, 95, 226, 233, 228, 93, 31, 218, 159, 228, 42, 146, 109]   # Insert your full ct array here

# --- Step 1: Collect ALL Candidate LCG Pairs ---
# We generate a line between every pair of transitions. 
# This guarantees we capture every true LCG used at least twice.
candidate_lcgs = set()
for i in range(29):
    for j in range(i + 1, 29):
        x1, y1 = leak[i], leak[i+1]
        x2, y2 = leak[j], leak[j+1]
        if x1 == x2: 
            continue
        
        # Calculate the unique (a, b) line passing through these two transitions
        a = ((y1 - y2) * inverse(x1 - x2, p)) % p
        b = (y1 - a * x1) % p
        candidate_lcgs.add((a, b))

print(f"[*] Generated {len(candidate_lcgs)} candidate LCG pairs.")

# --- Step 2: Strict DFS + Wide Beam Search ---
prefix = b"BKISC{"
suffix = b"}"

# Beam state: (current_s, decrypted_flag_bytes)
# leak[-1] is the internal state `s` immediately before `ct` begins.
beam = [(leak[-1], b"")]

print("[*] Starting decryption...")
for i in range(len(ct)):
    next_beam = []
    for s, flag in beam:
        for a, b in candidate_lcgs:
            next_s = (a * s + b) % p
            char_val = (next_s & 0xFF) ^ ct[i]
            
            # 1. Strict Prefix Filtering (Destroys garbage paths instantly)
            if i < len(prefix):
                if char_val == prefix[i]:
                    next_beam.append((next_s, flag + bytes([char_val])))
            
            # 2. Strict Suffix Filtering
            elif i == len(ct) - 1:
                if char_val == suffix[0]:
                    next_beam.append((next_s, flag + bytes([char_val])))
            
            # 3. Printable ASCII Filtering for the body
            else:
                if 32 <= char_val <= 126:  # Standard printable ASCII range
                    next_beam.append((next_s, flag + bytes([char_val])))
    
    # If we are past the prefix, we need to sort and truncate to prevent exponential explosion
    if i >= len(prefix):
        # Stronger heuristic: heavily favor standard flag formats (alphanumeric + underscores)
        def score(item):
            f = item[1]
            s = 0
            for c in f:
                if chr(c).isalnum() or chr(c) in "_{}": s += 10
                elif chr(c) in "!?@#$%&*()": s += 2
                else: s -= 10 # Penalize weird printable characters like ~ or `
            return s
        
        next_beam.sort(key=score, reverse=True)
        beam = next_beam[:10000] # Expanded beam size to ensure true path survives
    else:
        beam = next_beam # Keep all exact prefix matches (usually only a handful survive)

    print(f"Step {i+1}/{len(ct)} - Beam size: {len(beam)}")

print("\n[*] Top Decrypted Flags:")
for _, flag in beam[:10]:
    # Final check to ensure it printed a complete flag
    if flag.endswith(b"}"):
        print(flag.decode(errors='ignore'))