
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
parser.add_argument('-w', action = 'store', nargs='+', required = False, 
    help = "The files with wikicores per n-gram")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The tmp dict for pattern indexing")
parser.add_argument('-a', action = 'store', required = False,
    help = "Choose to extract entities. \'single\' for only the top entity, \'all\' for all common "
    "entities")
parser.add_argument('-t', action = 'store_true',
    help = "Choose to include hashtags as entities")
parser.add_argument('-o', action = 'store', 
    help = "The directory to write files to")
parser.add_argument('--window', type = int, action = 'store', default = 7,
    help = "The window in days of tweets on which event extraction is based (default = 7 days)")
args = parser.parse_args() 

event_vars = [["fit",False,"events_fit.txt"],["freq",False,"events_freq.txt"]]

#sort input-files
day_files = defaultdict(list)
for infile in args.i:
    parts = infile.split("/")
    day = parts[-3][:2] + "_" + parts[-2]
    day_files[day].append(infile)

ep = Event_pairs()
if args.m:
    print("loading event tweets")
    eventfile = open(args.m,"r",encoding = "utf-8")
    ep.append_eventtweets(eventfile.readlines())
    eventfile.close()
    print("ranking events")
    day = args.m.split("/")[-3][:2] + "_" + args.m.split("/")[-2] + "/"
    basedir = args.o + day    
    try:
        os.mkdir(basedir)
    except:
        print("dir exists")
    print(basedir)
    for j,ev in enumerate(event_vars):
        ranked_events = ep.rank_events(ev[0],clust=ev[1])
        eventinfo = open(basedir + ev[2],"w",encoding = "utf-8")
        for event in ranked_events:
            try:
                outstr = "\n" + "\t".join([str(x) for x in event[:-1]]) + "\n" + "\n".join(event[-1]) + "\n"
            except TypeError:
                outstr = "\n" + "\t".join([str(x) for x in event]) + "\n"
            eventinfo.write(outstr)
        eventinfo.close()

if args.w:
    print("preparing ngram commonness scores")
    ep.load_commonness(args.d,args.w)

for i,day in enumerate(sorted(day_files.keys())):
    print("extracting tweets with a time reference posted on",day)
    for infile in day_files[day]:
        tweetfile = open(infile,"r",encoding = "utf-8")
        ep.select_date_entity_tweets(tweetfile.readlines(),args.a,args.t)
        tweetfile.close()
    ep.discard_last_day(args.window)
    if len(set([x.date for x in ep.tweets])) >= 6:
        print("ranking events")
        basedir = args.o + day + "/"
        try:
            os.mkdir(basedir)
        except:
            print("dir exists")
        print(basedir)
        tweetinfo = open(basedir + "modeltweets.txt","w",encoding = "utf-8")
        for tweet in ep.tweets:
            info = [tweet.id,tweet.user,str(tweet.date),tweet.text," ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks])]
            try:
                info.append(" ".join(tweet.entities))
                tweetinfo.write("\t".join(info) + "\n")
            except:
                tweetinfo.write("\t".join(info) + "\n")
        tweetinfo.close()
        for j,ev in enumerate(event_vars):
            ranked_events = ep.rank_events(ev[0],clust=ev[1])
            eventinfo = open(basedir + ev[2],"w",encoding = "utf-8")
            for event in ranked_events:
                try:
                    outstr = "\n" + "\t".join([str(x) for x in event[:-1]]) + "\n" + "\n".join(event[-1]) + "\n"
                except TypeError:
                    outstr = "\n" + "\t".join([str(x) for x in event]) + "\n"
                eventinfo.write(outstr)
            eventinfo.close()
