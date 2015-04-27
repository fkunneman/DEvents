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
parser.add_argument('-o', action = 'store', required = True, help = "The directory to write outcomes to")

args = parser.parse_args()

eventsfile = open(args.i,"r",encoding="utf-8")
predictfile = open(args.p,"r",encoding="utf-8")

print("generating dicts")
#generate term_dates dict from file
term_dates = defaultdict(list)
for line in eventsfile.readlines():
    if line[0] == "<":
        tokens = line.strip().split("\t")
        terms = "_".join(sorted(tokens[1].split(", ")))
        dates_raw = tokens[3].split(" > ")
        for date in dates_raw:
            entries = date.split("-")
            term_dates[terms].append(datetime.datetime(int(entries[0]),int(entries[1]),int(entries[2])))
        term_dates[terms] = list(set(term_dates[terms]))

#generate term_predictions dict from file
terms_predictions = defaultdict(list)
for line in predictfile.readlines():
    tokens = line.strip().split("\t")
    terms = "_".join(sorted(tokens[0].split(", ")))
    pattern = tokens[1]
    fields = tokens[2][1:-1].split(", ")
    predict_date = datetime.datetime(int(fields[5][-4:]),int(fields[6]),int(fields[7]))
    score = float(fields[11])
    coverage = float(fields[12])
    consistency = float(fields[13])
    terms_predictions[terms].append((predict_date,pattern,score,coverage,consistency))

print("scoring predictions")
#match predictions with occurrences and list scores and accuracies
resultsfile = open(args.o + "results.txt","w",encoding = "utf-8")
scores_raw = open(args.o + "scores_raw.txt","w",encoding = "utf-8")
coverage_raw = open(args.o + "coverage_raw.txt","w",encoding = "utf-8")
consistency_raw = open(args.o + "consistency_raw.txt","w",encoding = "utf-8")
score_accuracies = []
coverage_accuracies = []
consistency_accuracies = []
print("assessment")
for term in terms_predictions.keys():
    predictions = terms_predictions[term]
    dates = term_dates[term]
    for prediction in predictions:
        prdate = prediction[0]
        if prdate in dates:
            assessment = "Correct"
        else:
            assessment = "False"
        resultsfile.write("\t".join([term,prediction[1],str(prdate),assessment]))
        score_accuracies.append([term,prediction[2],assessment])
        coverage_accuracies.append([term,prediction[3],assessment])
        consistency_accuracies.append([term,prediction[4],assessment])
resultsfile.close()

def score_accuracy(data):
    outlist = []
    thresh = 1.0
    while thresh >= 0:
        above_thresh = [x for x in data if x[1] >= thresh]
        accuracy = len([s for s in above_thresh if s[2] == "Correct"]) / len(above_thresh)
        outlist.append([str(thresh),str(accuracy)])
        thresh -= 0.1
    return outlist

print("accuracy plots"))
accuracies_score = score_accuracy(score_accuracies)
accuracies_coverage = score_accuracy(coverage_accuracies)
accuracies_consistency = score_accuracy(consistency_accuracies)

for accuracy in accuracies_score:
    scores_raw.write(" ".join(accuracy) + "\n")
scores_raw.close()

for accuracy in accuracies_coverage:
    coverage_raw.write(" ".join(accuracy) + "\n")
coverage_raw.close()

for accuracy in accuracies_consistency:
    concistency_raw.write(" ".join(accuracy) + "\n")
consistency_raw.close()
    



