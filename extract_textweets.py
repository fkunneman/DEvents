
import re
import datetime
from collections import defaultdict
import ucto
import sys
import time_functions

def extract_date(tweet,date):
    convert_nums = {"een":1, "twee":2, "drie":3, "vier":4,"vijf":5, "zes":6, "zeven":7, "acht":8, 
        "negen":9, "tien":10, "elf":11, "twaalf":12, "dertien":13,"veertien":14, "vijftien":15,
        "zestien":16, "zeventien":17,"achtien":18, "negentien":19, "twintig":20,"eenentwintig":21,
        "tweeentwintig":22,"drieentwintig":23,"vierentwintig":24,"vijfentwintig":25,
        "zesentwintig":26,"zevenentwintig":27,"achtentwintig":28,"negenentwintig":29,"dertig":30,
        "eenendertig":31}
    convert_month = {"jan":1, "januari":1, "feb":2, "februari":2,"mrt":3, "maart":3, "apr":4, 
        "april":4,"mei":5,"jun":6,"juni":6,"jul":7,"juli":7,"aug":8,"augustus":8,"sep":9,
        "september":9, "okt":10,"oktober":10, "nov":11,"november":11,"dec":12, "december":12}
    convert_timeunit = {"dagen":1, "daagjes":1, "dag":1,"dagje":1,"nachten":1,"nachtjes":1,"nacht":1,
        "nachtje":1,"weken":7,"weekjes":7,"week":7,"weekje":7,"maanden":30,"maandjes":30,"maand": 30,
        "maandje":30}
    weekdays=["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
    spec_days=["overmorgen"]

    nums = (r"(\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien|elf|twaalf|dertien|veertien|"
        "vijftien|zestien|zeventien|achtien|negentien|twintig|eenentwintig|tweeentwintig|"
        "drieentwintig|vierentwintig|vijfentwintig|zesentwintig|zevenentwintig|achtentwintig|"
        "negenentwintig|dertig|eenendertig)")
    months = (r"(jan|januari|feb|februari|mrt|maart|apr|april|mei|jun|juni|jul|juli|aug|augustus|"
        "sep|september|okt|oktober|nov|november|dec|december)")
    timeunits = (r"(dagen|daagjes|dag|dagje|nachten|nachtjes|nacht|nachtje|weken|weekjes|week|"
        "weekje|maanden|maandjes|maand|maandje)")

    list_patterns = ([r"(over|nog) (minimaal |maximaal |tenminste |bijna |ongeveer |maar |slechts |"
        "pakweg |ruim |krap |(maar )?een kleine |(maar )?iets (meer|minder) dan )?" + (nums) + " " + 
        (timeunits) + r"($| )", (nums) + " " + (timeunits) + r"( slapen)? tot",
        r"met( nog)? (minimaal |maximaal |tenminste |bijna |ongeveer |maar |slechts |pakweg |ruim |"
        "krap |(maar )?een kleine |(maar )?iets (meer|minder) dan )?" + (nums) + " " + (timeunits) + 
        r"( nog)? te gaan",r"(\b|^)" + (nums) + " " + (months) + r"( |$)" + r"(\d{4})?",
        r"(\b|^)(\d{1,2}-\d{1,2})(-\d{2,4})?(\b|$)",r"(\b|^)(\d{1,4}/\d{1,2})(/\d{1,4})?(\b|$)",
	r"(\b|$)(volgende week|komende|aankomende|deze) (maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)"
        r" ?(avond|nacht|ochtend|middag)?( |$)",r"(\b|$)(overmorgen) ?(avond|nacht|ochtend|middag)?( |$)"])

    date_eu = re.compile(r"(\d{1,2})-(\d{1,2})-?(\d{2,4})?")
    date_vs = re.compile(r"(\d{1,4})/(\d{1,2})/(\d{1,4})")
    date_vs2 = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2,4})")
    date_vs3 = re.compile(r"(\d{1,2})/(\d{1,2})")
    ns = convert_nums.keys()
    timeus = convert_timeunit.keys()
    ms = convert_month.keys()
    if re.findall('|'.join(list_patterns), tweet):
        #print tweet,re.findall('|'.join(list_patterns), tweet)
        timephrases = []
        matches = re.findall('|'.join(list_patterns), tweet)
        nud = defaultdict(list)
        for i,units in enumerate(matches):
            timephrases.append(" ".join([x for x in units if len(x) > 0 and not x == " "]))
            for unit in units:
