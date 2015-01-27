
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
parser.add_argument('-x', action='store_true', 
    help = "additional postagging during ranking to correct")
parser.add_argument('-q', action='store_true', 
    help = "Choose to output in Qualtrics format")
parser.add_argument('--window', type = int, action = 'store', default = 7,
    help = "The window in days of tweets on which event extraction is based (default = 7 days)")
parser.add_argument('--start', action = 'store_true',
    help = "Choose to rank events from the existing pairs (only applies when \'-m\' is included")
args = parser.parse_args() 

#sort input-files
day_files = defaultdict(list)
if args.i: 
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

ep = Event_pairs(args.w,args.d)

def output_events(d):
    print("ranking events")
    ep.rank_events(args.a)
    ep.resolve_overlap_events(d + "clusters.txt")
    ep.enrich_events(args.a,xpos = args.x)
    if args.x:
        tweetinfo = open(d + "modeltweets.txt","w",encoding = "utf-8")
        for tweet in ep.tweets:
            info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
                " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks]),
                " | ".join(tweet.entities)," | ".join(",".join(x) for x in tweet.postags)]
            tweetinfo.write("\t".join(info) + "\n")
        tweetinfo.close()
    eventinfo = open(d + "events_fit.txt","w",encoding = "utf-8")
    if args.q:
        eventq = open(d + "events_qualtrics.txt","w",encoding = "utf-8")
    for event in sorted(ep.events,key = lambda x : x.score,reverse=True):
        if event.tt_ratio > 0.30:
            if "linkshandigen" in [x[0] for x in event.entities] or "flikken" in [x[0] for x in event.entities] or "maastricht" in [x[0] for x in event.entities] or "flikkendag" in [x[0] for x in event.entities] or "de sims 4" in [x[0] for x in event.entities]:
                print("BEFORE tweet rank",[x.text for x in event.tweets]) 
            event.rank_tweets(rep = True)
            if "linkshandigen" in [x[0] for x in event.entities] or "flikken" in [x[0] for x in event.entities] or "maastricht" in [x[0] for x in event.entities] or "flikkendag" in [x[0] for x in event.entities] or "de sims 4" in [x[0] for x in event.entities]:
                print("AFTER tweet rank",event.reptweets) 
            if args.q:
                eventq.write("[[Question:MC:SingleAnswer:Vertical]]\nVerwijzen deze 5 tweets naar dezelfde gebeurtenis? <br> <br> <br> " +
                    "\n<table border=\"1\" cellpadding=\"1\" cellspacing=\"1\" style=\"width: 500px;\">\n\t<tbody>\n\t\t<tr>\n\t\t\t<td><b>")
                for tweet in event.reptweets:
                    eventq.write(tweet + "<br />\n\t\t\t<br />\n\t\t\t")
                eventq.write("</tr>\n\t</tbody>\n</table>\n[[choices]]\nJa\nNee\n\n[[Question:MC:SingleAnswer:Vertical]]\n" +
                    "Hoe verhouden onderstaande termen zich tot de gebeurtenis? <br> <br>\n")
                for ent in event.entities:
                    eventq.write("<b>" + ent[0] + "</b> <br>\n")
                eventq.write("[[Choices]]\nGoed\nMatig\nSlecht\n\n")
            outstr = "\n" + "\t".join([str(event.date),str(event.score)]) + "\t" + \
                ", ".join([x[0] for x in event.entities]) + "\n" + \
                "\n".join([x.text for x in event.tweets]) + "\n"
            eventinfo.write(outstr)
    eventinfo.close()
    if args.q:
        eventq.close()

if args.m:
    print("loading event tweets")
    eventfile = open(args.m,"r",encoding = "utf-8")
    ep.append_eventtweets(eventfile.readlines())
    eventfile.close()
    if args.start:
        day = args.m.split("/")[-2]
        basedir = args.o + day + "/"
        if not os.path.isdir(basedir):
            os.mkdir(basedir)
        output_events(basedir)

for i,day in enumerate(sorted(day_files.keys())):
    print("extracting tweets with a time reference posted on",day)
    for infile in day_files[day]:
        tweetfile = open(infile,"r",encoding = "utf-8")
        if args.f == "twiqs":
            ep.select_date_entity_tweets(tweetfile.readlines()[1:],"twiqs")
        elif args.f == "exp":
            ep.select_date_entity_tweets(tweetfile.readlines(),"exp")
        tweetfile.close()
    basedir = args.o + day + "/"
    if not os.path.isdir(basedir):
        os.mkdir(basedir)
    tweetinfo = open(basedir + "modeltweets.txt","w",encoding = "utf-8")
    for tweet in ep.tweets:
        info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
            " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks]),
            " | ".join(tweet.entities)," | ".join(",".join(x) for x in tweet.postags)]
        tweetinfo.write("\t".join(info) + "\n")
    tweetinfo.close()
    ep.discard_last_day(args.window)
    if len(set([x.date for x in ep.tweets])) >= 6:
        output_events(basedir)
