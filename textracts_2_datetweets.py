#!/usr/bin/env 

import sys
import re

outdir = sys.argv[1]

false_date = re.compile(r"(#?\d+(jan|januari|feb|februari|mrt|maart|apr|april|mei|jun|juni|jul|juli|aug|augustus|sep|september|okt|oktober|nov|november|dec|december))( |$)")
url = re.compile(r"^http")

for filename in sys.argv[2:]:
    print(filename)
    infile = open(filename,encoding="utf-8")
    lines = infile.readlines()
    infile.close()
    outfile = open(outdir + filename.split("/")[-1],"w",encoding = "utf-8")
    #for every line
    for line in lines:
        tokens = line.strip().split("\t")
        if len(tokens) >= 12:
            new_chunks = []
            try:
                for chunk in tokens[12].split("|"):
                    #remove punctuation
                    chunk = chunk.strip().replace("  "," ")
                    chunk = re.sub(r"( )(!|\"|#|\$|%|&|\'|\(|\)|\*|\+|,|-|\.|/|:|;|<|=|>|\?|\[|\\|]|\^|_|`|{|\||}|~)+( )",r" ",chunk)
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
                            if len(token) > 0:
                                if token[0] == '@' or url.search(token):
                                    pats.append(token)
                        if len(pats) > 0:
                            regexPattern = '|'.join(map(re.escape, pats))
                            new_chunks.extend([x.strip() for x in re.split(regexPattern,chunk)])
                        else:
                            new_chunks.append(chunk)
                for chunk in new_chunks:
                    if len(chunk) > 0:
                        outfile.write(chunk.strip() + "\n")
            except IndexError:
                continue
    outfile.close()

