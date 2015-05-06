#!/usr/bin/env 

import argparse
from collections import defaultdict
import datetime
import re
import itertools

"""
File to evaluate the quality of event predictions
"""
parser = argparse.ArgumentParser(description = "")
parser.add_argument('-i', action = 'store', required = True, help = "The file with identified events")
parser.add_argument('-p', action = 'store', required = True, help = "The predictions file")  
parser.add_argument('-o', action = 'store', required = True, help = "The directory to write outcomes to")
parser.add_argument('-y', action = 'store_true', help = "include only yearly patterns")
parser.add_argument('-d', action = 'store_true', help = "divide pattern types")
parser.add_argument('--std', action = 'store_true', help = "specify if predictions are made by std")

args = parser.parse_args()

eventsfile = open(args.i,"r",encoding="utf-8")
predictfile = open(args.p,"r",encoding="utf-8")

print("generating dicts")
#generate term_dates dict from file
term_dates = defaultdict(list)
if args.std:
    for line in eventsfile.readlines():
        if re.match(r"^\d+\.\d+",line):
            try:
                tokens = line.strip().split("\t")
                terms = tokens[1].split(", ")
                dates_raw = [x[:10] for x in tokens[2].split(" > ")]
                for date in dates_raw:
                    entries = date.split("-")
                    for term in terms:
                        term_dates[term].append(datetime.datetime(int(entries[0]),int(entries[1]),int(entries[2])))           
            except:
                continue
else:
    for line in eventsfile.readlines():
        if line[0] == "<":
            tokens = line.strip().split("\t")
            terms = tokens[1].split(", ")
            dates_raw = tokens[3].split(" > ")
            for date in dates_raw:
                entries = date.split("-")
                for term in terms:
                    term_dates[term].append(datetime.datetime(int(entries[0]),int(entries[1]),int(entries[2])))

#generate term_predictions dict from file
terms_predictions = defaultdict(list)
for line in predictfile.readlines():
    tokens = line.strip().split("\t")
    terms = "_".join(sorted(tokens[0].split(", ")))
    pattern = tokens[1]
    fields = tokens[2][1:-1].split(", ")
    if args.y and pattern[1] == "v":
        continue
    else:
        #print(pattern,pattern[1])
        predict_date = datetime.datetime(int(fields[5][-4:]),int(fields[6]),int(fields[7]))
        score = float(fields[11])
        if args.std:
            terms_predictions[terms].append((predict_date,pattern,score))
        else:
            coverage = float(fields[12])
            consistency = float(fields[13])
            terms_predictions[terms].append((predict_date,pattern,score,coverage,consistency))


#print(terms_predictions)

print("scoring predictions")
#match predictions with occurrences and list scores and accuracies
resultsfile = open(args.o + "results.txt","w",encoding = "utf-8")
#results9 = open(args.o + "results9.txt","w",encoding="utf-8")
scores_raw = open(args.o + "scores_raw.txt","w",encoding = "utf-8")
score_accuracies = []
coverage_accuracies = []
consistency_accuracies = []
print("assessment")
for term in terms_predictions.keys():
#    print(term,terms_predictions[term])
    predictions_sorted = sorted(terms_predictions[term],key = lambda x : x[0])
    if re.search("_",term):
        dates = []
        ts = term.split("_")
        for term in ts:
            dates.extend(term_dates[term])
    else:
        dates = term_dates[term]

        # i = len(ts) - 1
        # while i >= 2:
        #     for combination in itertools.combinations(ts,i):
        #         dates.extend(term_dates["_".join(sorted(combination))])
        #     i -= 1
        # for t in ts:
        #     dates.extend(term_dates[t])
    dates = list(set(dates))
    prediction = predictions_sorted[0]
    # for prediction in predictions:
    prdate = prediction[0]
    if prdate in dates:
        assessment = "Correct"
    else:
        assessment = "False"
    resultsfile.write("\t".join([term,prediction[1],str(prdate),assessment]) + "\n")
    #if prediction[2] >= 0.9:
    #    results9.write("\t".join([term,prediction[1],str(prdate),assessment]) + "\n")
    score_accuracies.append([term,prediction[2],assessment])
    if not args.std:
        coverage_accuracies.append([term,prediction[3],assessment])
        consistency_accuracies.append([term,prediction[4],assessment])
resultsfile.close()

def score_accuracy(data,sdev):
    outlist = []
    if sdev:
 #       print("sdev")
        thresh = 0
        while thresh <= 25:
            below_thresh = [x for x in data if x[1] <= thresh]
    #        if thresh == 1.0 and pr:
    #            print(above_thresh)
#            print(thresh,below_thresh)
            accuracy = len([s for s in below_thresh if s[2] == "Correct"]) / len(below_thresh)
            outlist.append([str(thresh),str(accuracy)])
            thresh += 0.1           
    else:
        thresh = 1.0
        while thresh >= 0:
            above_thresh = [x for x in data if x[1] >= thresh]
    #        if thresh == 1.0 and pr:
    #            print(above_thresh)
            accuracy = len([s for s in above_thresh if s[2] == "Correct"]) / len(above_thresh)
            outlist.append([str(thresh),str(accuracy)])
            thresh -= 0.01
    return outlist

def rank_accuracy(data,sdev):
    outlist = []
    if sdev:
        ranked_data = sorted(data,key = lambda k : k[1])
    else:
        ranked_data = sorted(data,key = lambda k : k[1],reverse = True)
    for r in range(50,len(ranked_data),50):
        accuracy = len([s for s in ranked_data[:r] if s[2] == "Correct"]) / len(ranked_data[:r])
        outlist.append([str(r),str(accuracy)])
    return outlist

print("accuracy plots")
print("score")
accuracies_score = score_accuracy(score_accuracies,args.std)
for accuracy in accuracies_score:
    scores_raw.write(" ".join(accuracy) + "\n")
scores_raw.close()

print("rank")
ranked_file = open(args.o + "accuracy_by_rank.txt","w",encoding = "utf-8")
accuracies_rank = rank_accuracy(score_accuracies,args.std)
for rank in accuracies_rank:
    ranked_file.write(" ".join(rank) + "\n")
ranked_file.close()

if not args.std:
    coverage_raw = open(args.o + "coverage_raw.txt","w",encoding = "utf-8")
    consistency_raw = open(args.o + "consistency_raw.txt","w",encoding = "utf-8")
    print("coverage")
    accuracies_coverage = score_accuracy(coverage_accuracies,sdev=False)
    print("consistency")
    accuracies_consistency = score_accuracy(consistency_accuracies,sdev=False)

    for accuracy in accuracies_coverage:
        coverage_raw.write(" ".join(accuracy) + "\n")
    coverage_raw.close()

    for accuracy in accuracies_consistency:
        consistency_raw.write(" ".join(accuracy) + "\n")
    consistency_raw.close()
