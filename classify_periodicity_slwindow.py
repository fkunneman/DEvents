#!/usr/bin/env 

import argparse
from collections import defaultdict
import ucto
import datetime
import re

import event_classes
import calculations
import time_functions

"""
Experimentation framework for calculating event periodicity from a given stream of events
"""
parser = argparse.ArgumentParser(description = "Experimentation framework for calculating " +
    "event periodicity from a given stream of events")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")
parser.add_argument('-s', action = 'store', type = int, nargs = '+', default = [2014,1,1], 
    help = "The date from which the periodicity of entities will be calculated [YYYY M(M) D(D)]")
parser.add_argument('-o', action = 'store', required = True, help = "The output directory")
parser.add_argument('--stdev', action = 'store_true', 
    help = "Choose to score periodicity by stdev (baseline)")
parser.add_argument('--cal', action = 'store_true', 
    help = "Choose to score periodicity with calendar periodicity detection")
parser.add_argument('--cluster', type=float, action = 'store', 
    help = "Choose a cosim threshold (0-1) to cluster periodic entities together")
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
term_periodicity = {}
calc_date = datetime.datetime(args.s[0],args.s[1],args.s[2])
print("Processing events")
for i,line in enumerate(lines):
    tokens = line.strip().split("\t")
    date = time_functions.return_datetime(tokens[0],setting="vs")
    score = tokens[1]
    terms = tokens[2].split(", ")
    ids = tokens[3].split(", ")
    tweets = tokens[4].split("-----")
    event = event_classes.Event(i,[date,terms,score,tweets])
    if date >= calc_date and date <= datetime.datetime(2014,4,3):
        print(event.date,event.entities,"calper")
        event_calendar.add_event(event,args.stdev,args.cal)
    else:
        event_calendar.add_event(event,False,False)

if args.cluster:
    #perform clustering
    event_calendar.cluster_entities_periodicity(args.cluster)
    #write periodics to file
    outfile = open(args.o + "calper_clustered_" + str(args.cluster)[2:] + ".txt",
        "w",encoding="utf-8")
    periodics = sorted(event_calendar.periodics,key = lambda x : x["score"],reverse = True)
    for periodic in periodics:
        outfile.write("---------------\n" + periodic["pattern"] + "\t" + 
            ", ".join(periodic["entities"]) + "\t" + 
            ",".join(str(x) for x in [periodic["score"],periodic["coverage"],
            periodic["consistency"],periodic["step"],periodic["len"]]) + "\t" + 
            " > ".join([str(x[0].date()) for x in periodic["dates"]]) + "\n" + 
            "\n".join([e.tweets[0] for e in periodic["events"]]) + "\n")
    outfile.close()

#sort by periodicity
entity_periodicity = []
for entity in event_calendar.entity_periodicity["calendar"].keys():
    for periodicity in event_calendar.entity_periodicity["calendar"][entity]:
        entity_periodicity.append([entity,periodicity])
sorted_periodicities = sorted(entity_periodicity,key = lambda x : x[1][0],reverse = True)

outfile = open(args.o + "calper_2014_cl.txt","w",encoding = "utf-8")
for p in sorted_periodicities:
    outfile.write("---------------\n" + p[0] + "\t" + p[1][-1] + "\t" + \
        ", ".join([str(x) for x in p[1][1:5]]) + "\t" + " > ".join([str(x[0]) for x in p[1][5]]) + \
        "\t" + ", ".join([str(x[0]) for x in p[1][6]]) + "\n")
outfile.close()

# tps = [[k,term_periodicity[k]] for k in term_periodicity.keys()]
# sorted_term_periodicity = sorted(tps,key = lambda x : x[1][0])
# sorted_term_periodicity_cutoff = []
# for tp in sorted_term_periodicity:
#     if tp[1][0] < 25:
#         sorted_term_periodicity_cutoff.append(tp)
#     else:
#         break

# outfile = open(args.o + "baseline_2014_firsthalf.txt","w",encoding = "utf-8")
# for tp in sorted_term_periodicity:
#     outfile.write(tp[0] + "\t" + str(tp[1][0]) + "\t" + ",".join([str(x) for x in tp[1][1]]) + "\t" + ",".join([str(x) for x in tp[1][2]]) + "\n")
# outfile.close()

