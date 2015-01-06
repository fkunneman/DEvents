
import sys
import codecs
import re

infile = codecs.open(sys.argv[1],"r","utf-8")
outfile = codecs.open(sys.argv[2],"a","utf-8")
try:
    lax = int(sys.argv[3])
except:
    print "last argument should be integer"

datevalue1 = re.compile(r"UNDEF-day-")
datevalue2 = re.compile(r"UNDEF-this-week-WE")
datevalue3 = re.compile(r"UNDEF-year-\d{1,2}-\d{1,2}")
datevalue4 = re.compile(r"UNDEF-next-(week|month|year)")
datevalue5 = re.compile(r"UNDEF-century\d{2}-\d{2}-\d{2}")
datevalue6 = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
timevalue1 = re.compile(r"UNDEF-day-")
setvalue1 = re.compile(r"P\d(W|D|M|Y|WE)")
setvalue2 = re.compile(r"XXXX-WXX-\dT(EV|MO|AF|NI)")

lines = infile.readlines()
infile.close()

for i,line in enumerate(lines):
    if re.match(r"^#tweet_id",line):
        start = i + 1
        break

for line in lines[start:]:
    if re.search("<",line) and re.search(">",line):
        tokens = line.strip().split("\t")
        if re.match(r"</TimeML>",tokens[0]):
            break
        tweet_id = tokens[0]
        text = tokens[1]
        textparts = text.split("<")
        texs = []
        for timetag in range(1,len(textparts),2):
            parts = textparts[timetag].split(">")
            tex = parts[1]
            tag = parts[0]
            value = tag.split("value=")[1]
            if re.search("type=\"DATE\"",tag):
                if datevalue1.search(value) or datevalue2.search(value) or datevalue3.search(value) or datevalue4.search(value) or datevalue5.search(value) or datevalue6.search(value):
                    texs.append((tex,value))
            elif re.search("type=\"TIME\"",tag):
                if timevalue1.search(value):
                    texs.append((tex,value))
            elif re.search("type=\"SET\"",tag):
                if (setvalue1.search(value) and not re.search("quant",tag)) or setvalue2.search(value):
                    texs.append((tex,value))
        if len(texs) > 0:
            outfile.write(tweet_id + "\t" + " ".join([",".join(list(x)) for x in texs]) + "\n")


