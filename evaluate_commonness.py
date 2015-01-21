
from __future__ import division
import sys
import codecs
import re
from collections import defaultdict

standardfile = codecs.open(sys.argv[1],"r","utf-8")
commonnessfile = codecs.open(sys.argv[2],"r","utf-8")
frogfile = codecs.open(sys.argv[3],"r","utf-8")
outfile_stats = open(sys.argv[4],"w")
outfile_commonness_fp = codecs.open(sys.argv[5],"w","utf-8")
outfile_commonness_fn = codecs.open(sys.argv[6],"w","utf-8")
outfile_frog_fp = codecs.open(sys.argv[7],"w",'utf-8')
outfile_frog_fn = codecs.open(sys.argv[8],"w","utf-8")

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
tpcl = 0
fpcl = 0
fncl = 0
tpfl = 0
fpfl = 0
fnfl = 0

for key in match.keys():
    lists = match[key]
    print key,lists
    if len(lists) != 3:
        print key,len(lists)
    tpc += len([x for x in lists[1] if x in lists[0]])
    fpc += len([x for x in lists[1] if x not in lists[0]])
    fnc += len([x for x in lists[0] if x not in lists[1]])
    tpf += len([x for x in lists[2] if x in lists[0]])
    fpf += len([x for x in lists[2] if x not in lists[0]])
    fnf += len([x for x in lists[0] if x not in lists[2]])
    reflist = lists[0][:]
    for x in lists[1]:
        tp = False
        for r in reflist:
            if re.search(x.replace("(","\(").replace(")","\)").replace("*","\*"),r.replace("(","\(").replace(")","\)").replace("*","\*")) or re.search(r.replace("(","\(").replace(")","\)").replace("*","\*"),x.replace("(","\(").replace(")","\)").replace("*","\*")):
                tp = True
        if tp:
            tpcl += 1
        else:
            fpcl += 1
            outfile_commonness_fp.write(x + "\n")
    for r in reflist:
        tp = False
        for x in lists[1]:
            if re.search(x.replace("(","\(").replace(")","\)").replace("*","\*"),r.replace("(","\(").replace(")","\)").replace("*","\*")) or re.search(r.replace("(","\(").replace(")","\)").replace("*","\*"),x.replace("(","\(").replace(")","\)").replace("*","\*")):
                tp = True
        if not tp:
            fncl += 1
            outfile_commonness_fn.write(r + "\n")
    for x in lists[2]:
        tp = False
        for r in reflist:
            print r,x
            if re.search(x.replace("(","\(").replace(")","\)").replace("*","\*"),r.replace("(","\(").replace(")","\)").replace("*","\*")) or re.search(r.replace("(","\(").replace(")","\)").replace("*","\*"),x.replace("(","\(").replace(")","\)").replace("*","\*")):
                tp = True
        if tp:
            tpfl += 1
        else:
            fpfl += 1
            outfile_frog_fp.write(x+"\n")
    for r in reflist:
        tp = False
        for x in lists[2]:
            if re.search(x.replace("(","\(").replace(")","\)").replace("*","\*"),r.replace("(","\(").replace(")","\)").replace("*","\*")) or re.search(r.replace("(","\(").replace(")","\)").replace("*","\*"),x.replace("(","\(").replace(")","\)").replace("*","\*")):
                tp = True
        if not tp:
            fnfl += 1
            outfile_frog_fn.write(r + "\n")

    print lists,"tpc",tpc,"fpc",fpc,"fnc",fnc,"tpf",tpf,"fpf",fpf,"fnf",fnf,"tpcl",tpcl,"fpcl",fpcl,"fncl",fncl,"tpfl",tpfl,"fpfl",fpfl,"fnfl",fnfl

precisionc = tpc / (tpc+fpc)
recallc = tpc / (tpc+fnc)
f1c = 2 * ((precisionc*recallc) / (precisionc+recallc))
precisionf = tpf / (tpf+fpf)
recallf = tpf / (tpf+fnf)
f1f = 2 * ((precisionf*recallf) / (precisionf+recallf))
precisioncl = tpcl / (tpcl+fpcl)
recallcl = tpcl / (tpcl+fncl)
f1cl = 2 * ((precisioncl*recallcl) / (precisioncl+recallcl))
precisionfl = tpfl / (tpfl+fpfl)
recallfl = tpfl / (tpfl+fnfl)
f1fl = 2 * ((precisionfl*recallfl) / (precisionfl+recallfl))


outfile_stats.write("commonness: precision - " + str(precisionc) + ",recall - " + str(recallc) + ",f1 - " + str(f1c) + "\nfrog: precision - " + str(precisionf) + ",recall - " + str(recallf) + ",f1 - " + str(f1f) +"\ncommonness lax: precision - " + str(precisioncl) + ",recall - " + str(recallcl) + ",f1 - " + str(f1cl) + "\nfrog lax: precision - " + str(precisionfl) + ",recall - " + str(recallfl) + ",f1 - " + str(f1fl) + "\n")
#print len(match.keys()),[x for x in match.values() if len(x) < 2]

