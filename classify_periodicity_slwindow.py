#!/usr/bin/env 

import argparse
from collections import defaultdict
import ucto

import event_classes
import calculations
import time_functions

"""

"""
parser = argparse.ArgumentParser(description = "")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
parser.add_argument('-o', action = 'store', required = True, help = "The output directory")
args = parser.parse_args() 

date_periodics = defaultdict(list)
date_terms = defaultdict(list)
term_dates = defaultdict(list)
term_date_events = defaultdict(lambda : defaultdict(list))

event_calendar = event_classes.Calendar()

#for each line
infile = open(args.i,"r",encoding="utf-8")
lines = infile.readlines()
infile.close()
for i,line in enumerate(lines[:45000]):
    tokens = line.strip().split("\t")
    date = time_functions.return_datetime(tokens[0],setting="vs")
    score = tokens[1]
    terms = tokens[2].split(", ")
    ids = tokens[3].split(", ")
    tweets = tokens[4].split("-----")
    event = event_classes.Event(i,[date,terms,score,tweets])
    event.add_tids(ids)
    event_calendar.add_event(event)

outfile = open(args.o + "test.txt","w",encoding = "utf-8")
periodicities = []
for term in event_calendar.term_stdev.keys():
    for stdev in event_calendar.term_stdev[term]:
        periodicities.append([stdev[0]] + [term] + [",".join([str(x) for x in stdev[1]])] + [",".join([str(x) for x in stdev[2]])] + [",".join([str(x) for x in event_calendar.term_sequences[term]["intervals"]])])
sorted_periodicities = sorted(periodicities,key = lambda x : x[0])
for per in sorted_periodicities:
    outfile.write(str(per[0]) + "\t" + "\t".join(per[1:]) + "\n")


#for string in event_calendar.string_events.keys():
#    print([x.entities for x in event_calendar.string_events[string]])


#     date_terms[date].extend()
#     for term in tokens[2].split(", "):
#         term_date_events[term][date].append(line.strip())
#         term_dates[term].append(date)

# for current_date in sorted(date_terms.keys())[:400]:
#     print(current_date)
#     for term in list(set(date_terms[current_date])):
#         history = [date for date in term_dates[term] if date < current_date] + [current_date]
#         intervals = calculations.return_intervals(history)
#         if len(intervals) >= 2:
#             scores = []
#             for i in range(len(intervals[:-1])):
#                 sequence = intervals[i:]
#                 scores.append([i,calculations.return_relative_stdev(sequence)])
#             best = sorted(scores,key = lambda x : x[0])[0]
#             date_periodics[current_date].append([term,best[1],intervals,history[best[0]:]])

# all_dates = set(date_terms.keys())
# all_years = set([x.year for x in all_dates])
# for year in sorted(all_years):
#     outfile = open(args.o + str(year) + ".txt","w",encoding = "utf-8")
#     periodics = []
#     for date in [x for x in all_dates if x.year == year]:
#         periodics.extend(date_periodics[date])
#     for periodic in sorted(periodics,key = lambda x : x[1]):
#         outfile.write(periodic[0] + "\t" + str(periodic[1]) + "\t" + \
#             ",".join([str(x) for x in periodic[2]]) + "\t" + \
#             ",".join([str(x) for x in periodic[3]]) + "\n")
#     outfile.close()            
