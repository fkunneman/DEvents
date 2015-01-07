
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

print("extracting ids heidel")
#extract id-info list heideltagging
heidelds = []
heidelinfo = []
heideldict = {}
for line in heideltagging.readlines():
    tokens = line.strip().split("\t")
    tex = tokens[1].split(",")[0]
    heidelinfo.append((tokens[0],tex))
    heidelds.append(tokens[0])
    heideldict[tokens[0]] = tex
heideltagging.close()

print("extracting ids rules")
#extract id-info list ruletagging
ruleds = []
ruleinfo = []
ruledict = {}
for line in ruletagging.readlines():
    tokens = line.strip().split("\t")
    ruleinfo.append((tokens[0],tokens[3] + ", " + tokens[4])) 
    ruleds.append(tokens[0])
    ruledict[tokens[0]] = tokens[3] + ", " + tokens[4]
ruletagging.close()

print("making intersection, unique and union lists")
print("len set heidelds",len(list(set(heidelds))),"len set ruleds",len(list(set(ruleds))))
#generate intersect and 2 unique lists
unique_heidel = list(set(heidelds) - set(ruleds))
intersect = list(set(heidelds) & set(ruleds))
unique_ruleds = list(set(ruleds) - set(heidelds))
union = intersect + unique_heidel + unique_ruleds

print("heidelds",len(heidelds),"ruleds",len(ruleds),"intersect",len(intersect),"unique heidel",len(unique_heidel),"unique_rules",len(unique_ruleds),"union",len(union))

print("calculation statistics")
#calculate statistics
statfile.write("num timetweets heidel: " + str(len(heidelds)) + " (" + str((len(heidelds) / total_amount_tweets) * 100) + "%)\n")
statfile.write("num timetweets rules: " + str(len(ruleds)) + " (" + str((len(ruleds) / total_amount_tweets) * 100) + "%)\n")
statfile.write("num timetweets intersect: " + str(len(intersect)) + " (" + str((len(intersect) / total_amount_tweets) * 100) + "%)\n")
statfile.write("num timetweets union: " + str(len(union)) + " (" + str((len(union) / total_amount_tweets) * 100) + "%)\n")
statfile.close()

print("writing tweetfiles")
#write_files
print("intersect file")
intersect_tweets = []
for d in intersect:
    intersect_tweets.append((heideldict[d],ruledict[d]))
for tweet in intersect_tweets:
    intersectout.write("\t".join(tweet) + "\n")

print("heidelfile")
for d in unique_heidel:
    unique_heidelout.write(heideldict[d] + "\n")
print("rulefile")
for d in unique_ruleds:
    unique_ruleout.write(ruledict[d] + "\n")
