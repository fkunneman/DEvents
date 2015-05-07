#!/usr/bin/env 

import argparse
from collections import defaultdict
import re
from random import shuffle
import numpy

"""
Programme to evaluate a file with periodicity output
"""
parser = argparse.ArgumentParser(
    description = "Programme to evaluate a file with periodicity output")
parser.add_argument('-i', action = 'store', required = True, help = "The input file")
parser.add_argument('-t', action = 'store', required = True, help = "The file with tweets")
parser.add_argument('-d', action = 'store', required = False, 
    help = "The file with dates (for calendar periodicity output)")
parser.add_argument('-o', action = 'store', required = True, help = "The output dir")
parser.add_argument('-a', action = 'store', type = int, required = True, 
    help = "The column with the assessment")
parser.add_argument('-s', action = 'store', type = int, required = True, 
    help = "The column with the score")
parser.add_argument('-e', action = 'store', type = int, required = True, 
    help = "The column with the entities")
parser.add_argument('-p', action = 'store', type = int, required = True, 
    help = "The columns with the pattern information")
parser.add_argument('-m', action = 'store', type = int, required = True, 
    help = "The column with comments")
parser.add_argument('-k', action = 'store_true', 
    help = "choose to categorize periodics into calendar characteristics (only applies if the " +
        "output is based on calendar periodicity")
parser.add_argument('--st', action = 'store_true', 
    help = "choose to categorize periodics into timeline characteristics (only applies if the " +
        "output is based on timeline periodicity")
parser.add_argument('-w', action = 'store_true', 
    help = "choose to extract word statistics of periodics")

args = parser.parse_args() 

#read in file
print("Reading in assessment file")
assessments_periodics = defaultdict(int)
score_periodics = defaultdict(list)
all_periodics = []
n_periodics = 0
infile = open(args.i,"r",encoding="utf-8")
for line in infile.readlines()[1:]:
    columns = line.strip().split("\t")
    assessment = columns[args.a]
    #print(columns[args.s])
    score = float(columns[args.s])
    entities = columns[args.e].split(", ") 
    #pattern = [column[i] for i in args.p]
    pattern = columns[args.p]
    periodic = [entities,assessment,score,pattern]
    assessments_periodics[assessment] += 1
    score_periodics[score].append(periodic)
    if len(columns) > args.m:
        if columns[args.m] == "Dubbel" or columns[args.m] == "dubbel":
            assessments_periodics["Dubbel"] += 1 
            periodic.append("dubbel")
    all_periodics.append(periodic)
    n_periodics += 1

if args.d: #link dates to terms
    print("Reading in periodics file")
    term_pattern_dates = defaultdict(lambda : defaultdict(list))
    datefile = open(args.d,"r",encoding="utf-8")
    for line in datefile.readlines():
        if line[0] == "<":
            tokens = line.strip().split("\t")
            pattern = tokens[0]
            terms = tokens[1].split(", ")
            dates = tokens[3].split(" > ")
            for term in terms:
                term_pattern_dates[term][pattern] = dates

#read in tweets
print("Reading in event file")
term_date_tweets = defaultdict(lambda : defaultdict(list))
tweetsfile = open(args.t,"r",encoding="utf-8")
for line in tweetsfile.readlines():
    tokens = line.split("\t")
    date = tokens[0]
    terms = tokens[2].split(", ")
    ids = tokens[3].split(", ")
    tweets = tokens[4].split("-----")
    for term in terms:
        term_date_tweets[term][date] = tweets

#calculate general results
print("writing results")
resultsout = open(args.o + "results.txt","w",encoding="utf-8")
for assessment in sorted(assessments_periodics.keys()):
    num_as = assessments_periodics[assessment]
    resultsout.write(assessment + ": " + str(num_as) + "/" + str(n_periodics) + " (" + \
        str(num_as/n_periodics) + ")\n")
resultsout.close()

#make precision-at-plot
print("Plotting precision at")
plot_raw = open(args.o + "prat.txt","w",encoding="utf-8")
if args.k:
    scores = sorted(score_periodics.keys(),reverse=True)
else:
    scores = sorted(score_periodics.keys())
periodics_assessment = [0,0]
for score in scores:
    periodics = score_periodics[score]
    shuffle(periodics)
    for periodic in periodics:
        periodics_assessment[0] += 1
        if periodic[1] == "1.0":
            periodics_assessment[1] += 1
        #periodics_assessment[1] += len([x for x in periodics if x[1] == "1.0"])
        plot_raw.write(str(periodics_assessment[0]) + "\t" + str(periodics_assessment[1] / periodics_assessment[0]) + "\n")
plot_raw.close()