#outfile = open(args.o + "baseline_2014_jaccard_k10.txt","w",encoding = "utf-8")
#terms = [x[0] for x in sorted_term_periodicity_cutoff]
#term_candidates = {}
#for term in terms:
#    term_candidates[term] = term_periodicity[term][3]
#    #print(term,term_candidates[term])

# clusters = calculations.cluster_jp(term_candidates,10)
# infoclusters = []
# for cluster in clusters.keys():
#     terms = clusters[cluster]
#     info = [[term,term_periodicity[term][0],term_periodicity[term][1]] for term in terms]
#     best_stdev = min([x[1] for x in info])
#     infoclusters.append([best_stdev,info])
# sorted_infoclusters = sorted(infoclusters,key = lambda x : x[0])
# for clust in sorted_infoclusters:
#     outfile.write("-------" + str(clust[0]) + "-------\n")
#     for term in clust[1]:
#         outfile.write(term[0] + "\t" + str(term[1]) + "\t" + ",".join([str(x) for x in term[2]]) + "\n")
# outfile.close()


# entity_candidates = [[x for x in event_calendar.entity_sequences[term]["entities"] if x in terms] for term in terms]
# dateseqs = [x[1][1] for x in sorted_term_periodicity_cutoff]
# clusters = calculations.cluster_time_vectors(terms,dateseqs,entity_candidates,datetime.datetime(2010,12,1),datetime.datetime(2014,7,1),3)
# infoclusters = []
# for cluster in clusters.keys():
#     vecs = clusters[cluster]
#     info = [sorted_term_periodicity_cutoff[x] for x in vecs]
#     terms = [x[0] for x in info]
#     stdevs = sorted([x[1][0] for x in info])
#     dateseqs = [",".join([str(d) for d in x[1][1]]) for x in info]
#     intervals = [",".join([str(i) for i in x[1][2]]) for x in info]
#     infoclusters.append([",".join(terms),stdevs,"---".join(dateseqs),"---".join(intervals)])
# sorted_info_clusters = sorted(infoclusters,key = lambda x : x[1][0])
# for clust in sorted_info_clusters:
#     outfile.write(clust[0] + "\t" + ",".join([str(x) for x in clust[1]]) + "\t" + clust[2] + "\t" + clust[3] + "\n")
# outfile.close()

#clusterterms
# outfile = open(args.o + "baseline_2014_firsthalf_clustered.txt","w",encoding = "utf-8")
# terms = [x[0] for x in sorted_term_periodicity_cutoff]
# entity_candidates = [[x for x in event_calendar.entity_sequences[term]["entities"] if x in terms] for term in terms]
# dateseqs = [x[1][1] for x in sorted_term_periodicity_cutoff]
# clusters = calculations.cluster_time_vectors(terms,dateseqs,entity_candidates,datetime.datetime(2010,12,1),datetime.datetime(2014,7,1),3)
# infoclusters = []
# for cluster in clusters.keys():
#     vecs = clusters[cluster]
#     info = [sorted_term_periodicity_cutoff[x] for x in vecs]
#     terms = [x[0] for x in info]
#     stdevs = sorted([x[1][0] for x in info])
#     dateseqs = [",".join([str(d) for d in x[1][1]]) for x in info]
#     intervals = [",".join([str(i) for i in x[1][2]]) for x in info]
#     infoclusters.append([",".join(terms),stdevs,"---".join(dateseqs),"---".join(intervals)])
# sorted_info_clusters = sorted(infoclusters,key = lambda x : x[1][0])
# for clust in sorted_info_clusters:
#     outfile.write(clust[0] + "\t" + ",".join([str(x) for x in clust[1]]) + "\t" + clust[2] + "\t" + clust[3] + "\n")
# outfile.close()


#for es in event_calendar.entity_sequences.keys():
#    print(es,"\t",event_calendar.entity_sequences[es])

# outfile = open(args.o + "test.txt","w",encoding = "utf-8")
# periodicities = []
# for term in event_calendar.term_stdev.keys():
#     for stdev in event_calendar.term_stdev[term]:
#         periodicities.append([stdev[0]] + [term] + [",".join([str(x) for x in stdev[1]])] + [",".join([str(x) for x in stdev[2]])] + [",".join([str(x) for x in event_calendar.term_sequences[term]["intervals"]])])
# sorted_periodicities = sorted(periodicities,key = lambda x : x[0])
# for per in sorted_periodicities:
#     outfile.write(str(per[0]) + "\t" + "\t".join(per[1:]) + "\n")


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
