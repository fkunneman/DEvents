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
    infile = open(filename,"r",encoding = "utf-8")
    for line in infile.readlines()[1:]:
        tokens = line.split("\t")
        terms = tokens[args.ta].split(", ")
        assessment = tokens[args.sa]
        outputA[i].append([terms,assessment])

#read in files of output B
outputB = [] #list of lists
for i,filename in enumerate(args.b):
    outputB.append([])
    infile = open(filename,"r",encoding = "utf-8")
    for line in infile.readlines()[1:]:
        tokens = line.split("\t")
        terms = tokens[args.tb].split(", ")
        assessment = tokens[args.sb]
        outputB[i].append([terms,assessment])

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
termsA = []
for entry in assessmentA:
    if entry[1] == "1.0":
        positiveA += 1
        termsA.extend(entry[0])
        all_terms.extend(entry[0])
precisionA = positiveA / len(assessmentA)

#count positive assessments B
positiveB = 0
termsB = []
for entry in assessmentB:
    if entry[1] == "1.0":
        positiveB += 1
        termsB.extend(entry[0])
        all_terms.extend(entry[0])
precisionB = positiveB / len(assessmentB)

all_terms = list(set(all_terms))
recallA = len(termsA) / len(all_terms)
fscoreA = 2*((precisionA*recallA)/(precisionA+recallA))
outfile.write("\nresults A\nPrecision: " + str(precisionA) + "\nRecall: " + str(recallA) + 
    "\nF1: " + str(fscoreA) + "\n\n")

recallB = len(termsB) / len(all_terms)
fscoreB = 2*((precisionB*recallB)/(precisionB+recallB))
outfile.write("\nresults B\nPrecision: " + str(precisionB) + "\nRecall: " + str(recallB) + 
    "\nF1: " + str(fscoreB) + "\n\n")

intersect = len(list(set(termsA) & set(termsB))) / len(all_terms)
A = sorted(list(set(termsA) - set(termsB)))
As = len(A) / len(all_terms)
B = sorted(list(set(termsB) - set(termsA)))
Bs = len(B) / len(all_terms)
outfile.write("intersect: " + str(intersect) + " " + str(len(list(set(termsA) & set(termsB)))) + "\nunique A: " + str(As) + " " + str(len(termsA)) +  
    "\nunique B: " + str(Bs) + " " + str(len(list(set(termsB)))) + "\n\n\nterms A:\n" + "\n".join(A) + 
    "\n\n\nterms B:\n" + "\n".join(B))
