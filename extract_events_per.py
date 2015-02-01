
import argparse
from collections import defaultdict
import os
import datetime

from event_pairs import Event_pairs

"""
Script to similate the daily extraction of time referring tweet and event clustering
"""
parser = argparse.ArgumentParser(description = "Script to similate the daily extraction of time referring tweet and event clustering")
parser.add_argument('-i', action = 'store', nargs='+',required = False, 
    help = "the input files")
parser.add_argument('-m', action = 'store', required = False, 
    help = "The file with information on existing pairs (modeltweets.txt)")
parser.add_argument('-w', action = 'store', required = False, 
    help = "The directory hosting the files with wikiscores per n-gram")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The tmp directory for pattern indexing")
parser.add_argument('-o', action = 'store', required = True,
    help = "The directory to write files to")
parser.add_argument('--start', action = 'store_true',
    help = "Choose to rank events from the existing pairs (only applies when \'-m\' is included")
parser.add_argument('--cities', action = 'store',
    help = "To exclude city names from entity extraction, specify a file met city names")
args = parser.parse_args() 

#sort input-files
day_files = {}
if args.i: 
    for infile in args.i:
        day = infile.split("/")[-1][:-4]
        day_files[day] = infile

ep = Event_pairs(args.w,args.d,cities = args.cities)

def output_events(d):
    print("ranking events")
    ep.rank_events(2000)
    ep.resolve_overlap_events()
    ep.enrich_events("csx",order = False)
    eventinfo = open(d + "events_fit.txt","w",encoding = "utf-8")
    for event in sorted(ep.events,key = lambda x : x.score,reverse=True):
        print("join([str(event.date),str(event.score)])",event.date,event.score)
        print("\t".join([str(event.date),str(event.score)]))
        print("join([event.places])",event.places)
        print(", ".join([event.places]))
        print("join([x[0] for x in event.entities])",event.entities)
        print(", ".join([x[0] for x in event.entities]))
        print("join([x.text for x in event.tweets])",event.tweets)
        print("-----".join([x.text for x in event.tweets]))
        outstr = "\t".join([str(event.date),str(event.score)]) + "\t" + \
            ", ".join([event.places]) + \
            ", ".join([x[0] for x in event.entities]) + "\t" + \
            ", ".join([x.id for x in event.tweets]) + "\t" + \
            "-----".join([x.text for x in event.tweets])
        eventinfo.write(outstr)
    eventinfo.close()

for i,day in enumerate(sorted(day_files.keys())):
    print("extracting tweets with a time reference posted on",day)
    tweetfile = open(day_files[day],"r",encoding = "utf-8")
    ep.append_eventtweets(tweetfile.readlines(),entities=True)
    tweetfile.close()
    if i >= 1:
        basedir = args.o + day + "/"
        if not os.path.isdir(basedir):
            os.mkdir(basedir)
        tweetinfo = open(basedir + "modeltweets.txt","w",encoding = "utf-8")
        for tweet in ep.tweets:
            if hasattr(tweet, 'postags') and hasattr(tweet, 'phrase'):
                info = [tweet.id,tweet.user,str(tweet.date),tweet.text,tweet.phrase,
                    " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks]),
                    " | ".join(tweet.entities)," | ".join(",".join(x) for x in tweet.postags)]
            else:
                if hasattr(tweet, 'postags'):
                    info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
                        " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks]),
                        " | ".join(tweet.entities)," | ".join(",".join(x) for x in tweet.postags)]
                elif hasattr(tweet, 'phrase'):
                    info = [tweet.id,tweet.user,str(tweet.date),tweet.text,tweet.phrase,
                        " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks]),
                        " | ".join(tweet.entities)]
                else:
                    info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
                    " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks]),
                    " | ".join(tweet.entities)]
            tweetinfo.write("\t".join(info) + "\n")
        tweetinfo.close()
        ep.discard_last_day(30)
        output_events(basedir)
