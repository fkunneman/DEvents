#!/usr/bin/env 

import argparse
from collections import defaultdict
import datetime

"""
File to evaluate the quality of event predictions
"""
parser = argparse.ArgumentParser(description = "")
parser.add_argument('-i', action = 'store', required = True, help = "The file with identified events")
parser.add_argument('-p', action = 'store', required = True, help = "The predictions file")  
parser.add_argument('-o', action = 'store', required = True, help = "The file with results")
parser.add_argument('-r', action = 'store', required = False, help = "The raw file for plotting")

args = parser.parse_args()

eventsfile = open(args.i,"r",encoding="utf-8") 
predictfile = open(args.p,"r",encoding="utf-8")

#generate term_predictions dict from file
terms_predictions = defaultdict(list)
for line in predictfile.readlines():
    tokens = line.strip().split("\t")
    terms = "_".join(sorted(tokens[0].split(", ")))
    fields = tokens[2][1:-1].split(", ")
    predict_date = datetime.datetime(int(fields[5][-4:]),int(fields[6]),int(fields[7]))
    score = float(fields[11])
    coverage = float(fields[12])
    consistency = float(fields[13])
    terms_predictions[terms].append((predict_date,score,coverage,consistency))

print(terms_predictions)
