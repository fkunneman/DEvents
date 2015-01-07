
import sys
import codecs
import re
import datetime

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

datesearch_value = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
datesearch_value2 = re.compile(r"(\d{1,2})-(\d{1,2})")
datesearch = re.compile(r"tagged_(\d{4})(\d{2})(\d{2})")
filedateinfo = datesearch.search(sys.argv[1]).groups()
filedate = datetime.date(int(filedateinfo[0]),int(filedateinfo[1]),int(filedateinfo[2]))

lines = infile.readlines()
infile.close()

for i,line in enumerate(lines):
    if re.match(r"^#tweet_id",line):
        start = i + 1
        break

for i,line in enumerate(lines[start:]):
    tokens = line.strip().split("\t")
    tweet_id = tokens[0]
    s=1
    if re.search("TIMEX3",tweet_id):
        s=2
        tweet_id = tweet_id.split(">")[1] 
    if len(tokens) <= 1:
        continue
    if re.match(r"</TimeML>",tweet_id):
        break
    text = tokens[1]
    if re.search("TIMEX3",text):
        textparts = text.split("<")
        texs = []
        for timetag in range(s,len(textparts),2):
            parts = textparts[timetag].split(">")
            tex = parts[1]
            tag = parts[0]
#            print "index",i+start,"tokens",tokens,"text",text,"textparts",textparts,"parts",parts,"tag",tag
            if re.search("<TIMEX3",text):
                value = tag.split("value=")[1]
                if re.search("type=\"DATE\"",tag):
                    if datevalue6.search(value) and not (re.search(r"gisteren",tex.lower()) or re.search(r"vandaag",tex.lower()) or re.search(r"morgen",tex.lower())):
                        datevaluefields = datesearch_value.search(value).groups()
                        try:
                            datevalue = datetime.date(int(datevaluefields[0]),int(datevaluefields[1]),int(datevaluefields[2]))
                            if filedate < datevalue:
                                texs.append((tex,value))
                        except:
                            continue
                    elif datevalue3.search(value):
                        datevaluefields = datesearch_value2.search(value).groups()
                        try:
                            datevalue = datetime.date(2014,int(datevaluefields[0]),int(datevaluefields[1]))
                            if filedate < datevalue:
                                texs.append((tex,value))
                        except:
                            continue
                    elif datevalue1.search(value) or datevalue2.search(value) or datevalue4.search(value) or datevalue5.search(value):
                        texs.append((tex,value))
                elif re.search("type=\"TIME\"",tag):
                    if timevalue1.search(value):
                        texs.append((tex,value))
                elif re.search("type=\"SET\"",tag):
                    if (setvalue1.search(value) and not re.search("quant",tag) and lax) or setvalue2.search(value):
                        texs.append((tex,value))
            if len(texs) > 0:
                outfile.write(tweet_id + "\t" + " | ".join([",".join(list(x)) for x in texs]) + "\n")


