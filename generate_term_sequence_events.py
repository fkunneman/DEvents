#!/usr/bin/env 

import argparse
from collections import defaultdict
import ucto

"""
Program to extract term-event dates from an events file
"""
parser = argparse.ArgumentParser(description = "Program to extract term-event dates from an events file")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
parser.add_argument('-o', action = 'store', required = True, help = "The output file")
parser.add_argument('-t', action = 'store', required = True, choices = ["term","tweets"],
    help = "the type of extraction: from terms or tweets")
args = parser.parse_args() 

term_dates = defaultdict(list)
if args.t == "tweets":
    ucto_settingsfile = "/vol/customopt/uvt-ru/etc/ucto/tokconfig-nl-twitter"
    tokenizer = ucto.Tokenizer(ucto_settingsfile)
#for each line
infile = open(args.i,"r",encoding="utf-8")
lines = infile.readlines()
infile.close()
nlines = len(lines)
for i,line in enumerate(lines):
    print(i,"of",nlines,"lines")
    tokens = line.strip().split("\t")
    date = tokens[0]
    if args.t == "term":
        terms = tokens[2].split(", ")
    else:
        for tweet in tokens[4].split("-----"):
            tokenizer.process(tweet)
            terms = [x.text.lower() for x in tokenizer]
    for term in terms:
        term_dates[term].append((date,i))

outfile = open(args.o,"w",encoding="utf-8")
#link date and term
for term in sorted(term_dates.keys()):
    dates_index = term_dates[term]
    outfile.write(term + "\t" + "|".join([",".join([str(y) for y in x]) for x in dates_index]) + "\n")
outfile.close()



