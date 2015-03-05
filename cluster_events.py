#!/usr/bin/env 

import argparse
from collections import defaultdict
import datetime
import itertools
import multiprocessing

import event_classes
import calculations
import time_functions
import gen_functions

"""
Program to detect periodic events and rank them by certainty
"""
parser = argparse.ArgumentParser(description = 
    "Program to detect periodic events and rank them by certainty")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
parser.add_argument('-o', action = 'store', required = True, help = "The output file")
parser.add_argument('--min', type = int, action = 'store', default = 2, 
    help = "The minimum number of days for an interval (default = 2)")
parser.add_argument('--max', type = int, action = 'store', default = 800, 
    help = "The maximum number of days for an interval (default = 800)")
parser.add_argument('-k', type=int, action = 'store', required = True, 
    help = "The value of k in k-NN clustering")    
args = parser.parse_args()

#load in events
print("reading in events")
index_event = {}
entityl_events = defaultdict(list)
bigdocs = []
infile = open(args.i,"r",encoding = "utf-8")
eventlines = infile.readlines()
infile.close()
numlines = len(eventlines)
for i,line in enumerate(eventlines):
    print(i,"of",numlines)
    tokens = line.strip().split("\t")
    date = time_functions.return_datetime(tokens[0],setting="vs")
    entities = tokens[2].split(", ")
    score = float(tokens[1])
    tweets = tokens[4].split("-----")
    bigdocs.append(" ".join(tweets))
    event = event_classes.Event(i,[date,entities,score,tweets])
    index_event[i] = event
    entityls = tokens[5].split(", ")
    print(entityls)
    for entityl in entityls:
        entityl_events[entityl].append([i,date])
        
#generate canopies
print("generating canopies")
event_candidates = defaultdict(list)
entityls = sorted(entityl_events.keys())
all_combs = []
le = len(entityls)
for i,entityl in enumerate(entityls):
    print(i,"of",le,"canopies")
    events = entityl_events[entityl]
    if (len(events) / numlines) < 0.03:
        combos = itertools.combinations(events, 2)
        for comb in combos:
            dif = (comb[0][1].date()-comb[1][1].date()).days 
            if dif < 0:
                dif = dif * -1
            if dif >= args.min and dif <= args.max: 
                # event_candidates[comb[0]].append(comb[1])
                # event_candidates[comb[0]] = list(set(event_candidates[comb[0]]))
                # event_candidates[comb[1]].append(comb[0])
                # event_candidates[comb[1]] = list(set(event_candidates[comb[1]]))
                all_combs.append(tuple(sorted([comb[0][0],comb[1][0]])))
all_combs = list(set(all_combs))
num_combs = len(all_combs)

#cluster events
print("extracting tf-idf graph")
vectors = calculations.tfidf_docs(bigdocs)
print("calculating similarities")
knn = defaultdict(list)
def calculate_similarity(combs,qu):
    for comb in combs:
        cos = calculations.return_similarities(vectors[comb[0]],vectors[comb[1]])
        qu.put([comb[0],comb[1],cos[0][0]])

q = multiprocessing.Queue()
chunks = gen_functions.make_chunks(all_combs)
for c in chunks:
    p = multiprocessing.Process(target=calculate_similarity,args=[c,q])
    p.start()
i = 0
while True:
    l = q.get()
    knn[l[0]].append([l[1],l[2]])
    knn[l[1]].append([l[0],l[2]])
    print(i,"/",num_combs)
    i += 1
    if i == num_combs:
        break

print("clustering events")
events = sorted(knn.keys())
for event in events:
    knn[event] = [n[0] for n in sorted(knn[event],key = lambda x : x[1],reverse = True)[:args.k]]
#make links based on jp
event_group = {}
for event in events:
    event_group[event] = False
groups = []
for comb in all_combs:
    c0 = comb[0]
    c1 = comb[1]
    if c1 in knn[c0]:
        if c0 in knn[c1]:
            #link between events
            if event_group[c0] != event_group[c1]:
                if event_group[c0] == False: #c1 has a group
                    groups[event_group[c1]].append(c0)
                    event_group[c0] = event_group[c1]
                elif event_group[c1] == False: #c0 has a group
                    groups[event_group[c0]].append(c1)
                    event_group[c1] = event_group[c0]
                else: #different groups  
                    eg = event_group[c0]
                    groups[eg].append(c1)
                    groups[eg].extend(groups[event_group[c1]])
                    groups[event_group[c1]] = []
                    event_group[c1] = eg
            else: #groups are the same
                if event_group[c0] == False or event_group[c1] == False: #no group yet
                    groups.append([c0,c1])
                    event_group[c0] = len(groups)-1
                    event_group[c1] = len(groups)-1

#write to file
print("writing to file")
outfile = open(args.o,"w",encoding="utf-8")
for group in groups:
    events = list(set(group))
    eventout = []
    dates = []
    i = 0
    while i < len(events):
        evindex = events[i]
        event = index_event[evindex]
        date = event.date.date()
        close = False
        for d in dates:
            if ((date-d).days * -1) <= args.min:
                close = True
        if close:
            del events[i]
        else: 
            dates.append(date)
            eventout.append("|".join([str(evindex),str(date),",".join(event.entities)]))
            i += 1
    if len(eventout) >= 3:
        outfile.write("\t".join(eventout) + "\n")
outfile.close()