#                print(unit)
                if unit in ns:
                    nud["num"].append((convert_nums[unit],i))
                elif unit in timeus:
                    if not "weekday" in nud:
                        nud["timeunit"].append((convert_timeunit[unit],i))
                elif unit in ms:
                    nud["month"].append((convert_month[unit],i))
                elif re.search(r"\d{1,2}-\d{1,2}",unit) or \
                    re.search(r"\d{1,2}/\d{1,2}",unit):
                    nud["date"].append((unit,i))
                    timephrases[i] = "".join([x for x in units if len(x) > 0 and not x == " "])
                elif re.search(r"-\d{2,4}",unit) or re.search(r"/\d{1,4}",unit):
                    nud["year"].append((unit,i))
                elif re.match(r"\d+",unit):
                    if int(unit) in range(2010,2020):
                        nud["year"].append((int(unit),i))
                    elif "num" in nud:
                        if int(unit) in range(1,13):
                            nud["month"].append((int(unit),i))
                        nud["num"].append((int(unit),i))
                    else:
                        nud["num"].append((int(unit),i))
                elif unit in weekdays:
                    nud["weekday"].append((unit,i))
                    if re.search(unit + r"(avond|middag|ochtend|nacht)",tweet):
                        timephrases[i] = "".join([x for x in units if len(x) > 0 and not x == " "])
                elif unit in spec_days:
                    nud["sday"].append((unit,i))
                elif unit == "volgende week":
                    nud["nweek"].append((unit,i))
            timephrases[i] = timephrases[i].replace("  "," ")
        regexPattern = '|'.join(map(re.escape, timephrases))
        tp = ', '.join(timephrases)
        output = [re.split(regexPattern, tweet),tp]
        if "timeunit" in nud:
            if not "month" in nud and not "date" in nud: #overrule by more specific time indication
                for t in nud["timeunit"]: 
                    num_match = t[1]
                    if "num" in nud:
                        days = t[0] * [x[0] for x in nud["num"] if x[1] == num_match][0]
                        try:
                            if days > 0:
                                output.append(date + datetime.timedelta(days=days))
                        except OverflowError:
                            continue
        if "month" in nud:
            for t in nud["month"]:
                num_match = t[1]
                m = t[0]
                try:
                    d = [x[0] for x in nud["num"] if x[1] == num_match][0]
                    if "year" in nud:
                        if num_match in [x[1] for x in nud["year"]]:
                            y = [x[0] for x in nud["year"] if x[1] == num_match][0]
                        else:
                            y = date.year
                    else:
                        y = date.year
                    if date < datetime.date(y,m,d):
                        output.append(datetime.date(y,m,d))
                except:
                    continue
        if "date" in nud:
            for da in nud["date"]:
                num_match = da[1]
                if re.search("-",da[0]):
                    if "year" in nud:
                        if num_match in [x[1] for x in nud["year"]]:
#                            print("da0",da[0],"nudyear",nud["year"],"nylist",[x for x in nud["year"]])
                            ds = date_eu.search(da[0] + [x[0] for x in nud["year"] if x[1] == \
                                num_match][0]).groups()
                        else:
                            ds = date_eu.search(da[0]).groups()
                    else:
                        ds = date_eu.search(da[0]).groups()
                    dsi = [int(x) for x in ds if x != None]
                    if dsi[1] in range(1,13) and \
                        dsi[0] in range(1,32):
                        try:
                            if ds[2] == None:
                                if date < datetime.date(date.year,dsi[1],dsi[0]):
                                        output.append(datetime.date(date.year,dsi[1],dsi[0]))
                            else:
                                if dsi[2] in range(2010,2020):
                                    if date < datetime.date(dsi[2],dsi[1],dsi[0]):
                                        output.append(datetime.date(dsi[2],dsi[1],dsi[0])) 
                        except:
                            continue
                elif re.search("/",da[0]):
                    if "year" in nud:
                        if num_match in [x[1] for x in nud["year"]]:
