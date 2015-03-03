#!/usr/bin/env 

import argparse
import re

"""
Type description here
"""
parser = argparse.ArgumentParser(description = "")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
parser.add_argument('-o', action = 'store', required = True, help = "The output file")
parser.add_argument('--cities', action = 'store', required = True, 
    help = "file with cities to check")
args = parser.parse_args()

months = (r"(jan|januari|feb|februari|mrt|maart|apr|april|mei|jun|juni|jul|juli|aug|augustus|"
    "sep|september|okt|oktober|nov|november|dec|december)")
timex = re.compile(r"\d+ (jan|januari|feb|februari|mrt|maart|apr|april|mei|jun|juni|jul|juli|aug|augustus|"
    "sep|september|okt|oktober|nov|november|dec|december)")
hasht = re.compile(r"#\d+(jan|januari|feb|februari|mrt|maart|apr|april|mei|jun|juni|jul|juli|aug|augustus|"
    "sep|september|okt|oktober|nov|november|dec|december)")

cityfile = open(args.cities,"r",encoding="utf-8")
cities = [x.strip().lower() for x in cityfile.read().split("\n")]
#print(cities)

infile = open(args.i,"r",encoding="utf-8")
lines = infile.readlines()
print("begin:",len(lines),"lines")
outfile = open(args.o,"w",encoding="utf-8")
newlines = 0
for line in lines:
    tokens = line.split("\t")
    terms = tokens[2].split(", ")
    keep = False
    new_terms = []
    for term in terms:
        if timex.match(term) or hasht.match(term):
            continue
        else:
            new_terms.append(term)
#            if not keep:
#            	print(term)
            if not term in cities:
 #               if not keep:
 #                   print("True")
                keep = True
  #              print(keep)
   #         else:
   #             if not keep:
   #                 print("stays False")
    if keep:
        tokens[2] = ", ".join(new_terms)
        outfile.write("\t".join(tokens))
        newlines += 1

infile.close()
outfile.close()
print("Done:",newlines,"lines")
