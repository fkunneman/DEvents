
from __future__ import division
import sys
import codecs
import re
from collections import defaultdict

standardfile = codecs.open(sys.argv[1],"r","utf-8")
commonnessfile = codecs.open(sys.argv[2],"r","utf-8")
frogfile = codecs.open(sys.argv[3],"r","utf-8")
goldout = codecs.open(sys.argv[4],"w","utf-8")
csout = codecs.open(sys.argv[5],"w","utf-8")
frogout = codecs.open(sys.argv[6],"w","utf-8")

match = defaultdict(list)

#link entities to ids
#standard
for line in standardfile.readlines():
    tokens = line.strip().split("\t")
    tid = tokens[0]
    text = tokens[1].lower()
    match[tid].append(text)
    entities = tokens[2].lower().split(",")
    if entities[0] == "x":
        entities = []
    match[tid].append(entities)
standardkeys = match.keys()

#commonness
for line in commonnessfile.readlines():
    tokens = line.strip().split("\t")
    tid = tokens[0]
    if tid in standardkeys:
        entities = tokens[6].lower().split(" | ")
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
        entities = tokens[8].lower().split(" | ")
        entities = [x.replace("_"," ").lower() for x in entities if not re.search(r"^#",x)]
        if len(entities) > 0:
            for e in entities:
                if re.search("resultaat=inspiratie",e):
                    print line
            if entities[0] == "x":
                entities = []    
        match[tid].append(entities)

methods = [goldout,csout,frogout]
for key in match.keys():
    lists = match[key]
    print key,lists
    if len(lists) != 4:
        print key,len(lists)
    text = lists[0]
    iob_stand = []
    iob_index = defaultdict(list)
    for i,token in enumerate(text.split()):
        iob_stand.append([token,"O"])
        if token in iob_index.keys():
            iob_index[token].append(text.split()[(iob_index[token][-1]+1):].index(token))
        else:
            iob_index[token].append(i)
    for i,m in enumerate(lists[1:]):
        iob = iob_stand
        past = {}
        for x in iob_index.keys():
            past[x] = 0
        if len(m) > 0:
            for entity in m:
                parts = entity.split()
                try:
                    ti = iob_index[parts[0]][past[parts[0]]]
                    past[parts[0]] += 1
                    iob[ti][1] = "B-ORG"
                    for p in parts[1:]:
                        ti = iob_index[p][past[p]]
                        past[p] += 1
                        iob[ti][1] = "I-ORG"
                except:
                    try:
                        ti = iob_index["_".join(parts)][past["_".join(parts)]]
                        past["_".join(parts)] += 1
                        iob[ti][1] = "B-ORG"
                    except:
                        try:
                            ti = iob_index[parts[0]][past[parts[0]]-1]
                            iob[ti][1] = "B-ORG"
                            for p in parts[1:]:
                                ti = iob_index[p][past[p]-1]
                                iob[ti][1] = "I-ORG"
                        except:
                            continue
        print([" ".join(t) for t in iob])
        methods[i].write("\n".join([" ".join(t) for t in iob]) + "\n\n")

goldout.close()
csout.close()
frogout.close()



