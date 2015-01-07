
from __future__ import division
import sys
import codecs

heideltagging = codecs.open(sys.argv[1],"r","utf-8")
ruletagging = codecs.open(sys.argv[2],"r","utf-8")
total_amount_tweets = int(sys.argv[3])
statfile = open(sys.argv[4],"w")
intersectout = codecs.open(sys.argv[5],"w","utf-8")
unique_heidelout = codecs.open(sys.argv[6],"w","utf-8")
unique_ruleout = codecs.open(sys.argv[7],"w","utf-8")

#extract id-info list heideltagging
heidelds = []
heidelinfo = []
for line in heideltagging.readlines():
    tokens = line.strip().split("\t")
    tex = tokens[1].split(",")[0]
    heidelinfo.append((tokens[0],tex))
    heidelds.append(tokens[0])
heideltagging.close()

#extract id-info list ruletagging
ruleds = []
ruleinfo = []
for line in ruletagging.readlines():
    tokens = line.strip().split("\t")
    ruleinfo.append((tokens[0],tokens[3] + ", " + tokens[4])) 
    ruleds.append(tokens[0])
ruletagging.close()

#generate intersect and 2 unique lists
intersect = list(set(heidelds).intersection(ruleds))
unique_heidel = list(set(heidelds) - set(ruleds))
unique_ruleds = list(set(ruleds) - set(heidelds))
union = intersect + unique_heidel + unique_ruleds

#calculate statistics
statfile.write("num timetweets heidel: " + str(len(heidelds)) + " (" + str((len(heidelds) / total_amount_tweets) * 100) + "%)\n")
statfile.write("num timetweets rules: " + str(len(ruleds)) + " (" + str((len(ruleds) / total_amount_tweets) * 100) + "%)\n")
statfile.write("num timetweets intersect: " + str(len(intersect)) + " (" + str((len(intersect) / total_amount_tweets) * 100) + "%)\n")
statfile.write("num timetweets union: " + str(len(union)) + " (" + str((len(union) / total_amount_tweets) * 100) + "%)\n")

#write_files
intersect_tweets = []
for d in intersect:
    intersect_tweets.append(([x[1] for x in heidelinfo if x[0] == d][0],[x[1] for x in ruleinfo if x[0] == d]))=
for tweet in intersect_tweets:
    intersectout.write("\t".join(tweet) + "\n")

unique_heidelout.write("\n".join([x[1] for x in heidelinfo if x[0] in unique_heidel]))
unique_ruleout.write("\n".join([x[1] for x in ruleinfo if x[0] in unique_ruleds]))
