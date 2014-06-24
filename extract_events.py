
import argparse
import codecs
from event_pairs import Event_pairs

"""

"""
parser = argparse.ArgumentParser(description = "")
parser.add_argument('-i', action = 'store', required = True, help = "the input file")  
parser.add_argument('-m', action = 'store', required = False, 
    help = "The file with information on existing pairs")
args = parser.parse_args() 

ep = Event_pairs(args.m)
tweetfile = codecs.open(args.i,"r","utf-8")
ep.extract_date(tweetfile.readlines())
tweetfile.close()
