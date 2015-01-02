
import sys
import codecs

#parse qualtrics files
qualtrics_csx = codecs.open(sys.argv[1],"r","utf-8")
qualtrics_cs = codecs.open(sys.argv[2],"r","utf-8")
qualtrics_ngram = codecs.open(sys.argv[3],"r","utf-8")

qualtrics_csx_str = qualtrics_csx.read()
qualtrics_cs_str = qualtrics_cs.read()
qualtrics_ngram_str = qualtrics_ngram.read()

qualtrics_csx.close()
qualtrics_cs.close()
qualtrics_ngram.close()

cs_events = []
ngram_events = []

csx = qualtrics_csx_str.split("[[Question:MC:SingleAnswer:Vertical]]")[1:501]
cs = qualtrics_cs_str.split("[[Question:MC:SingleAnswer:Vertical]]")[1:501]
ngram = qualtrics_ngram_str.split("[[Question:MC:SingleAnswer:Vertical]]")[1:501]
for event in range(0,500,2):
    events_dict = {}
    tweets_csx = csx[event].split("<br />\n\t\t\t<br />\n\t\t\t")
    tweet_csx1 = tweets_csx[0].split("<b>")[-1]
    tweets_csxfinal = [tweet_csx1] + tweets_csx[1:-1]
    events_dict["tweets"] = tweets_csxfinal
    terms_csx = [x.split("<b>")[-1] for x in csx[event+1].split("</b>")[:-1]]
    events_dict["terms+"] = terms_csx
    terms_cs = [x.split("<b>")[-1] for x in cs[event+1].split("</b>")[:-1]]
    events_dict["terms"] = terms_cs
    cs_events.append(events_dict)
    ngram_dict = {}
    tweets_ngram = ngram[event].split("<br />\n\t\t\t<br />\n\t\t\t")
    tweet_ngram1 = tweets_ngram[0].split("<b>")[-1]
    tweets_ngramfinal = [tweet_ngram1] + tweets_ngram[1:-1]
    ngram_dict["tweets"] = tweets_ngramfinal
    terms_ngram = [x.split("<b>")[-1] for x in ngram[event+1].split("</b>")[:-1]]
    ngram_dict["terms"] = terms_ngram
    ngram_events.append(ngram_dict)

#add human assessments
annotations_cs_csx = open(sys.argv[4])
annotations_ngram = open(sys.argv[5])

lines_cs_csx = annotations_cs_csx.readlines()
lines_ngram = annotations_ngram.readlines()

annotations_ngram.close()
annotations_cs_csx.close()

for i,line in enumerate(lines_cs_csx):
    event = cs_events[i]
    ass = line.strip().split("\t")
    if ass.count('1') == 4:
        event["assessment"] = "event"
    if ass.count('1') == 3:
        event["assessment"] = "75"
    if ass.count('1') == 2:
        event["assessment"] = "50"
    if ass.count('1') == 1:
        event["assessment"] = "25"
    if ass.count('1') == 0:
        event["assessment"] = "no_event"
for i,line in enumerate(lines_ngram):
    event = ngram_events[i]
    ass = line.strip().split("\t")
    if ass.count('1') == 2:
        event["assessment"] = "event"
    if ass.count('1') == 1:
        event["assessment"] = "50"
    if ass.count('1') == 0:
        event["assessment"] = "no_event"

terms_cs = open(sys.argv[6])
terms_csx = open(sys.argv[7])
terms_ngram = open(sys.argv[8])

lines_cs = terms_cs.readlines()
lines_csx = terms_csx.readlines()
lines_ngram = terms_ngram.readlines()

terms_cs.close()
terms_csx.close()
terms_ngram.close()

print len(lines_cs),len(lines_csx),len(lines_ngram)
for i,line in enumerate(lines_cs):
    event = cs_events[i]
    ass = line.strip().split("\t")
    if ass.count('3') == 2 or ass.count('3') == 1 and "miss" in ass:
        event["termassess_cs"] = "GOOD"
    elif ass.count('1') == 2 or ass.count('1') == 1 and "miss" in ass:
        event["termassess_cs"] = "BAD"
    elif ass.count('2') == 2 or ass.count('2') == 1 and "miss" in ass:
        event["termassess_cs"] = "MED"
    elif ass.count('miss') == 2:
        event["termassess_cs"] = "MISS"
    else:
        event["termassess_cs"] = "MIXED"

for i,line in enumerate(lines_csx):
    event = cs_events[i]
    ass = line.strip().split("\t")
    if ass.count('3') == 2 or ass.count('3') == 1 and "miss" in ass:
        event["termassess_csx"] = "GOOD"
    elif ass.count('1') == 2 or ass.count('1') == 1 and "miss" in ass:
        event["termassess_csx"] = "BAD"
    elif ass.count('2') == 2 or ass.count('2') == 1 and "miss" in ass:
        event["termassess_csx"] = "MED"
    elif ass.count('miss') == 2:
        event["termassess_csx"] = "MISS"
    else:
        event["termassess_csx"] = "MIXED"

for i,line in enumerate(lines_ngram):
    event = ngram_events[i]
    ass = line.strip().split("\t")
    if ass.count('3') == 2 or ass.count('3') == 1 and "miss" in ass:
        event["termassess"] = "GOOD"
    elif ass.count('1') == 2 or ass.count('1') == 1 and "miss" in ass:
        event["termassess"] = "BAD"
    elif ass.count('2') == 2 or ass.count('2') == 1 and "miss" in ass:
        event["termassess"] = "MED"
    elif ass.count('miss') == 2:
        event["termassess"] = "MISS"
    else:
        event["termassess"] = "MIXED"

#write to file
cs_csx_out = codecs.open(sys.argv[9],"w","utf-8")
ngram_out = codecs.open(sys.argv[10],"w","utf-8")

for i,event in enumerate(cs_events):
    cs_csx_out.write('\t'.join([str(i),"LINEBREAK".join(event["tweets"]),event["assessment"],",".join(event["terms"]),",".join(event["terms+"]),event["termassess_cs"],event["termassess_csx"]]) + "\n")
for i,event in enumerate(ngram_events):
    ngram_out.write('\t'.join([str(i),"LINEBREAK".join(event["tweets"]),event["assessment"],",".join(event["terms"]),event["termassess"]]) + "\n")

cs_csx_out.close()
ngram_out.close()