#                            print("da0",da[0],"nudyear",nud["year"],"nylist",[x for x in nud["year"]])
                            ds = date_vs.search(da[0] + [x[0] for x in nud["year"] if x[1] == \
                                num_match][0]).groups()
                        else:
                            ds = date_vs3.search(da[0]).groups()
                    else:
                        ds = date_vs3.search(da[0]).groups()
                    dsi = [int(x) for x in ds if x != None]
                    try:
                        if dsi[0] in range(1,32) and dsi[1] in range(1,13): #30/03/2015
                            outdate = False
                            if len(dsi) == 3:
                                if len(str(dsi[2])) == 4:
                                    outdate = datetime.date(dsi[2],dsi[1],dsi[0])
                                elif len(str(dsi[2])) == 2:
                                    if dsi[2] in range(10,21):
                                        outdate = datetime.date((dsi[2]+2000),dsi[1],dsi[0])
                            else:
                                outdate = datetime.date(date.year,dsi[1],dsi[0])
                            if outdate:
                                if date < outdate:
                                    output.append(outdate)
                        elif dsi[0] in range(1,13) and dsi[1] in range(1,32): #30/03
                            if date < datetime.date(date.year,dsi[0],dsi[1]):
                                output.append(datetime.date(date.year,dsi[0],dsi[1]))
                        elif dsi[0] in range(2010,2020): #2015/03/30
                            if dsi[1] in range(1,13) and dsi[2] in range(1,32):
                                if date < datetime.date(dsi[0],dsi[1],dsi[2]):
                                    output.append(datetime.date(dsi[0],dsi[1],dsi[2]))
                    except:
                        continue
        if "weekday" in nud:
            if not "date" in nud and not "month" in nud and not "timeunit" in nud: # overrule by more specific indication
#                ptags = return_postags(tweet,f,wws = True)
#                past = False
#                for tag in ptags:
#                    if re.search(r"^WW\(vd",tag[1]) or re.search(r"^WW\(pv,verl",tag[1]):
#                        past = True
#                if not past:
                tweet_weekday=date.weekday()
                for w in nud["weekday"]:
                    num_match = w[1]
                    ref_weekday=weekdays.index(w[0])
                    if num_match in [x[1] for x in nud["nweek"]]:
                        add = 7
                    else:
                        add = 0
                    if not ref_weekday == tweet_weekday and not num_match in [x[1] for x in nud["nweek"]]: 
                        if tweet_weekday < ref_weekday:
                            days_ahead = ref_weekday - tweet_weekday + add
                        else:
                            days_ahead = ref_weekday + (7-tweet_weekday) + add
                        output.append(date + datetime.timedelta(days=days_ahead))
        if "sday" in nud:
            for s in nud["sday"]:
                num_match = s[1] 
                timephrase = " ".join([x for x in matches[num_match] if len(x) > 0])
                u = s[0]
                if u == "overmorgen":
                    output.append(date + datetime.timedelta(days=2))
        if len(nud.keys()) == 0:
            return False
        else:
            return output

print(sys.argv[1])
print(datetime.datetime.now())

infile = open(sys.argv[1],encoding="utf-8")
tweets = infile.readlines()
infile.close()
outfile = open(sys.argv[2],"a",encoding="utf-8")
tokenizer = ucto.Tokenizer("/vol/customopt/uvt-ru/etc/ucto/tokconfig-nl-twitter")
for tweet in tweets[1:]:
    tokens = tweet.strip().split("\t")
    if not re.search(r"\bRT\b",tokens[-1]):
        tokenizer.process(tokens[-1])
        text = " ".join([x.text.lower() for x in tokenizer])
        try:
            date = time_functions.return_datetime(tokens[2],setting="vs").date()
        except:
            print("dateerror",tweet,tokens)
            quit()
        dateref_phrase = extract_date(text,date)
        if dateref_phrase:
            if len(dateref_phrase) > 2:
                chunks = dateref_phrase[0]
                datephrase = dateref_phrase[1] 
                refdates = dateref_phrase[2:]
                units = [tokens[1],tokens[6],str(date),text," ".join([str(x) for x in refdates]),"|".join([x for x in chunks]),datephrase]
                outfile.write("\t".join(units) + "\n")

print(datetime.datetime.now())

