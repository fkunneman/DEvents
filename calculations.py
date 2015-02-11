
from __future__ import division
import math
import itertools
import numpy
import re
import os
import datetime
from collections import defaultdict

def goodness_of_fit(total,dc,ec,ode):
    g2 = 0
    ede = (dc * ec) / total
    if ode > 0 and ede > 0:
        g2 += ode * (math.log(ode/ede)/math.log(2))
    odne = dc - ode
    edne = (dc * (total-ec)) / total
    if edne > 0 and odne > 0:
        g2 += odne * (math.log(odne/edne)/math.log(2))
    onde = ec - ode
    ende = (ec * (total-dc)) / total
    if onde > 0 and ende > 0:
        g2 += onde * (math.log(onde/ende)/math.log(2))
    ondne = total - (ode+odne+onde) 
    endne = ((total-dc) * (total-ec)) / total
    if ondne > 0 and endne > 0:
        g2 += ondne * (math.log(ondne/endne)/math.log(2))
    return g2

def return_postags(text,f,wws=False):
    output = []
    adj = re.compile(r"^ADJ\(")
    n = re.compile(r"^N\(")
    ww = re.compile(r"^WW\(")
    data = f.process(text)
    for token in data:
        pos = token["pos"]
        if ww.search(pos):
            output.append((token["text"],token["pos"]))
        if (adj.search(pos) or n.search(pos)) and not wws:
            output.append((token["text"],token["pos"]))
    return output

def return_cities(chunks,cl):
    remove_chunk = []
    new_chunks = []
    for i,chunk in enumerate(chunks):
        pt = [x.replace(" ","_") for x in re.findall(cl,chunk)]
        cts = [x for x in pt if not x == ""]
        if len(cts) > 0:
            regexPattern = '|'.join(map(re.escape, cts))
            new_chunks.extend(re.split(regexPattern,chunk))
            remove_chunk.append(i)
    if len(remove_chunk) > 0:
        for i,e in enumerate(remove_chunk):
            del chunks[e-i]
        chunks.extend(new_chunks)
    return(chunks,cts)

def decide_year(tdate,month,day):
    d1 = datetime.date(tdate.year,month,day)
    d2 = datetime.date(tdate.year+1,month,day)
    d3 = datetime.date(tdate.year-1,month,day)
    dif1 = (tdate-d1).days
    if dif1 < 0:
        dif1 = (dif1 * -1)
    dif2 = (tdate-d2).days
    if dif2<0:
        dif2 = dif2*-1
    dif3 = (tdate-d3).days
    if dif3<0:
        dif3 = dif3*-1
    if dif1 < dif2 and dif1 < dif3:
        return d1.year
    elif dif2 < dif3:
        return d2.year
    else:
        return d3.year

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
        r"(\b|^)(\d{1,2}-\d{1,2})(-\d{2,4})?(\b|$)",
        r"(\b|^)(\d{4}-)(\d{1,2}-\d{1,2})(\b|$)",
        r"(\b|^)(\d{1,2}/\d{1,2})(/\d{2,4})?(\b|$)",
        r"(\b|^)(\d{4}/)(\d{1,2}/\d{1,2})(\b|$)",
        r"(volgende week|komende|aankomende|deze) (maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)"
        r" ?(avond|nacht|ochtend|middag)?", r"(overmorgen) ?(avond|nacht|ochtend|middag)?"])

    date_eu = re.compile(r"(\d{1,2})-(\d{1,2})-?(\d{2,4})?")
    date_eu2 = re.compile(r"(\d{1,4})-(\d{1,2})-?(\d{1,4})?")
    date_vs = re.compile(r"(\d{1,4})/(\d{1,2})/(\d{1,4})")
    date_vs2 = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2,4})")
    date_vs3 = re.compile(r"(\d{1,2})/(\d{1,2})")
    ns = convert_nums.keys()
    timeus = convert_timeunit.keys()
    ms = convert_month.keys()
    if re.findall('|'.join(list_patterns), tweet):
        timephrases = []
        matches = re.findall('|'.join(list_patterns), tweet)
        nud = defaultdict(list)
        for i,units in enumerate(matches):
            timephrases.append(" ".join([x for x in units if len(x) > 0 and not x == " "]))
            for unit in units:
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
                elif re.search(r"-\d{2,4}",unit) or re.search(r"\d{4}-",unit) or re.search(r"\d{4}/",unit) or re.search(r"/\d{2,4}",unit):
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
                            y = decide_year(date,m,d)
                    else:
                        y = decide_year(date,m,d)
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
                            ds = date_eu.search(da[0] + [x[0] for x in nud["year"] if x[1] == \
                                num_match][0]).groups()
                        else:
                            ds = date_eu.search(da[0]).groups()
                    else:
                        ds = date_eu.search(da[0]).groups()
                    dsi = [int(x) for x in ds if x != None]
                    dsis = [x for x in ds if x != None]
                    try:
                        if dsi[1] in range(1,13) and \
                            dsi[0] in range(1,32):
                            if ds[2] == None:
                                if not (len(dsis[0]) == 1 and len(dsis[1]) == 1): #avoid patterns like 1-2
                                    y = decide_year(date,dsi[1],dsi[0])
                                    if date < datetime.date(y,dsi[1],dsi[0]):
                                        output.append(datetime.date(y,dsi[1],dsi[0]))
                            else:
                                if dsi[2] in range(2010,2020):
                                    if date < datetime.date(dsi[2],dsi[1],dsi[0]):
                                        output.append(datetime.date(dsi[2],dsi[1],dsi[0]))
                        elif dsi[0] in range(2010,2020): #2015/03/30
                            if dsi[1] in range(1,13) and dsi[2] in range(1,32):
                                if not (len(dsis[1]) == 1 and len(dsis[2]) == 1): #avoid patterns like 1/2
                                    if date < datetime.date(dsi[0],dsi[1],dsi[2]):
                                        output.append(datetime.date(dsi[0],dsi[1],dsi[2]))
                    except:
                        continue
                elif re.search("/",da[0]):
                    if "year" in nud:
                        if num_match in [x[1] for x in nud["year"]]:
                            if [x[0] for x in nud["year"] if x[1] == num_match][0][-1] == "/":
                                ds = date_vs.search([x[0] for x in nud["year"] if x[1] == \
                                    num_match][0] + da[0]).groups()
                            else:
                                ds = date_vs.search(da[0] + [x[0] for x in nud["year"] if x[1] == \
                                    num_match][0]).groups()
                        else:
                            ds = date_vs3.search(da[0]).groups()
                    else:
                        ds = date_vs3.search(da[0]).groups()
                    dsi = [int(x) for x in ds if x != None]
                    dsis = [x for x in ds if x != None]
                    try:
                        if dsi[0] in range(1,13) and dsi[1] in range(1,32): #30/03/2015
                            outdate = False
                            if len(dsi) == 3:
                                if len(dsis[2]) == 4:
                                    outdate = datetime.date(dsi[2],dsi[1],dsi[0])
                                elif len(dsis[2]) == 2:
                                    if dsi[2] in range(10,21):
                                        outdate = datetime.date((dsi[2]+2000),dsi[1],dsi[0])
                            else:
                                if not (len(dsis[0]) == 1 and len(dsis[1]) == 1): #avoid patterns like 1/2
                                    y = decide_year(date,dsi[1],dsi[0])
                                    outdate = datetime.date(y,dsi[1],dsi[0])
                            if outdate:
                                if date < outdate:
                                    output.append(outdate)
                        elif dsi[0] in range(1,13) and dsi[1] in range(1,32): #30/03
                            if not (len(dsis[0]) == 1 and len(dsis[1]) == 1): #avoid patterns like 1/2
                                y = decide_year(date,dsi[0],dsi[1])
                                if date < datetime.date(y,dsi[0],dsi[1]):
                                    output.append(datetime.date(date.year,dsi[0],dsi[1]))
                        elif dsi[0] in range(2010,2020): #2015/03/30
                            if dsi[1] in range(1,13) and dsi[2] in range(1,32):
                                if not (len(dsis[1]) == 1 and len(dsis[2]) == 1): #avoid patterns like 1/2
                                    if date < datetime.date(dsi[0],dsi[1],dsi[2]):
                                        output.append(datetime.date(dsi[0],dsi[1],dsi[2]))
                    except:
                        continue
        if "weekday" in nud:
            if not "date" in nud and not "month" in nud and not "timeunit" in nud: # overrule by more specific indication
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

