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

cityfile = open(args.cities,"r",encoding="utf-8")
cities = [x.lower() for x in cityfile.read().split("\n")]

infile = open(args.i,"r",encoding="utf-8")
lines = infile.readlines()
print("begin:",len(lines),"lines")
outfile = open(args.o,"w",encoding="utf-8")
newlines = 0
for line in lines:
    tokens = line.strip().split("\t")
    terms = tokens[2].split(",")
    keep = False
    for term in terms:
        if not (keep and (timex.match(term) or term in cities)):
            outfile.write(line)
            keep = True
            newlines += 1

infile.close()
outfile.close()
print("Done:",nelines,"lines")