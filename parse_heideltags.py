
import sys
import codecs
import re

infile = codecs.open(sys.argv[1],"r","utf-8")
#outfile = codecs.open(sys.argv[2],"a","utf-8")

lines = infile.readlines()
infile.close()

for i,line in enumerate(lines):
    if re.match(r"^#tweet_id",line):
        start = i + 1
        break

for line in lines[start:]:
    if re.search("<",line) and re.search(">",line):
        tokens = line.strip().split("\t")
        tweet_id = tokens[0]
        text = tokens[1]
        textparts = text.split("<")
        timetags = [x.split(">")[0] for x in textparts]
        print timetags

