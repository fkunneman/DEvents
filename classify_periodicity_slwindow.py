#!/usr/bin/env 

import argparse
from collections import defaultdict
import ucto

import calculations
import time_functions

"""
Program to extract term-event dates from an events file
"""
parser = argparse.ArgumentParser(description = "Program to extract term-event dates from an events file")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
parser.add_argument('-o', action = 'store', required = True, help = "The output directory")
args = parser.parse_args() 

date_periodics = defaultdict(list)
date_terms = defaultdict(list)
term_dates = defaultdict(list)
term_events = defaultdict(list)

#for each line
infile = open(args.i,"r",encoding="utf-8")
lines = infile.readlines()
infile.close()
for i,line in enumerate(lines):
    date = time_functions.return_datetime(tokens[0],setting="vs")
    date_terms[date].extend(tokens[2].split(", "))
    for term in tokens[2].split(", "):
        term_events[term].append(line.strip())
        term_dates[term].append(date)

for current_date in sorted(date_terms.keys())[:2]:
    print(current_date)
    for term in date_term[current_date]:
        history = [date for date in term_dates[term] if date < current_date] 
        intervals = calculations.return_intervals(history + current_date)
        if len(intervals) >= 2:
            scores = []
            for i in range(len(intervals[:-2])):
                sequence = intervals[i:]
                scores.append([i,calculations.return_relative_stdev(sequence)])
            best = sorted(scores,key = lambda x : x[0])[0]
            date_periodics[current_date].append([term,best[1],intervals,history[best[0]:]])

all_dates = set(date_terms.keys())
all_years = set([x.year for x in all_dates])
for year in sorted(all_years):
    outfile = open(outdir + year + ".txt","w","utf-8")
    for date in [x for x in all_dates if x.year == year]:
        for periodic in date_periodics[date]:
            outfile.write("\t".join(periodic[:2]) + ",".join(periodic[2]) + ",".join(periodic[3]) + "\n")
    outfile.close()            