if args.w:
    print("writing all periodic tweets")
    #link correct events to tweets and calculate word statistics
    outfile = open(args.o + "periodic_event_tweets.txt","w",encoding="utf-8")
    #iterate through sorted periodics
    for score in scores:
        periodics = score_periodics[score]
        for periodic in periodics:
            if periodic[1] == "1.0":
                terms = periodic[0]
                pattern = periodic[3]
                date_tweets = defaultdict(list)
                for term in terms:
                    dates = term_pattern_dates[term][pattern]
                    for date in dates:
                        date_tweets[date].extend(term_date_tweets[term][date])
                outfile.write("----------\n" + pattern + "\t" + ", ".join(terms) + "\n")
                for date in sorted(date_tweets.keys()):
                    outfile.write("*******\n" + date + "\n")
                    tweets = list(set(date_tweets[date]))
                    outfile.write("\n".join([t for t in tweets if not t == "\n"]) + "\n")
    outfile.close()

def count_calendarfeat(d,i):
 #   print("cat",i,d[0][3],d[0][3].split(",")[i])
    periodics_cat = [p for p in d if re.search(r"\d",p[3].split(",")[i])]
    non_periodics_cat = [p for p in d if re.search(r"v",p[3].split(",")[i])]
#    print("per",len(periodics_cat),"non per",len(non_periodics_cat))
    cat_periodics = defaultdict(list)
    for pc in periodics_cat:
        cat = pc[3].split(",")[i]
        cat_periodics[cat].append(pc)
    return [cat_periodics,periodics_cat]

if args.st:
    print("Extracting statistics")
    statfile = open(args.o + "stats_tl.txt","w",encoding="utf-8")
    periodics = [p for p in all_periodics if p[1] == "1.0"]
    intervals = []
    for p in periodics:
        ints = [int(x) for x in p[3].split("-")]
        steps = [(x,ints.count(x)) for x in list(set(ints))]
        sorted_steps = sorted(steps,key = lambda k : k[1],reverse=True)
        shuffle(sorted_steps)
        if not sorted_steps[0][0] == 1:
            step = sorted_steps[0][0]
        else:
            step = sorted_steps[1][0]
        intervals.append(step)
    print(intervals)
    average = numpy.mean(intervals)
    stdev = numpy.std(intervals)
    median = numpy.median(intervals)
    statfile.write(str(average) + " " + str(stdev) + "\n" + str(median) + "\n\n")
    for interval in sorted(list(set(intervals))):
        statfile.write(str(interval) + " " + str(intervals.count(interval)) + "\n")
    statfile.close()

if args.k:
    print("Extracting full periodics")
    #make raw files for plots based on different pattern features
    periodics = [p for p in all_periodics if p[1] == "1.0"]
    print("periodics",len(periodics))
    #remove doubles
    #double_periodics = [p for p in all_periodics if p[-1] == "dubbel"]
    #double_entities = []
    #for dp in double_periodics:
    #    double_entities.extend(dp[0])
    #filtered_periodics = []
    #for p in periodics:
    #    double = False
    #    for c in p[0]:
    #       if c in double_entities: #possible candidates
    #           double = True
    #    if not double:
    #        filtered_periodics.append(p)
    #print(len(periodics),"confirmed periodics, ",len(double_periodics),"double periodics, ",
    #   len(filtered_periodics),"final periodics")
    #filtered_periodics_patternlists = []
    #for p in periodics:
    #    p[3] = p[3][1:-1].split(",")
    filtered_periodics_patternlists = [p for p in periodics if p[-1] != "dubbel"]
    print("fpp",len(filtered_periodics_patternlists))
    #weekdays
    print("Plotting weekdays")
    weekday_plot = open(args.o + "weekday_plot_raw.txt","w",encoding="utf-8")
    wd_dict = {"0":"Monday", "1":"Tuesday", "2":"Wednesday", "3":"Thursday", "4":"Friday", 
        "5":"Saturday", "6":"Sunday"}
    weekday_periodics = count_calendarfeat(filtered_periodics_patternlists,4)
    num_periodics = len(weekday_periodics[1])
    for weekday in sorted(weekday_periodics[0].keys()):
