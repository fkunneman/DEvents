#!/usr/bin/env 

import argparse
import frog

"""
Program to enrich eventlines with lemmas
"""
parser = argparse.ArgumentParser(description = 
    "Program to enrich eventlines with lemmas")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
parser.add_argument('-o', action = 'store', required = True, help = "The output file")
args = parser.parse_args()

frogger = frog.Frog(frog.FrogOptions(),"/vol/customopt/uvt-ru/etc/frog/frog-twitter.cfg")

#load in events
print("reading in events")
infile = open(args.i,"r",encoding = "utf-8")
eventlines = infile.readlines()
infile.close()
numlines = len(eventlines)
outfile = open(args.o,"a",encoding = "utf-8")
for i,line in enumerate(eventlines):
    print(i,"of",numlines)
    tokens = line.strip().split("\t")
    entities = tokens[2].split(", ")
    entityls = []
    for entity in entities:
        data = frogger.process(entity)
        for token in data:
            entityls.append(token["lemma"])
    tokens.append(", ".join(entityls))
    outfile.write("\t".join(tokens) + "\n")
