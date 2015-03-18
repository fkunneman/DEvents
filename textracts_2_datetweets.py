#!/usr/bin/env 

import sys
import re

infile = open(sys.argv[1],encoding="utf-8")
lines = infile.readlines()
infile.close()
outdir = sys.argv[2]
outfile = open(outdir + sys.argv[1].split("/")[-1],"w",encoding = "utf-8")

false_date = re.compile(r"(#?\d+(jan|januari|feb|februari|mrt|maart|apr|april|mei|jun|juni|jul|juli|aug|augustus|sep|september|okt|oktober|nov|november|dec|december))( |$)")
url = re.compile(r"^http")

#for every line
for line in lines:
    tokens = line.strip().split("\t")
    new_chunks = []
    for chunk in tokens[11].split(" \| "):
        #remove punctuation
        chunk = re.sub(r"(!|\"|#|\$|%|&|\'|\(|\)|\*|\+|,|-|\.|/|:|;|<|=|>|\?|\[|\\|]|\^|_|`|{|\||}|~)+( |$)",r"\2",chunk)
        chunk = re.sub(r"(^| )(!|\"|#|\$|%|&|\'|\(|\)|\*|\+|,|-|\.|/|:|;|<|=|>|\?|\[|\\|]|\^|_|`|{|\||}|~)+",r"\1",chunk)
        #remove false date
        if re.search(false_date,chunk):
            pats = [pat[0] for pat in re.findall(false_date,chunk)]
            regexPattern = '|'.join(map(re.escape, pats))
            chunks = re.split(regexPattern,chunk)
        else:
            chunks = [chunk]
        #remove users, urls
        for chunk in chunks:
            pats = []
            for token in chunk.split(" "):
                if token[0] == '@' or url.search(token):
                    pats.append(token)
            if len(pats) > 0:
                regexPattern = '|'.join(map(re.escape, pats))
                new_chunks.extend([x.strip() for x in re.split(regexPattern,chunk)])
            else:
                new_chunks.append(chunk)
    for chunk in new_chunks:
        print(chunk)
#        outfile.write(chunk + "\n")






