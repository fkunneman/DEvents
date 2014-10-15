
import re
import codecs
import sys
import random
from collections import defaultdict

outdir = sys.argv[1]
ngramf = sys.argv[2]
csf = sys.argv[3]
csxf = sys.argv[4]

twothird = 13*[14] + 4*[17]
onethird = 14*[16] + 2*[13]
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

def parse_outputfile(filename):
    outputfile = codecs.open(filename,"r","utf-8")
    units = []
    unit = ""
    for line in outputfile.readlines():
        print line
        unit += line
        if re.search("Slecht",line):
            units.append(unit)
            unit = ""
    return units[:250]

#generate index lists
asets = generate_indexlist(20,twothird)
asets += generate_indexlist(10,onethird)

#parse outputfiles
ngram = parse_outputfile(ngramf)
cs = parse_outputfile(csf)
csx = parse_outputfile(csxf)

print ngram,cs,csx

#extract events per annotator
for i in range(30):
    outfile = codecs.open(outdir + "annotator_" + str(i) + ".txt","w","utf-8")
    indexfile = codecs.open(outdir + "indexes_annotator_" + str(i) + ".txt","w","utf-8")
    outfile.write("[[AdvancedFormat]]\n\n[[Block:MC Block]]\n\n")
    j = i
    print i,"index",j
    indexes = range(50)
    index_event = {}
    ngrami = asets[j]
    print ngrami
    print ngram
    for h in range(len(ngrami)):
        print h
        index_event[h] = ("ngram",ngrami[h],ngram[ngrami[h]])
    j += 10
    if j >= 30:
        j = j - 30
    print i,"index",j
    csi = asets[j]
    for k,h in enumerate(range(len(index_event.keys()),len(ngrami) + len(csi))):
        index_event[h] = ("cs",csi[k],cs[csi[k]])
    j += 10
    if j >= 30:
        j = j - 30
    print i,"index",j
    csxi = asets[j]
    for k,h in enumerate(range(len(index_event.keys()),len(ngrami) + len(csi) + len(csxi))):
        index_event[h] = ("csx",csxi[k],csx[csxi[k]])
    print len(index_event.keys()),len(ngrami),len(csi),len(csxi)
    random.shuffle(indexes)
    for index in indexes:
        print index
        outfile.write(index_event[index][2] + "\n[[PageBreak]]\n")
        indexfile.write(str(index_event[index][0]) + " " + str(index_event[index][1]) + "\n")
    outfile.close()
    indexfile.close()

     
