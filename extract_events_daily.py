 
import argparse
from collections import defaultdict
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
for day in sorted(day_files.keys()):
    print("extracting tweets with a time reference")
    for infile in day_files[day]:
        print(infile)
        tweetfile = open(infile,"r",encoding = "utf-8")
        ep.select_date_tweets(tweetfile.readlines())
        tweetfile.close()
    if args.a:
        print("extracting entities")
        ep.select_entity_tweets(args.a)
    if args.t:
        ep.select_hashtags_tweets()
    print("ranking events")
    ranked_events = ep.rank_events()
    #print(ranked_events)
    print("writing output")
    basedir = args.o + day + "/"
    tweetinfo = open(basedir + "modeltweets.txt","w",encoding = "utf-8")
    for tweet in ep.tweets:
        info = [tweet.id,tweet.user,str(tweet.date),tweet.text," ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks])]
        try:
            info.append(" ".join(tweet.entities))
            tweetinfo.write("\t".join(info) + "\n")
        except:
            tweetinfo.write("\t".join(info) + "\n")
    tweetinfo.close()
    eventinfo = open(basedir + "events.txt","w",encoding = "utf-8")
    for event in ranked_events:
        outstr = "\n" + "\t".join([str(x) for x in event[:-1]]) + "\n" + "\n".join(event[-1]) + "\n"
        eventinfo.write(outstr)
    eventinfo.close()
    print(day,"done")
