#!/usr/bin/env 

import argparse

"""
Program to evaluate the output of two systems, possibly with multiple annotations, and return a 
precision and recall based on them
"""
parser = argparse.ArgumentParser(description = "Program to evaluate the output of two systems, " +
    "possibly with multiple annotations")
parser.add_argument('-a', action = 'store', required = True, nargs = '+', 
    help = "The input file(s) of output A")
parser.add_argument('--ta', action='store', type = int, required = True, 
    help = "The column of the terms in output files A")
parser.add_argument('--sa', action='store', type = int, required = True, 
    help = "The column of the annotation in output files A")
parser.add_argument('-b', action = 'store', required = True, nargs = '+', 
    help = "The input file(s) of output B")
parser.add_argument('--tb', action='store', type = int, required = True, 
    help = "The column of the terms in output files B")
parser.add_argument('--sb', action='store', type = int, required = True, 
    help = "The column of the annotation in output files B")
parser.add_argument('-o', action = 'store', required = True, 
    help = "The output file")
args = parser.parse_args() 

all_terms = []
outfile = open(args.o,"w",encoding="utf-8")

#read in files of output A
outputA = [] #list of lists
for i,filename in enumerate(args.a):
    outputA.append([])
    infile = open(filename,"r","utf-8")
    for line in infile.readlines():
        tokens = line.split("\t")
        terms = tokens[args.ta].split(",")
        assessment = tokens[args.sa]
        outputA[i].append([terms,assessment])
        all_terms.extend(terms)

#read in files of output B
outputB = [] #list of lists
for i,filename in enumerate(args.b):
    outputb.append([])
    infile = open(filename,"r","utf-8")
    for line in infile.readlines():
        tokens = line.split("\t")
        terms = tokens[args.tb].split(",")
        assessment = tokens[args.sb]
        outputB[i].append([terms,assessment])
        all_terms.extend(terms)

all_terms = list(set(all_terms))

if len(outputA) > 1: #measure interannotator agreement
    print("calculating agreement for Output A")
else:
    assessmentA = outputA[0]

if len(outputB) > 1: #measure interannotator agreement
    print("calculating agreement for Output B")
else:
    assessmentB = outputB[0]

#calculate results
#count positive assessments A
positiveA = 0
termsA = 0
for entry in assessmentA:
    if entry[1] == "1.0":
        positiveA += 1
        termsA += len(entry[0])
precision = positiveA / len(assessmentA)
recall = termsA / len(all_terms)
fscore = 2*((precision*recall)/(precision+recall))
outfile.write("\nresults A\nPrecision: " + str(precision) + "\nRecall: " + str(recall) + 
    "\nF1: " + str(fscore) + "\n\n")

#count positive assessments B
positiveB = 0
termsB = 0
for entry in assessmentB:
    if entry[1] == "1.0":
        positiveB += 1
        termsB += len(entry[0])
precision = positiveB / len(assessmentB)
recall = termsB / len(all_terms)
fscore = 2*((precision*recall)/(precision+recall))
outfile.write("\nresults B\nPrecision: " + str(precision) + "\nRecall: " + str(recall) + 
    "\nF1: " + str(fscore) + "\n\n")