def extract_entity(text):
    ngram_score = []
    c = text.split()
    for i in range(5):
        if i == 0:
            ngrams = zip(c)
        elif i == 1:
            ngrams = zip(c, c[1:])
        elif i == 2:
            ngrams = zip(c, c[1:], c[2:])
        elif i == 3:
            ngrams = zip(c, c[1:], c[2:], c[3:])
        elif i == 4:
            ngrams = zip(c, c[1:], c[2:], c[3:], c[4:])
        for ngram in ngrams:
            if not (len(ngram) == 1 and (re.match("~",ngram[0]) or re.match(r"\d+",ngram[0]))):
                ngram = " ".join(ngram)
                pattern = classencoder.buildpattern(ngram)
                if not pattern.unknown():
                    if dmodel[pattern] > 0.05:
                        ngram_score.append((ngram,dmodel[pattern]))
    return ngram_score

def has_overlap(ids1,ids2):
    overlap = list(set(ids1) & set(ids2))
    overlap_percent = len(overlap) / len(ids1)
    if overlap_percent > 0.30:
        return True
    else:
        return False

#given two sets of tweet id list (tweets describing an event), couple the lists that overlap, return a new set
def merge_event_sets(set_current,set_new):
    set_merged = set_current
    for i,eventdict_new in enumerate(set_new):
        print(i)
        date = eventdict_new["date"]
        ids = eventdict_new["ids"]
        new = True
        date_events = [(j,x) for j,x in enumerate(set_1) if x["date"] == date]
        for index_ed in date_events:
            eventdict_current = index_ed[1]
            if has_overlap(ids,eventdict_current["ids"]):
                set_merged[j]["ids"] = eventdict_current["ids"].union(ids)
                set_merged[j]["tweets"] = eventdict_current["tweets"].union(eventdict_new["tweets"])
                set_merged[j]["score"] = max(eventdict_current["score"],eventdict_new["score"])
                set_merged[j]["entities"] = eventdict_current["entities"].union(eventdict_new["entities"])
                set_merged[j]["cities"] = eventdict_current["cities"].union(eventdict_new["cities"])
                print("add",j)
                new = False
        if new:
            set_merged.append(eventdict_new)
            print("new",len(set_merged))
    return set_merged

def calculate_cosine_similarity(vector1,vector2):
    if len(vector1) != len(vector2):
        print(str(len(vector1)) + " " + str(len(vector2))) 
        print("Cosine distance: no equal number of dimensions, terminating process.")

    mag1 = 0
    mag2 = 0
    dotpr = 0
    for i,term_1 in enumerate(vector1):
        term_2 = vector2[i]
        m1 = term_1 * term_1
        m2 = term_2 * term_2
        dp = term_1 * term_2
        mag1 += m1
        mag2 += m2
        dotpr += dp
    try:
        print(dotpr,mag1,mag2)
        cosine_similarity = dotpr / (math.sqrt(mag1)*math.sqrt(mag2))
    except:
        cosine_similarity = 0
    return cosine_similarity
