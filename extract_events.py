
import argparse
import os

from event_pairs import Event_pairs

"""
Interface to applying event extraction
"""
parser = argparse.ArgumentParser(description = "Interface to applying event extraction")
parser.add_argument('-i', action = 'store', nargs='+',required = False, 
    help = "the input files")  
parser.add_argument('-m', action = 'store', required = False, 
    help = "The file with information on existing pairs")
parser.add_argument('-w', action = 'store', nargs='+', required = False, 
    help = "The files with wikicores per n-gram")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The dict for pattern indexing")
parser.add_argument('-o', action = 'store', 
    help = "The directory to write files to")
parser.add_argument('--window', type = int, action = 'store', default = 7,
    help = "The window in days of tweets on which event extraction is based (default = 7 days)")
parser.add_argument('--start', action = 'store_true',
    help = "Choose to rank events from the existing pairs (only applies when \'-m\' is included")
args = parser.parse_args() 

ep = Event_pairs()

print("preparing ngram commonness scores")
ep.load_commonness(args.d,args.w)
if args.m:
    print("loading event tweets")
    eventfile = open(args.m,"r",encoding = "utf-8")
    ep.append_eventtweets(eventfile.readlines())
    eventfile.close()

for infile in args.i:
    tweetfile = open(infile,"r",encoding = "utf-8")
    ep.select_date_entity_tweets(tweetfile.readlines(),"all",True)
    tweetfile.close()
basedir = args.o
if not os.path.isdir(basedir):
    os.mkdir(basedir)
ep.discard_last_day(args.window)
tweetinfo = open(basedir + "modeltweets.txt","w",encoding = "utf-8")
for tweet in ep.tweets:
    info = [tweet.id,tweet.user,str(tweet.date),tweet.text," ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks])]
    if tweet.e:
        info.append(" | ".join(tweet.entities))
    tweetinfo.write("\t".join(info) + "\n")
tweetinfo.close()
print("ranking events")
ep.rank_events("cosine")
eventinfo = open(basedir + "events_fit.txt","w",encoding = "utf-8")
for event in sorted(ep.events,key = lambda x : x.score,reverse=True):
    outstr = "\n" + "\t".join([str(event.date),str(event.score)]) + "\t" + ", ".join([x[0] for x in event.entities]) + "\n" + "\n".join(event.tweets) + "\n"
    eventinfo.write(outstr)
eventinfo.close()
