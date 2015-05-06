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
parser.add_argument('--predict', type=int, action= 'store', nargs = '+', required=False,
    help = "choose to predict upcoming editions of an event, at date [1,2,3] up to date [4,5,6]")
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
predict = False
if args.predict:
    predict_date = datetime.datetime(args.predict[0],args.predict[1],args.predict[2])
    predict_to_date = datetime.datetime(args.predict[3],args.predict[4],args.predict[5])
    predict = True

print("Processing events")
for i,line in enumerate(lines):
    tokens = line.strip().split("\t")
    date = time_functions.return_datetime(tokens[0],setting="vs")
    score = tokens[1]
    terms = tokens[2].split(", ")
    ids = tokens[3].split(", ")
    tweets = tokens[4].split("-----")
    event = event_classes.Event(i,[date,terms,score,tweets])
    if date >= calc_date:
        if predict:
            if date == predict_date:
                print("making predictions")
                event_calendar.cluster_entities_periodicity(args.cluster,args.cal)
                if args.stdev:
                    predictfile = open(args.o + "stdev_predictions.txt","w",encoding="utf-8")
                    event_calendar.predict_events_timeline(predict_to_date,25)
                    for entry in event_calendar.expected_events:
                        predictfile.write("\t".join([", ".join(entry[0]),
                            "-".join([str(x) for x in entry[1]]),
                            ", ".join([str(x) for x in [entry[2:]]])]) + "\n")
                    predictfile.close()
                    quit()
                else:
                    predictfile = open(args.o + "calper_predictions.txt","w",encoding="utf-8")
                    event_calendar.predict_events(predict_to_date,0.25)
                    for entry in event_calendar.expected_events:
                        predictfile.write("\t".join([", ".join(entry[0]),entry[1],
                            ", ".join([str(x) for x in [entry[2:]]])]) + "\n")
                    predictfile.close()
                    quit()
    #and date <= datetime.datetime(2014,4,3):
        print(event.date,event.entities,"calper")
        event_calendar.add_event(event,args.stdev,args.cal)
    else:
        event_calendar.add_event(event,False,False)
    #if date == datetime.datetime(2014,2,1):
    #    break

if args.cluster:
    #perform clustering
    event_calendar.cluster_entities_periodicity(args.cluster,args.cal)
    #write periodics to file
    if args.cal:
        outfile = open(args.o + "calper_clusteredpattern_" + str(args.cluster)[2:] + ".txt",
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
    else:
        outfile = open(args.o + "stdev_clustered_" + str(args.cluster)[2:] + ".txt",
            "w",encoding="utf-8")
        periodics = sorted(event_calendar.periodics,key = lambda x : x["score"])
        for periodic in periodics:
            outfile.write("---------------\n" + str(periodic["score"]) + "\t" + 
                ", ".join(periodic["entities"]) + "\t" + 
                " > ".join([str(x) for x in periodic["dates"]]) + "\t" +
                "-".join([str(x) for x in periodic["intervals"]]) + "\n" + 
                "\n".join([e.tweets[0] for e in periodic["events"]]) + "\n")
        outfile.close()       

# else:
#     #sort by periodicity
#     entity_periodicity = []
#     for entity in event_calendar.entity_periodicity["calendar"].keys():
#         for periodicity in event_calendar.entity_periodicity["calendar"][entity]:
#             entity_periodicity.append([entity,periodicity])
#     sorted_periodicities = sorted(entity_periodicity,key = lambda x : x[1][0],reverse = True)

#     outfile = open(args.o + "calper_2014_cl.txt","w",encoding = "utf-8")
#     for p in sorted_periodicities:
#         outfile.write("---------------\n" + p[0] + "\t" + p[1][-1] + "\t" + \
#             ", ".join([str(x) for x in p[1][1:5]]) + "\t" + " > ".join([str(x[0]) for x in p[1][5]]) + \
#             "\t" + ", ".join([str(x[0]) for x in p[1][6]]) + "\n")
#     outfile.close()
