
import random
from collections import defaultdict

twothird = 19*[8] + 14*[7]
onethird = 12*[8] + 22*[7]
filled = []
counts = defaultdict(int)
asets = []

def generate_indexlist(r,s):
    asets_f =[]
    for i in range(r):
        index = 0
        aset = []
        for j,e in enumerate(s):
            es = range(index,index+e)
            es_clean = []
            es_clean = [v for v in es if v not in (set(es) & set(filled))]
            if len(es_clean) == 0:
                rc = random.choice([v for v in range(250) if v not in (set(range(250)) & set(filled))])
            else:
                rc = random.choice(es_clean)
            aset.append(rc)
            counts[rc] += 1
            if counts[rc] == 2:
                filled.append(rc)
            index += e
        asets_f.append(aset)
    return asets_f

asets = generate_indexlist(10,twothird)
asets += generate_indexlist(5,onethird)

#process 
