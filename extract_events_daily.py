
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
parser.add_argument('-w', action = 'store', nargs='+', required = False, 
    help = "The files with wikicores per n-gram")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The tmp dict for pattern indexing")
parser.add_argument('-a', action = 'store', required = False,
    help = "Choose to extract entities. \'single\' for only the top entity, or \'all\' for all common "
    "entities")
parser.add_argument('-t', action = 'store_true',
    help = "Choose to include hashtags as entities")
parser.add_argument('-o', action = 'store', 
    help = "The directory to write files to")
parser.add_argument('--window', type = int, action = 'store', default = 7,
    help = "The window in days of tweets on which event extraction is based (default = 7 days)")
args = parser.parse_args() 

#sort input-files
day_files = defaultdict(list)
for infile in args.i:
    parts = infile.split("/")
    day = parts[-3][:2] + "_" + parts[-2]
    day_files[day].append(infile)

ep = Event_pairs()
if args.w:
    ep.load_commonness(args.d,args.w)

for i,day in enumerate(sorted(day_files.keys())):
    print("extracting tweets with a time reference for day",day)
    for infile in day_files[day]:
        tweetfile = open(infile,"r",encoding = "utf-8")
        ep.select_date_entity_tweets(tweetfile.readlines(),args.a,args.t)
        tweetfile.close()
    ep.discard_tweets(args.window)
    if i >= 6:
        print("ranking events")
        ranked_events_fit = ep.rank_events("fit")
        ranked_events_freq = ep.rank_events("freq")
        ranked_events_fit_multi = ep.rank_events("fit",clust = True)
        #print(ranked_events)
        print("writing output")
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
        eventinfo_fit = open(basedir + "events_fit.txt","w",encoding = "utf-8")
        for event in ranked_events_fit:
            outstr = "\n" + "\t".join([str(x) for x in event[:-1]]) + "\n" + "\n".join(event[-1]) + "\n"
            eventinfo_fit.write(outstr)
        eventinfo_fit.close()
        eventinfo_freq = open(basedir + "events_freq.txt","w",encoding = "utf-8")
        for event in ranked_events_freq:
            outstr = "\n" + "\t".join([str(x) for x in event[:-1]]) + "\n\n"
            eventinfo_freq.write(outstr)
        eventinfo_freq.close()
        eventinfo_fit_multi = open(basedir + "events_fit_multi.txt","w",encoding = "utf-8")
        for event in ranked_events_fit_multi:
            outstr = "\n" + "\t".join([str(x) for x in event[:-1]]) + "\n" + "\n".join(event[-1]) + "\n"
            eventinfo_fit_multi.write(outstr)
        eventinfo_fit_multi.close()
