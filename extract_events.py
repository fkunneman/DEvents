
import argparse
from event_pairs import Event_pairs

"""

"""
parser = argparse.ArgumentParser(description = "")
parser.add_argument('-i', action = 'store', required = True, help = "the input file")  
parser.add_argument('-m', action = 'store', required = False, 
    help = "The file with information on existing pairs")
parser.add_argument('-w', action = 'store', nargs='+', required = False, 
    help = "The files with wikicores per n-gram")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The tmp dict for pattern indexing")
parser.add_argument('-o', action = 'store', required = True, 
    help = "File to write event pairs to")
args = parser.parse_args() 

ep = Event_pairs()
print("extracting tweets with a time reference")
tweetfile = open(args.i,"r",encoding = "utf-8")
ep.select_date_tweets(tweetfile.readlines())
tweetfile.close()
print("extracting entities")
ep.select_entity_tweets(args.d,args.w)
print("ranking events")
ranked_events = ep.rank_events()
print(ranked_events)

