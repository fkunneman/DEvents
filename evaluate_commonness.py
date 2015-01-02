
import sys
import codecs
from collections import defaultdict

standardfile = codecs.open(sys.argv[1],"r","utf-8")
commonnessfile = codecs.open(sys.argv[2],"r","utf-8")

match = defaultdict(list)

#link entities to ids
#standard
for line in standardfile.readlines():
    tokens = line.strip().split("\t")
    tid = tokens[0]
    entities = tokens[2].split()
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
        if entities[0] == "--":
            entities = []
        match[tid].append(entities)

print match
print len(match.keys()),[x for x in match.values() if len(x) < 2]

