#!/usr/bin/env 

import argparse
import re
from collections import defaultdict

import calculations

"""
program to clear event file from duplicates
"""
parser = argparse.ArgumentParser(description = "program to clear event file from duplicates")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
parser.add_argument('-o', action = 'store', required = True, help = "The output file")
args = parser.parse_args()

date_events = defaultdict(list)
infile = open(args.i,"r",encoding="utf-8")
lines = infile.readlines()
print("begin:",len(lines),"lines")
outfile = open(args.o,"w",encoding="utf-8")
newlines = 0
for line in lines:
    eventdict = {}
    tokens = line.strip().split("\t")
    eventdict["date"] = tokens[0]
    eventdict["score"] = tokens[1]
    eventdict["keylist"] = tokens[2].split(", ")
    ids = tokens[3].split(", ")
    texts = tokens[4].split("-----")
    eventdict["tweets"] = []
    for i,e in enumerate(ids):
        tweet = {}
        tweet["id"] = e
        tweet["text"] = texts[i]
        eventdict["tweets"].append(tweet)
    date_events[tokens[0]].append(eventdict)
infile.close()

for date in sorted(date_events.keys()):
    events = date_events[date]
    print(date,"BEFORE",len(events))
    unique_events = calculations.merge_event_sets([],date_events[date])
    print(date,"AFTER",len(unique_events))
    for event in unique_events:
        outfile.write("\t".join([event["date"],event["score"],
        ", ".join(event["keylist"]),", ".join([t["id"] for t in event["tweets"]]),
        "-----".join([t["text"] for t in event["tweets"]]) + "\n"]))

outfile.close()
