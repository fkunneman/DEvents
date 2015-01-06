
from __future__ import division
import sys
import codecs
import re
from collections import defaultdict

standardfile = codecs.open(sys.argv[1],"r","utf-8")
commonnessfile = codecs.open(sys.argv[2],"r","utf-8")
frogfile = codecs.open(sys.argv[3],"r","utf-8")

match = defaultdict(list)

#link entities to ids
#standard
for line in standardfile.readlines():
    tokens = line.strip().split("\t")
    tid = tokens[0]
    entities = tokens[2].split(",")
    if entities[0] == "x":
        entities = []
    match[tid].append(entities)
standardkeys = match.keys()

#commonness
for line in commonnessfile.readlines():
    tokens = line.strip().split("\t")
    tid = tokens[0]
    if tid in standardkeys:
        entities = tokens[6].split(" | ")
        entities = [x for x in entities if not re.search(r"^#",x)]
        if len(entities) > 0:
            if entities[0] == "--":
                entities = []    
        match[tid].append(entities)

#frog
for line in frogfile.readlines():
    tokens = line.strip().split("\t")
    tid = tokens[1]
    if tid in standardkeys:
        entities = tokens[8].split(" | ")
        entities = [x.replace("_"," ").lower() for x in entities if not re.search(r"^#",x)]
        if len(entities) > 0:
            if entities[0] == "x":
                entities = []    
        match[tid].append(entities)

tpc = 0
fpc = 0
fnc = 0
tpf = 0
fpf = 0
fnf = 0

for key in match.keys():
    lists = match[key]
    print key
    if len(lists) != 3:
        print key,len(lists)
    tpc += len([x for x in lists[1] if x in lists[0]])
    fpc += len([x for x in lists[1] if x not in lists[0]])
    fnc += len([x for x in lists[0] if x not in lists[1]])
    tpf += len([x for x in lists[2] if x in lists[0]])
    fpf += len([x for x in lists[2] if x not in lists[0]])
    fnf += len([x for x in lists[0] if x not in lists[2]])
    print lists,"tp",tpf,"fp",fpf,"fn",fnf

precisionc = tpc / (tpc+fpc)
recallc = tpc / (tpc+fnc)
f1c = 2 * ((precisionc*recallc) / (precisionc+recallc))
precisionf = tpf / (tpf+fpf)
recallf = tpf / (tpf+fnf)
f1f = 2 * ((precisionf*recallf) / (precisionf+recallf))

print "commonness: precision",precisionc,"recall",recallc,"f1",f1c
print "frog: precision",precisionf,"recall",recallf,"f1",f1f
#print len(match.keys()),[x for x in match.values() if len(x) < 2]

