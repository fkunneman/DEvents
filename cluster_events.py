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
parser.add_argument('-o', action = 'store', required = True, help = "The output directory")
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
    for entity in entities:
        entityl_events[entity].append(i)
        
#generate canopies
print("generating canopies")
event_candidates = defaultdict(list)
entityls = sorted(entityl_events.keys())
all_combs = []
for entityl in entityls:
    events = entityl_events[entityl]
    combos = itertools.combinations(events, 2)
    for comb in combos:
        event_candidates[comb[0]].append(comb[1])
        event_candidates[comb[0]] = list(set(event_candidates[comb[0]]))
        event_candidates[comb[1]].append(comb[0])
        event_candidates[comb[1]] = list(set(event_candidates[comb[1]]))
    all_combs.append(tuple(sorted([comb[0],comb[1]])))
all_combs = list(set(all_combs))
num_combs = len(all_combs)

#cluster events
print("extracting tf-idf graph")
vectors = calculations.tfidf_docs(bigdocs)
print("calculating similarities")
comb_sim = defaultdict(lambda : defaultdict(float))
def calculate_similarity(combs,qu):
    for comb in combs:
        cos = calculations.return_similarities(comb[0],comb[1])
        qu.put([comb[0],comb[1],cos])

q = multiprocessing.Queue()
chunks = gen_functions.make_chunks(all_combs)
for c in chunks:
    p = multiprocessing.Process(target=calculate_similarity,args=[c,q])
    p.start()
i = 0
while True:
    l = q.get()
    comb_sim[l[0]][l[1]] = l[2]
    print(i,"/",num_combs)
    i += 1
    if i == num_combs:
        break

# print("clustering events")
# event_sims = defaultdict(list)
# events = event_candidates.keys()
# for i,event in enumerate(events):
#     print(i,"of",len(events))
#     event_vector = vectors[event]
#     candidates = event_candidates[event]
#     candidate_vectors = [vectors[candidate] for candidate in list(set(candidates) - set([x[0] for x in event_sims[event]]))]
# #    print("event",event,len(event_vector))
# #    print("candidates",candidates,[len(x) for x in candidate_vectors])
#     simscores = calculations.return_similarities(event_vector,candidate_vectors)
#     for ss in simscores:
#         event_sims[event].append([candidates[ss[0]],ss[1]])
#         event_sims[candidates[ss[0]]].append([event,ss[1]])



print(comb_sim,"Done.")