
import argparse
import os

from event_pairs import Event_pairs

"""
Interface to applying event extraction
"""
parser = argparse.ArgumentParser(description = "Interface to applying event extraction")
parser.add_argument('-i', action = 'store', nargs='+',required = False, 
    help = "the input files")  
parser.add_argument('-w', action = 'store', required = False, 
    help = "The files with wikicores per n-gram")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The dict for pattern indexing")
parser.add_argument('-o', action = 'store', 
    help = "The directory to write files to")
parser.add_argument('--frog', action = 'store_true', help = "specify if frog is used")
parser.add_argument('--cities', action = 'store', required = False, 
    help = "to extract cities, include a file with city names")
args = parser.parse_args() 

ep = Event_pairs(args.w,args.d,args.frog,args.cities)
for tfname in args.i:
    tweetfile = open(tfname,"r",encoding="utf-8")
    tweets = tweetfile.read()
    tweetfile.close()
    events = ep.detect_events(tweets)
    print(events)
