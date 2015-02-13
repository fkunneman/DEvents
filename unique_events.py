
import argparse
import calculations

"""
Script to merge sliding windows based collected events into a set of unique events
"""
parser = argparse.ArgumentParser(description = "Script to merge sliding windows based collected events into a set of unique events")
parser.add_argument('-i', action = 'store', nargs='+',required = True, 
    help = "the input files")
parser.add_argument('-o', action = 'store', required = True,
    help = "The output file")
args = parser.parse_args() 

unique_events = []
#extract and hash event data
for infile in args.i:
    print(infile)
    with open(infile,"r",encoding="utf-8") as fopen:
        lines = fopen.readlines()
    events = []
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
        events.append(eventdict)
    unique_events = calculations.merge_event_sets(unique_events,events)

outfile = open(args.o,"w",encoding="utf-8")
for event in unique_events:
    outfile.write("\t".join([event["date"],event["score"],
        ", ".join(event["keylist"]),", ".join([t["id"] for t in event["tweets"]]),
        "-----".join([t["text"] for t in event["tweets"]]) + "\n"]))
outfile.close()
