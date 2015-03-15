#!/usr/bin/env 

import argparse
import datetime
import time_functions
import calculations
import gen_functions

"""
Script to calculate the periodicity score for a sequence of dates, and rank event terms accordingly 
"""
parser = argparse.ArgumentParser(description = "Script to calculate the periodicity score for a sequence of dates, and rank event terms accordingly")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")  
#parser.add_argument('-o', action = 'store', required = True, help = "The output file")
args = parser.parse_args() 

term_score = []
infile = open(args.i,"r",encoding="utf-8")
lines = infile.readlines()
infile.close()
for line in lines:
    tokens = line.strip().split("\t")
    # dates = [time_functions.return_datetime(x.split(",")[0],setting="vs") for x in tokens[1].split("|")]
    # if len(dates) > 2:
    #     intervals = calculations.return_intervals(dates)
    intervals = [int(x) for x in tokens[2].split(",")]
    if len(intervals) > 1:
        segmentation = calculations.return_segmentation(intervals)
#        calculations.find_outliers(intervals)
        score = calculations.return_relative_stdev(intervals)
        term_score.append([tokens[0],score,intervals])

quit()
term_score_sorted = sorted(term_score,key = lambda x : x[1])
# outfile = open(args.o,"w",encoding = "utf-8")
# for pair in term_score_sorted:
#     outfile.write("\t".join([str(x) for x in pair[:2]]) + "\t" + ",".join([str(y) for y in pair[2]]) + "\n")
# outfile.close
