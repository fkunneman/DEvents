#!/usr/bin/env 

import argparse
from collections import defaultdict
import datetime

import event_classes
import calculations
import time_functions

"""
Program to detect periodic events and rank them by certainty
"""
parser = argparse.ArgumentParser(description = 
    "Program to detect periodic events and rank them by certainty")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
parser.add_argument('-o', action = 'store', required = True, help = "The output directory")
parser.add_argument('--min', type = int, action = 'store', default = 2, 
    help = "The minimum number of days for an interval (default = 2)")
parser.add_argument('--max', type = int, action = 'store', default = 800, 
    help = "The maximum number of days for an interval (default = 800)")
parser.add_argument('-f', type = float, action = 'store', default = 0.1, 
    help = "The flexibility in percent difference allowed for periodicity (default = 0.1)")
parser.add_argument('-s', action = 'store', nargs = '+', 
    choices = ["tweets","keys","hashtag","popularity"], 
    help = "The features for event similarity")
parser.add_argument('-k', type=int, action = 'store', required = True, 
    help = "The value of k in k-NN clustering")    
args = parser.parse_args()

#load in events
print("reading in events")
index_event = {}
date_events = defaultdict(list)
infile = open(args.i,"r",encoding = "utf-8")
eventlines = infile.readlines()
infile.close()
for i,line in enumerate(eventlines):
    tokens = line.strip().split("\t")
    date = time_functions.return_datetime(tokens[0],setting="vs")
    entities = tokens[2].split(", ")
    score = float(tokens[1])
    tweets = tokens[4].split("-----")
    event = event_classes.Event(i,[date,entities,score,tweets])
    index_event[i] = event
    date_events[date].append(i)

#cluster events
print("start clustering")
event_links = defaultdict(list)
sorted_dates = sorted(date_events.keys())
event_ids = []
event_out = open(args.o + "event_order.txt","w","utf-8")
for i,date in enumerate(sorted_dates):
    event_ids.extend(date_events[date])
    for e in date_events[date]:
        event_out.write("\t".join([e.date," ".join(e.entities),e.score,"-----".join(e.tweets)]) + "\n")
event_docs = [" ".join(index_event[x].tweets) for x in event_ids]
print(event_docs[:10])
print("pair sim")
pair_sim = calculations.return_similarity_graph(event_docs[:25000])
i = 0
NNs = defaultdict(list)
outfile =   
for j,event_id in enumerate(event_ids):
    scores = [[key,pair_sim[j][key]] for key in event_ids]
    knn = sorted(scores,key = lambda x : x[1],reverse = True)[:args.k]
    print(j,knn)
    NNs[j] = knn

