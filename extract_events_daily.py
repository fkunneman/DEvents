
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
parser.add_argument('-a', action = 'store', required = True, choices = ["ngrams","cs","csx"], 
    help = "The type of entity extraction. \'ngram\' for all ngrams (baseline), \'cs\' for entities based on Wikipedia commonness score "
    "and \'csx\' for cs and extra terms from event clusters")
parser.add_argument('-f', action = 'store', default = "twiqs", choices = ["exp","twiqs"],
    help = "Specify the format of the inputted tweet files (default = twiqs)")
parser.add_argument('-o', action = 'store', required = True,
    help = "The directory to write files to")
parser.add_argument('--window', type = int, action = 'store', default = 7,
    help = "The window in days of tweets on which event extraction is based (default = 7 days)")
parser.add_argument('--start', action = 'store_true',
    help = "Choose to rank events from the existing pairs (only applies when \'-m\' is included")
args = parser.parse_args() 

#sort input-files
day_files = defaultdict(list)
if args.f == "twiqs":
    for infile in args.i:
        day = infile.split("/")[-1][:-6]
        day_files[day].append(infile)
elif args.f == "exp":
    for infile in args.i:
        parts = infile.split("/")
        day = parts[-3][:2] + "_" + parts[-2]
        day_files[day].append(infile)
else:
    print("format not included, exiting program")
    quit()

ep = Event_pairs(args.a,args.w,args.d)

def output_events(d):
    print("ranking events")
    ep.rank_events()
    ep.resolve_overlap_events(d + "clusters.txt")
    ep.enrich_events(args.a)
    eventinfo = open(d + "events_fit.txt","w",encoding = "utf-8")
    for event in sorted(ep.events,key = lambda x : x.score,reverse=True):
        if event.tt_ratio > 0.4:
            outstr = "\n" + "\t".join([str(event.date),str(event.score)]) + "\t" + \
                ", ".join([x[0] for x in event.entities]) + "\n" + \
                "\n".join([x.text for x in event.tweets]) + "\n"
            eventinfo.write(outstr)
    eventinfo.close()

if args.m:
    print("loading event tweets")
    eventfile = open(args.m,"r",encoding = "utf-8")
    ep.append_eventtweets(eventfile.readlines())
    eventfile.close()
    if args.start:
        day = args.m.split("/")[-3][:2] + "_" + args.m.split("/")[-2]
        basedir = args.o + day + "/"
        output_events(basedir)

for i,day in enumerate(sorted(day_files.keys())):
    print("extracting tweets with a time reference posted on",day)
    for infile in day_files[day]:
        tweetfile = open(infile,"r",encoding = "utf-8")
        if args.f == "twiqs":
            ep.select_date_entity_tweets(tweetfile.readlines()[1:],args.a,args.t,"twiqs")
        elif args.f == "exp":
            ep.select_date_entity_tweets(tweetfile.readlines(),args.a,args.t,"exp")
        tweetfile.close()
    basedir = args.o + day + "/"
    if not os.path.isdir(basedir):
        os.mkdir(basedir)
    tweetinfo = open(basedir + "modeltweets.txt","w",encoding = "utf-8")
    for tweet in ep.tweets:
        info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
            " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks]),
            " ".join([",".join(x) for x in tweet.postags])]
        if tweet.e:
            info.append(" | ".join(tweet.entities))
        tweetinfo.write("\t".join(info) + "\n")
    tweetinfo.close()
    ep.discard_last_day(args.window)
    if len(set([x.date for x in ep.tweets])) >= 6:
        output_events(basedir)
