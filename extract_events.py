
import argparse
from event_pairs import Event_pairs

"""

"""
parser = argparse.ArgumentParser(description = "")
parser.add_argument('-i', action = 'store', nargs='+',required = True, 
    help = "the input file")  
parser.add_argument('-m', action = 'store', required = False, 
    help = "The file with information on existing pairs")
parser.add_argument('-w', action = 'store', nargs='+', required = False, 
    help = "The files with wikicores per n-gram")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The tmp dict for pattern indexing")
parser.add_argument('-a', action = 'store', default = "single",
    help = "Choose to extract only the top entity, or all common "
    "entities")
parser.add_argument('-t', action = 'store_true',
    help = "Choose to include hashtags as entities")
parser.add_argument('-p', action = 'store', required = True, 
    help = "File to write tweet info to")
parser.add_argument('-o', action = 'store', required = True, 
    help = "File to write ranked events to")
args = parser.parse_args() 

ep = Event_pairs()
print("extracting tweets with a time reference")
if args.m:
    for infile in args.m:
        eventfile = open(infile,"r",encoding = "utf-8")
        ep.append_eventtweets(eventfile.readlines())
        eventfile.close()
for infile in args.i:
    tweetfile = open(infile,"r",encoding = "utf-8")
    ep.select_date_tweets(tweetfile.readlines())
    tweetfile.close()
print("extracting entities")
if args.w:
    ep.select_entity_tweets(args.d,args.w,args.a)
if args.t:
    ep.select_hashtags_tweets()
print("ranking events")
ranked_events = ep.rank_events()
#print(ranked_events)
print("writing output")
tweetinfo = open(args.p,"w",encoding = "utf-8")
for tweet in ep.tweets:
    info = [tweet.id,tweet.user,str(tweet.date),tweet.text," ".join([str(x) for x in tweet.daterefs]),"|".join(x for x in tweet.chunks])]
    try:
        info.append(" ".join(tweet.entities))
    except:
        print("no entity")
    tweetinfo.write("\t".join(info) + "\n")
tweetinfo.close()
eventinfo = open(args.o,"w",encoding = "utf-8")
for event in ranked_events:
    outstr = "\n" + "\t".join([str(x) for x in event[:-1]]) + "\n" + "\n".join(event[-1]) + "\n"
    eventinfo.write(outstr)
eventinfo.close()
