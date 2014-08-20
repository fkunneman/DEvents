
import argparse
from collections import defaultdict
import os
import datetime

from event_pairs import Event_pairs

"""

"""
parser = argparse.ArgumentParser(description = "")
parser.add_argument('-i', action = 'store', nargs='+',required = False, 
    help = "the input files")  
parser.add_argument('-m', action = 'store', required = False, 
    help = "The file with information on existing pairs")
parser.add_argument('-w', action = 'store', required = False, 
    help = "The files with wikiscores per n-gram")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The tmp dict for pattern indexing")
parser.add_argument('-p', action = 'store', required = False, 
    help = "The server id for part-of-speech tagging")
parser.add_argument('-a', action = 'store', required = False,
    help = "Choose to extract entities. \'single\' for only the top entity, \'all\' for all common "
    "entities, \'ngram\' for all ngrams (baseline)")
parser.add_argument('-t', action = 'store_true',
    help = "Choose to include hashtags as entities")
parser.add_argument('-x', action = 'store_true',
    help = "Choose to add extra event informative terms to the description")
parser.add_argument('-o', action = 'store', 
    help = "The directory to write files to")
parser.add_argument('--window', type = int, action = 'store', default = 7,
    help = "The window in days of tweets on which event extraction is based (default = 7 days)")
parser.add_argument('--start', action = 'store_true',
    help = "Choose to rank events from the existing pairs (only applies when \'-m\' is included")
args = parser.parse_args() 

#sort input-files
day_files = defaultdict(list)
for infile in args.i:
    parts = infile.split("/")
    day = parts[-3][:2] + "_" + parts[-2]
    day_files[day].append(infile)

ep = Event_pairs(args.a,args.w,args.d,args.p)
if args.m:
    print("loading event tweets")
    eventfile = open(args.m,"r",encoding = "utf-8")
    ep.append_eventtweets(eventfile.readlines())
    eventfile.close()
    if args.start:
        print("ranking events")
        day = args.m.split("/")[-3][:2] + "_" + args.m.split("/")[-2] + "/"
        basedir = args.o + day    
        if not os.path.isdir(basedir):
            os.mkdir(basedir)
        # for j,ev in enumerate(event_vars):
        ep.rank_events("cosine")
        if args.x:
            for event in ep.events:
                event.add_event_terms()
        eventinfo = open(basedir + "events_fit.txt","w",encoding = "utf-8")
        for event in sorted(ep.events,key = lambda x : x.score,reverse=True):
            outstr = "\n" + "\t".join([str(event.date),str(event.score)]) + "\t" + \
                ", ".join([x[0] for x in event.entities]) + "\n" + \
                "\n".join([x.text for x in event.tweets]) + "\n"
            eventinfo.write(outstr)
        eventinfo.close()

for i,day in enumerate(sorted(day_files.keys())):
    print("extracting tweets with a time reference posted on",day)
    for infile in day_files[day]:
        tweetfile = open(infile,"r",encoding = "utf-8")
        ep.select_date_entity_tweets(tweetfile.readlines(),args.a,args.t,"exp")
        tweetfile.close()
    basedir = args.o + day + "/"
    if not os.path.isdir(basedir):
        os.mkdir(basedir)
    tweetinfo = open(basedir + "modeltweets.txt","w",encoding = "utf-8")
    for tweet in ep.tweets:
        info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
            " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks])]
        if tweet.e:
            info.append(" | ".join(tweet.entities))
        tweetinfo.write("\t".join(info) + "\n")
    tweetinfo.close()
    ep.discard_last_day(args.window)
    if len(set([x.date for x in ep.tweets])) >= 6:
        print("ranking events")
        ep.rank_events("cosine",basedir + "clusters.txt")
        if args.x:
            for event in ep.events:
                event.add_event_terms()
        eventinfo = open(basedir + "events_fit.txt","w",encoding = "utf-8")
        for event in ep.events:
            outstr = "\n" + "\t".join([str(event.date),str(event.score),str(event.g2_rank),
                str(event.tt_rank)]) + "\t" + ", ".join([x[0] for x in event.entities]) + \
                "\n" + "\n".join([x.text for x in event.tweets]) + "\n"
            eventinfo.write(outstr)
        eventinfo.close()
