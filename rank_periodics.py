#!/usr/bin/env 

import argparse
from collections import defaultdict
import datetime
import itertools

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
for entityl in entityls:
    events = entityl_events[entityl]
    combos = itertools.combinations(events, 2)
    for comb in combos:
        event_candidates[comb[0]].append(comb[1])
        event_candidates[comb[0]] = list(set(event_candidates[comb[0]]))
        event_candidates[comb[1]].append(comb[0])
        event_candidates[comb[1]] = list(set(event_candidates[comb[1]]))

#cluster events
print("extracting tf-idf graph")
vectors = calculations.tfidf_docs(bigdocs)
print("clustering events")
event_sims = defaultdict(list)
events = event_candidates.keys()
for i,event in enumerate(events):
    print(i,"of",len(events))
    event_vector = vectors[event]
    candidates = event_candidates[event]
    candidate_vectors = [vectors[candidate] for candidate in list(set(candidates) - set([x[0] for x in event_sims[event]]))]
#    print("event",event,len(event_vector))
#    print("candidates",candidates,[len(x) for x in candidate_vectors])
    simscores = calculations.return_similarities(event_vector,candidate_vectors)
    for ss in simscores:
        event_sims[event].append([candidates[ss[0]],ss[1]])
        event_sims[candidates[ss[0]]].append([event,ss[1]])

print(event_sims,"Done.")


#generate bigdocs per date
# sorted_dates = sorted(date_events.keys())
# bigdocs = []
# segments = []
# for i,date in enumerate(sorted_dates):
#     event_ids = date_events[date]
#     date_bigdocs[date] = [" ".join(index_event[x].tweets) for x in event_ids]
#     if i == 0:
#         print(date,date_bigdocs[date])
    # segments.append(len(event_ids))
    # bigdocs.extend([" ".join(index_event[x].tweets) for x in event_ids])

#cluster events
# print("start clustering")
# eventlinks = defaultdict(list)
# # unperiodics = []
# # periodics = {}
# # for index in index_event.keys():
# #     periodics[index] = False
# # sequences = []
# # index_sequences = {}
# i = args.min+1
# for date in sorted_dates[i:]:
#     print(date)
#     for j,date_backward in enumerate(sorted_dates[0:i-args.min]):
#         bigdocs = date_bigdocs[date_backward]
#         print(date_backward,len(date_events[date_backward]))
#         for index in date_events[date]:
#             bigdoc = " ".join(index_event[index].tweets)
#             #print(bigdoc,bigdocs)
#             simevents = sorted(calculations.return_similarity_graph(bigdocs,bigdoc),key=lambda x: x[1],reverse=True)
#             #sorted(unsorted_list, key = lambda x: int(x[3]))
#             #print(simevents)
#             if len(simevents) < 5:
#                 top = len(simevents)
#             else:
#                 top = 5
#             for rank in range(top):
#                 if simevents[rank][1] > 0.5:
#                     simevent = simevents[0][0]
#                     simindex = date_events[date_backward][simevent]
#                     eventlinks[index].append(simindex)
#                 else:
#                     break
#     i+=1

# print(eventlinks)

                    # if periodics[index]:
                    #     sequence = index_sequences[index]
                    #     sequences[sequence].append(simevent)
                    #     periodics[simevent] = True
                    #     index_sequences[simevent] = sequence
                    # else:


                    #for x in 


    # for e in date_events[date]:
    #     event_out.write("\t".join([e.date," ".join(e.entities),e.score,"-----".join(e.tweets)]) + "\n")


# event_links = defaultdict(list)
# sorted_dates = sorted(date_events.keys())
# event_ids = []
# event_out = open(args.o + "event_order.txt","w","utf-8")

# event_docs = [" ".join(index_event[x].tweets) for x in event_ids]
# print(event_docs[:10])
# print("pair sim")
# pair_sim = calculations.return_similarity_graph(event_docs[:25000])
# i = 0
# NNs = defaultdict(list)
# outfile =   
# for j,event_id in enumerate(event_ids):
#     scores = [[key,pair_sim[j][key]] for key in event_ids]
#     knn = sorted(scores,key = lambda x : x[1],reverse = True)[:args.k]
#     print(j,knn)
#     NNs[j] = knn