#        print(num_periodics,weekday)
        weekday_plot.write(wd_dict[weekday] + "\t" + \
            str(len(weekday_periodics[0][weekday]) / num_periodics) + "\n")
    weekday_plot.close()
    #monthdays
    print("Plotting monthdays")
    monthday_plot = open(args.o + "monthday_plot_raw.txt","w",encoding="utf-8")
    monthday_periodics = count_calendarfeat(filtered_periodics_patternlists,3)
    num_periodics = len(monthday_periodics[1])
    last = 0
    for monthday in sorted([int(x) for x in monthday_periodics[0].keys()]):
        while monthday - last > 1:
            last += 1
            monthday_plot.write(str(last) + "\t0.0\n")
        monthday = str(monthday)
        monthday_plot.write(monthday + "\t" + 
            str(len(monthday_periodics[0][monthday]) / num_periodics) + "\n")
        last += 1
    monthday_plot.close()
    print("enlisting date periodics")
    date_file = open(args.o + "date_periodics.txt","w",encoding="utf-8")
    date_periodics = []
    monthday_periodics_all = count_calendarfeat(periodics,3)
    for m in monthday_periodics_all[0].keys():
        date_periodics.extend([x for x in monthday_periodics_all[0][m] if \
        re.search(r"\d",x[3].split(",")[1])])
    sorted_date_periodics = sorted(date_periodics,key = lambda k : k[2],reverse = True)
    for dp in sorted_date_periodics:
        date_file.write("\t".join([str(x) for x in dp]) + "\n")
    date_file.close()
    #months
    print("Plotting months")
    month_plot = open(args.o + "month_plot_raw.txt","w",encoding="utf-8")
    month_dict = {"1":"January", "2":"February", "3":"March", "4":"April", "5":"May", "6":"June", 
        "7":"July", "8":"August", "9":"September", "10":"October", "11":"November", 
        "12":"December"}
    month_periodics = count_calendarfeat(filtered_periodics_patternlists,1)
    num_periodics = len(month_periodics[1])
    for month in sorted(month_periodics[0].keys()):
        month_plot.write(month_dict[month] + "\t" + \
            str(len(month_periodics[0][month]) / num_periodics) + "\n")
    month_plot.close()
    #weeks
    print("Plotting weeks")
    week_plot = open(args.o + "week_plot_raw.txt","w",encoding="utf-8")
    week_periodics = count_calendarfeat(filtered_periodics_patternlists,2) 
    num_periodics = len(week_periodics[1])
    last = 0
    for week in sorted([int(x) for x in week_periodics[0].keys()]):
        while week - last > 1:
            last += 1
            week_plot.write(str(last) + "\t0.0\n")
        week = str(week)
        week_plot.write(week + "\t" + \
            str(len(week_periodics[0][week]) / num_periodics) + "\n")
        last += 1
    week_plot.close()
    print("Enlisting week periodics")
    week_file = open(args.o + "week_periodics.txt","w",encoding="utf-8")
    week_periodics_all = count_calendarfeat(periodics,2)     
    week_periodics_el = []
    for w in week_periodics_all[0].keys():
        week_periodics_el.extend(week_periodics_all[0][w])
    sorted_week_periodics = sorted(week_periodics_el,key = lambda k : k[2],reverse = True)
    for wp in sorted_week_periodics:
        week_file.write("\t".join([str(x) for x in wp]) + "\n")
    week_file.close()
    # #weekday-weekday
    print("Plotting weekday index")
    weekday_index_plot = open(args.o + "weeday_index_plot_raw.txt","w",encoding="utf-8")
    periodics_index = [p for p in filtered_periodics_patternlists if re.search(r"\d",p[3].split(",")[5][0])]
    periodics_index_all = [p for p in periodics if re.search(r"\d",p[3].split(",")[5][0])]
    weekday_index_periodics = defaultdict(lambda : defaultdict(list))
    for pi in periodics_index:
        index = pi[3].split(",")[5][:-1]
#        print(pi,index)
        weekday = pi[3].split(",")[4]
        weekday_index_periodics[index][weekday].append(pi)
    for weekday in sorted(weekday_index_periodics.keys()):
        last = -1
        for index in sorted(weekday_index_periodics[weekday].keys()):
            while int(index) - last > 1:
                last += 1
                weekday_index_plot.write(wd_dict[weekday] + "_" + str(last) + "\t0.0\n")
            weekday_index_plot.write(wd_dict[weekday] + "-" + index + "\t" + \
                str(len(weekday_index_periodics[weekday][index]) / len(periodics_index)) + "\n")
    weekday_index_plot.close()
    print("enlisting weekday index periodics")
    weekday_index_file = open(args.o + "weekday_index_periodics.txt","w",encoding="utf-8")
    weekday_index_month = [p for p in periodics_index_all if p[3][1] == "e"]
    sorted_weekday_index_periodics = sorted(weekday_index_month,key = lambda k : k[2],reverse = True)
    for wip in sorted_weekday_index_periodics:
        weekday_index_file.write("\t".join([str(x) for x in wip]) + "\n")
    weekday_index_file.close()
    #weeksequence
    print("enlisting weeksequence periodics")
    weeksequence_file = open(args.o + "weeksequence_periodics.txt","w",encoding="utf-8")
    weeksequence_periodics = [p for p in periodics if p[3].split(",")[2] == "e"]
    sorted_weeksequence_periodics = sorted(weeksequence_periodics,key = lambda k : k[2],reverse = True)
    for wsp in sorted_weeksequence_periodics:
        weeksequence_file.write("\t".join([str(x) for x in wsp]) + "\n")
    weeksequence_file.close()    
    #monthsequence
    print("enlisting monthsequence periodics")
    monthsequence_file = open(args.o + "monthsequence_periodics.txt","w",encoding="utf-8")
    monthsequence_periodics = [p for p in periodics if p[3].split(",")[1] == "e"]
    sorted_monthsequence_periodics = sorted(monthsequence_periodics,key = lambda k : k[2],reverse = True)
    for msp in sorted_monthsequence_periodics:
        monthsequence_file.write("\t".join([str(x) for x in msp]) + "\n")
    monthsequence_file.close() 
