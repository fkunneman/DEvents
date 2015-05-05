
from __future__ import division
import math
import itertools
import numpy
import re
import os
import itertools
import datetime
from collections import defaultdict
import numpy
import copy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time_functions

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

def extract_entity(text,classencoder,dmodel):
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
            if not (len(ngram) == 1 and (re.match("~",ngram[0]) or re.match(r"\d+",ngram[0]) or re.match(r"ga",ngram[0]))):
                ngram = " ".join(ngram)
                pattern = classencoder.buildpattern(ngram)
                if not pattern.unknown():
                    if dmodel[pattern] > 0.05:
                        ngram_score.append((ngram,dmodel[pattern]))
    return ngram_score

def has_overlap_entity(s1,s2):
    if set(s1.split(" ")) & set(s2.split(" ")):
        return True
    else:
        return False

def resolve_overlap_entities(entities):
    new_entities = []
    i = 0
    while i < len(entities):
        one = False
        if i+1 >= len(entities):
            one = True 
        elif entities[i][1] > entities[i+1][1]:
            one = True
        if one:
            overlap = False
            for e in new_entities:
                if has_overlap_entity(re.sub('#','',entities[i][0]),re.sub('#','',e[0])):
                    overlap = True    
            if not overlap:
                new_entities.append(entities[i])
            i+=1
        else: #entities have the same score
            #make list of entities with similar score
            sim_entities = [entities[i],entities[i+1]]
            j = i+2
            while j < len(entities):
                if entities[j][1] == entities[i][1]: 
                    sim_entities.append(entities[j])
                    j+=1
                else:
                    break
            i=j
            #rank entities by length
            sim_entities = sorted(sim_entities,key = lambda x : len(x[0].split(" ")), reverse=True)
            for se in sim_entities:
                overlap = False
                for e in new_entities:
                    if has_overlap_entity(se[0].replace("_"," ").replace("#",""),e[0].replace("_"," ").replace("#","")):
                        overlap = True
                if not overlap:
                    new_entities.append(se)
    return new_entities

def order_entities(entities,tweets):
    rankings = {}
    for i,x in enumerate(entities):
        rankings[x] = [i,entities[i]]
    for i,e0 in enumerate(entities[:-1]):
        scores = [[0,0] for y in itertools.repeat(None,(len(entities) - (i+1)))]
        ents = entities[i+1:]
        for text in tweets:
            if re.search(re.escape(e0),text):
                p0 = re.search(re.escape(e0),text).span()[0]           
                for j,e1 in enumerate(ents):
                    if re.search(re.escape(e1),text):
                        p1 = re.search(re.escape(e1),text).span()[0]
                        if p0 < p1:
                            scores[j][0] += 1
                        else:
                            scores[j][1] += 1
        for j,e1 in enumerate(ents):
            score = scores[j]
            if score[0] > score[1] and rankings[e0][0] > rankings[e1][0]:
                lowers = [x for x in rankings.keys() if rankings[x][0] > rankings[e1][0] and rankings[x][0] < rankings[e0][0]]
                rankings[e0][0] = rankings[e1][0]
                rankings[e1][0] += 1
                for l in lowers:
                    rankings[l][0] += 1
            elif score[1] > score[0] and rankings[e1][0] > rankings[e0][0]:
                lowers = [x for x in rankings.keys() if rankings[x][0] > rankings[e0][0] and rankings[x][0] < rankings[e1][0]]
                rankings[e1][0] = rankings[e0][0]
                rankings[e0][0] += 1
                for l in lowers:
                    rankings[l][0] += 1
    if len(entities) == len(rankings.values()):
        new_entities = []
        for rank in range(len(rankings.keys())):
            new_entities.append([e[1] for e in rankings.values() if e[0] == rank][0]) 
        return new_entities
    else:
        return entities

def has_overlap(ts1,ts2):
    ids1 = [t["id"] for t in ts1]
    ids2 = [t["id"] for t in ts2]
    overlap = list(set(ids1) & set(ids2))
    overlap_percent = len(overlap) / len(ids1)
    if overlap_percent > 0.10:
        return True
    else:
        return False

#given two sets of tweet id list (tweets describing an event), couple the lists that overlap, return a new set
def merge_event_sets(set_current,set_new):
    if len(set_current) > 0:
        set_merged = set_current
    else:
        set_merged = [set_new[0]]
        set_new = set_new[1:]
    print("set merged",len(set_merged))
    for i,eventdict_new in enumerate(set_new):
        date = eventdict_new["date"]
        tweets = eventdict_new["tweets"]
        new = True
        if len(set_current) > 0:
            date_events = [(j,x) for j,x in enumerate(set_current) if x["date"] == date]
        else:
            date_events = [(j,x) for j,x in enumerate(set_merged) if x["date"] == date]
        for index_ed in date_events:
            j = index_ed[0]
            eventdict_current = index_ed[1]
            if has_overlap(tweets,eventdict_current["tweets"]):
                #print("MERGE",eventdict_current["keylist"],eventdict_new["keylist"])
                merged_ids = list(set([t["id"] for t in eventdict_current["tweets"]]).union(set([t["id"] for t in tweets])))
                set_merged[j]["tweets"] = []
                for t in tweets:
                    if t["id"] in merged_ids:
                        set_merged[j]["tweets"].append(t)
                        merged_ids.remove(t["id"])
                for t in eventdict_current["tweets"]:
                    if t["id"] in merged_ids:
                        set_merged[j]["tweets"].append(t)
                        merged_ids.remove(t["id"])
                set_merged[j]["score"] = max(eventdict_current["score"],eventdict_new["score"])
                keylist_ents = [[x,0] for x in list(set(eventdict_current["keylist"]).union(set(eventdict_new["keylist"])))]
                keylist_ents = resolve_overlap_entities(keylist_ents)
                keylist_ents = order_entities([x[0] for x in keylist_ents],[x["text"] for x in set_merged[j]["tweets"]])
                set_merged[j]["keylist"] = keylist_ents
                new = False
        if new:
            set_merged.append(eventdict_new)
    print("new",len(set_merged))
    return set_merged

def tfidf_docs(documents):
    tfidf_vectorizer = TfidfVectorizer()
    return tfidf_vectorizer.fit_transform(documents)

def return_similarities(vectors1,vectors2):
    return cosine_similarity(vectors1,vectors2)

def return_intervals(dates):
    intervals = []
    last_date = dates.pop(0)
    while len(dates) > 0:
        dif = time_functions.timerel(dates[0],last_date,unit="day")
        if dif >= 2:
            intervals.append(dif)
        last_date = dates.pop(0)
    return intervals

def return_relative_stdev(sequence):
    std = numpy.std(sequence)
    avg = numpy.mean(sequence)
    rstd = 100 * (std / avg)
    return rstd

def return_segmentation(sequence):
    print(sequence)
    
    def return_segs(k,seq):
        outsegs = []
        if k > 1:
            for n in range(1,len(seq)):
                outsegs.extend([[n] + x for x in return_segs(k-1,seq[n:]) if not \
                re.search("1_1","_".join([str(y) for y in x]))])
        else:
            outsegs.append([len(seq)])
        return outsegs

    #extract all segment scores
    segment_stdev = defaultdict(lambda : defaultdict(float))
    sst = []
    for n in range(2,len(sequence)+1):
        segments = [sequence[i:i+n] for i in range(len(sequence)-n+1)]
        for i,segment in enumerate(segments):
            segment_stdev[i][i+n] = return_relative_stdev(segment) + (100-(n/len(sequence) * 100))
            sst.append([[i,i+n],segment_stdev[i][i+n]])
#    print("sst",sst)
    top = sorted(sst,key = lambda k : k[1])
    for seg in top:
        st = seg[0][0]
        #if st<0:
        #    st = 0
        e = seg[0][1]
        #if e > len(sequence):
        #    e = len(sequence)
        testseq = sequence[st:e]
        median = numpy.median(testseq)
#        print(median)
        #print((median*2)+3)
        #print((median*2)-3)
        db = range(int((median*2)-3),int((median*2)+3))
        spl = range(int(median-3),int(median+3))
        newseq = []
 #       print(testseq)
        while i < len(testseq):
            if testseq[i] in db:
                newseq.append([int(x) for x in [(testseq[i]/2)] * 2])
                i+=1
            else:
                if i+2 < len(testseq):
                    if sum([testseq[i],testseq[i+1],testseq[i+2]]) in spl:
                        newseq.append(sum([testseq[i],testseq[i+1],testseq[i+2]]))
                        i+=3
                        continue
                    #else:
                    #    newseq.append(testseq[i])
                    #    i+=1
                #else:
                if i+1 < len(testseq):
                    if sum([testseq[i],testseq[i+1]]) in spl:
                        newseq.append(sum([testseq[i],testseq[i+1]]))
                        i+=2
                    else:
                        newseq.append(testseq[i])
                        i+=1
                else:
                    newseq.append(testseq[i])
                    i+=1
  #      print(seg,newseq)
                                         
    return sorted(sst,key = lambda k : k[1])
#    quit()
    #find optimal segmentation
 #   all_combs = []
 #   for k in range(1,len(sequence)):
 #       all_combs.extend([x for x in return_segs(k,sequence) if not \
 #       re.search("1_1","_".join([str(y) for y in x]))])
 #   best = [] # [[path,score]]
 #   print(len(all_combs))
 #   for combi in all_combs:
 #       scores = []
 #       start = 0
 #       for l in combi:
 #           if l >= 2:
 #               scores.append(segment_stdev[start][start+l])
 #           start = start+l
 #       penalty = len(combi) / len(sequence)
        #print(combi,scores)
 #       score = (numpy.mean(scores)) + penalty
 #       if len(best) == 0:
 #           best = [combi,score]
 #       else:
 #           if score < best[1]:
 #               best = [combi,score]
#    print(best)  

    #for start in range(1,len(sequence)-1): #number of segments
    # for n in range(2,len(sequence)+1):
    #     optimal = [0,10000]
    #     new_segmentations = [[i,n] for i in [0,1] if n-i >= 2]
    #     for ns in new_segmentations:
    #         score = segment_stdev[ns[0]][ns[1]]
    #         if score < optimal[1]:
    #             optimal[1] = score
    #             optimal[0] = [ns[0],ns[1]]
    #     for start in range(2,n):
    #         print(sequence,n,start,highest[start],segment_stdev[start][n],len(highest[start][0]) / len(sequence))
    #         if n-start >= 2:
    #             score = numpy.mean([highest[start][1],segment_stdev[start][n]]) * \
    #                 (len(highest[start][0]) / len(sequence))  
    #         else:
    #             score = highest[start][1]
    #         if score < optimal[1]:
    #             optimal[1] = score
    #             optimal[0] = highest[start][0] + [n]
    #     highest[n] = optimal
#    print(sequence,highest[n])
        
        #update best single segments

def find_outliers(sequence):
    seq = []
    avg = numpy.mean(sequence)
    std = numpy.std(sequence)
    print(sequence,avg,std)
    for i,val in enumerate(sequence):
        #print(i,val,abs(val-avg),std)
        if abs(val-avg) < std:
            seq.append([i,val])
    print(sequence,seq)
#    if len(seq) == len(sequence):
#       quit() 
#    find_outliers([x[1] for x in seq])

def cluster_time_vectors(terms,sequences,term_candidates,begin_date,end_date,k):
    #vectorize date sequences
    days = time_functions.timerel(end_date,begin_date,unit="day")
    standard_sequence = days * [0]
    vectors = []
    for sequence in sequences:
        vector = standard_sequence
        for date in sequence:
            vector[time_functions.timerel(date,begin_date,unit="day")] = 1
        vectors.append(vector)
    #generate initial clusters
    vector_cluster = {}
    cluster_vectors = defaultdict(list)
    vector_neighbours = defaultdict(list)
    for i in range(len(vectors)):
        vector_cluster[i] = i
        cluster_vectors[i] = [i]
    #generate nearest neighbours
    print("extracting nearest neighbours")
    for i,vector1 in enumerate(vectors):
        print(i,"of",len(vectors),"vectors")
        similarities = []
        candidates = [[terms.index(x),vectors[terms.index(x)]] for x in term_candidates[i]]
        for c in candidates:
            similarities.append([c[0],numpy.dot(vector1,c[1])])
        vector_neighbours[i] = [x[0] for x in sorted(similarities,key = lambda k : k[1],reverse = True)[:k]]
    #perform clustering
    print("clustering")
    for i in range(len(vectors)):
        candidates = [x for x in vector_neighbours[i] if vector_cluster[x] != vector_cluster[i]]
        for j in candidates:
            if i in vector_neighbours[j]:
                if vector_cluster[j] != j:
                    print("clusterrisk",i,j,cluster_vectors[vector_cluster[i]],cluster_vectors[vector_cluster[j]],sequences[i],sequences[j])
                try:
                    del cluster_vectors[vector_cluster[j]]
                except KeyError:
                    print("already deleted")
                vector_cluster[j] = vector_cluster[i]
                cluster_vectors[vector_cluster[i]].append(j)

    return cluster_vectors

def return_pmi(n,f1,f2,f12):
    p12 = f12/n
    p1_2 = (f1*f2)/(n*n)
    return math.log((p12/p1_2),10)

def return_jaccard(f1,f2,f12):
    return (f12/(f1+f2))

def cluster_jp(term_vecs,k):
    #generate initial clusters
    vector_cluster = {}
    cluster_vectors = defaultdict(list)
    vector_neighbours = defaultdict(list)
    terms = sorted(term_vecs.keys())
    for i,term in enumerate(terms):
        vector_cluster[term] = i
        cluster_vectors[i] = [term]
    #generate nearest neighbours
    print("extracting nearest neighbours")
    for term in terms:
        # vector_neighbours[term] = [x[0] for x in sorted(term_vecs[term],key = lambda x : x[1],reverse=True) if x[1] > 3][:k]
        vector_neighbours[term] = [x[0] for x in sorted(term_vecs[term],key = lambda x : x[1],reverse=True)][:k]
    #perform clustering
    print("clustering")
    for term in terms:
        candidates = vector_neighbours[term]
        clustered = False
        if re.search("bevrijding",term):
            print(term,candidates)
        if re.search("valentijnskaart",term):
            print(term,candidates)
        if re.search(r"valentine",term):
            print(term,candidates)
        for c in candidates:
            if not c in cluster_vectors[vector_cluster[term]] and c in terms:
                if re.search("bevrijding",term):
                    print(term,c,vector_neighbours[c])
                if re.search("valentijnskaart",term):
                    print(term,c,vector_neighbours[c])
                if re.search(r"valentine",term):
                    print(term,c,vector_neighbours[c])
                if term in vector_neighbours[c]: #cluster
                    prev_clust = vector_cluster[c]
                    cluster_vectors[vector_cluster[term]].extend(cluster_vectors[prev_clust])
                    for ca in cluster_vectors[prev_clust]:
                        vector_cluster[ca] = vector_cluster[term]
                    del cluster_vectors[prev_clust]

    return cluster_vectors

def apply_calendar_pattern(pattern,last_date,step):
    return_date = False
    for i,level in enumerate(reversed(pattern)):
        if level == "e":
            sequence_level = len(pattern)-(i+1) 
            break
    if sequence_level == 0: #year
        year = last_date.year+step
        if pattern[1] != "v": #month is filled
            month = last_date.month
    elif sequence_level == 1: #month
        month = last_date.month + step
        if month > 12:
            year = last_date.year+1
            month = month-12
        else:
            year = last_date.year
    else: #week
        return_date = last_date + datetime.timedelta(days = 7*step)

    if not return_date: #yearly or monthly sequence   
        if pattern[3] != "v": #day is filled
            try:
                return_date = datetime.datetime(year,month,pattern[3])
            except:
                return False
        else: 
            if pattern[2] != "v": #week is filled
                raw_date = datetime.datetime(year,last_date.month,last_date.day)
                until_weekday = pattern[4] - raw_date.weekday()
                if until_weekday < 0:
                    until_weekday = 7 + until_weekday
                raw_date_weekday = raw_date + datetime.timedelta(days=until_weekday)
                dif = (pattern[2] - raw_date_weekday.isocalendar()[1]) * 7
                return_date = raw_date_weekday + datetime.timedelta(days=dif)
            else: #weekday
                raw_date = datetime.datetime(year,month,1)
                until_first_day = pattern[4] - raw_date.weekday()
                if until_first_day < 0:
                    until_first_day = 7 + until_first_day
                day = 1+until_first_day
                index = pattern[5]-1
                while index > 0:
                    day += 7
                    index -= 1
                try:
                    return_date = datetime.datetime(year,month,day)
                except:
                    return False

    return return_date

def score_calendar_periodicity(pattern,entries,total):
    coverage = len(entries) / total
    sorted_entries = sorted(entries,key = lambda x : x[0])
    for i,level in enumerate(reversed(pattern)):
        if level == "e":
            sequence_level = len(pattern)-(i+1) 
            break
    #sequence_level = pattern.index("e") + 1
#    seq = [x[sequence_level] for x in sorted_entries]
    #for i,level in enumerate(reversed(pattern)):
    #    if level == "e":
    #        sequence_level = len(pattern) - (i+1) 
    #        break
    sl_unit = [365,30.42,7.02]
#    sequence_level = pattern.index("e") + 1
    #seq = [x[sequence_level] for x in sorted_entries]
    seq = [x[0] for x in sorted_entries]
    intervals = []
    for i,x in enumerate(seq[1:]):
        if sequence_level == 0: #year
            interval = seq[i+1].year - seq[i].year
        else:
            interval = int(round((seq[i+1]-seq[i]).days / sl_unit[sequence_level],0))
    #    print("INT",interval)
        # if interval < 0: #year difference for week and month
        #     if sequence_level == 2: #month
        #         interval = abs(seq[i]-12) + seq[i+1]
        #     elif sequence_level == 3: #weeknr
        #         no_weeknrs = datetime.date(sorted_entries[i][1],12,28).isocalendar()[1]
        #         interval = abs(seq[i]-no_weeknrs) + seq[i+1]
        intervals.append(interval)
    #print(intervals,pattern,seq)
    step = min(intervals)
    if step == 0 or step > 6:
        consistency = 0
        gaps = []
    else:
        gaps = []
        if intervals.count(step) < len(intervals): #locate gaps
            dummy_date = copy.deepcopy(entries[0])
            for i,x in enumerate(intervals):
                if x != step:
                    gap_start = seq[i]
                    gap_end = seq[i+1]
                    gap = copy.deepcopy(gap_start)
                    while gap < gap_end:
                        gap = apply_calendar_pattern(pattern,gap,step)
                        if gap:
                            gaps.append(gap)
                        else:
                            break
        consistency = len(entries) / (len(entries) + len(gaps))

                    #     while gap.year < gap_end.year:
                    #         gap_date = copy.deepcopy(dummy_date)
                    #         gap_date[sequence_level] = gap
                    #         gaps.append(gap_date)
                    #         gap += step
                    # #gap = gap_start + step
                    # while gap < gap_end:
                    #     gap_date = copy.deepcopy(dummy_date)
                    #     gap_date[sequence_level] = gap
                    #     gaps.append(gap_date)
                    #     gap += step
    return [numpy.mean([coverage,consistency]),coverage,consistency,step,
        len(seq) + len(gaps),sorted_entries,gaps,"<" + ",".join([str(x) for x in pattern]) + ">"]

def periodicity_procedure(dates,every,level_value,t,l):
    pers = []
    if t == "recur":
        units = [x[level_value[0]] for x in dates]
        candidates = [unit for unit in list(set(units)) if units.count(unit) > 2]
        for c in candidates:
            pattern = ["v","v","v","v","v","v"]
            pattern[every-1] = "e"
            pattern[level_value[0]-1] = c
            for lv in level_value[1:]:
                pattern[lv[0]-1] = lv[1] 
            dates_c = copy.deepcopy([x for x in dates if x[level_value[0]] == c])
            pers.append(score_calendar_periodicity(pattern,dates_c,l)) #score pattern
    elif t == "seq":
        unit_sequence = copy.deepcopy(dates)
        unit_sequence = sorted(unit_sequence,key = lambda x : x[0])
#        while len(unit_sequence) > 2:
        pattern = ["v","v","v","v","v","v"]
        pattern[every-1] = "e"
        for lv in level_value:
            pattern[lv[0]-1] = lv[1]
        #all possible segments
        k = range(3,len(unit_sequence))
        for seqlen in k:
            #weekly pattern only in same year
            if pattern[2] != "v":
                segments = []
                ys = list(set([x[1] for x in unit_sequence]))
                for y in ys:
                    us = copy.deepcopy([x for x in unit_sequence if x[1] == y])
                    segments.extend([us[i:i+seqlen] for i in range(len(us)-seqlen)])
            else:
                segments = [unit_sequence[i:i+seqlen] for i in range(len(unit_sequence)-seqlen)]
 #           print(len(unit_sequence),seqlen,len(segments))
            for segment in segments:
                pers.append(score_calendar_periodicity(pattern,copy.deepcopy(segment),l)) #score pattern
            #unit_sequence.pop()
    return pers

def return_calendar_periodicities(sequence):
    periodicities = []
    #day route
    days = [x[4] for x in sequence]
    candidate_days = [day for day in list(set(days)) if days.count(day) > 2]
    for day in candidate_days:
        dates = copy.deepcopy([x for x in sequence if x[4] == day]) #collect dates
        #check yearly pattern
        periodicities.extend(periodicity_procedure(dates,1,[2,[4,day]],"recur",len(sequence)))
        #check monthly pattern
        periodicities.extend(periodicity_procedure(dates,2,[[4,day]],"seq",len(sequence)))
    #nr_weekday route
    nrs = [x[6] for x in sequence]
    candidate_nrs = [nr for nr in list(set(nrs)) if nrs.count(nr) > 2]
    for nr in candidate_nrs:
        nr_dates = [x for x in sequence if x[6] == nr]
        weekdays = [x[5] for x in nr_dates]
        candidate_weekdays = [wd for wd in list(set(weekdays)) if weekdays.count(wd) > 2]
        for weekday in candidate_weekdays:
            dates = copy.deepcopy([x for x in nr_dates if x[5] == weekday])
            #check yearly pattern
            periodicities.extend(periodicity_procedure(dates,1,[2,[5,weekday],[6,nr]],"recur",
                len(sequence))) 
            #check monthly pattern
            periodicities.extend(periodicity_procedure(dates,2,[[5,weekday],[6,nr]],"seq",
                len(sequence)))
    #weekday route
    weekdays = [x[5] for x in sequence]
    candidate_weekdays = [wd for wd in list(set(weekdays)) if weekdays.count(wd) > 2]
    for weekday in candidate_weekdays:
        dates = copy.deepcopy([x for x in sequence if x[5] == weekday])
        #check yearly pattern
        periodicities.extend(periodicity_procedure(dates,1,[3,[5,weekday]],"recur",len(sequence)))
        #check weekly pattern
        years = [x[1] for x in dates]
        candidate_years = [y for y in list(set(years)) if years.count(y) > 2]
        for year in candidate_years: #can only be in the same year
            dates_years = copy.deepcopy([x for x in dates if x[1] == year])
            periodicities.extend(periodicity_procedure(dates_years,3,[[5,weekday]],"seq",len(sequence)))

    #finalize periodicities
    if len(periodicities) > 0:
        sorted_periodicities = sorted(periodicities,key = lambda x : x[0],reverse=True)
        final_periodicities = [sorted_periodicities[0]]
        for p in sorted_periodicities:
            overlap = False
            dateset = set([x[0] for x in p[5]])
            for fp in final_periodicities:
                fp_dates = set([x[0] for x in fp[5]])
                if len(dateset&fp_dates) > 0:
                    overlap = True
                    break
            if not overlap:
                final_periodicities.append(p)
        return final_periodicities
    else:
        return periodicities

def cluster_documents(pairsims,indices,thresh):
    pairs = [x for x in itertools.combinations(indices,2)]
    scores = [[x[0],x[1],pairsims[x[0]][x[1]]] for x in pairs if pairsims[x[0]][x[1]] > thresh]
    #print(scores)
    cluster_vectors = defaultdict(list)
    vector_cluster = {}
    for i,index in enumerate(indices):
        cluster_vectors[i] = [index]
        vector_cluster[index] = i
    #print(cluster_vectors) #find out why there are empty clusters
    #print("BEFORE",cluster_vectors)
    if len(scores) > 0:
        scores_sorted = sorted(scores,key = lambda x : x[2],reverse = True)
        for score in scores_sorted:
            #print("MERGE BEFORE",cluster_vectors,vector_cluster)
            prev_clust = vector_cluster[score[1]]
            merge_clust = vector_cluster[score[0]]
            if not prev_clust == merge_clust:
            #print("BEFORE MERGE",score[0],score[1],cluster_vectors[vector_cluster[score[0]]],cluster_vectors[prev_clust])
                cluster_vectors[merge_clust].extend(cluster_vectors[prev_clust])
                for index in cluster_vectors[prev_clust]:
                    vector_cluster[index] = vector_cluster[score[0]]
                del cluster_vectors[prev_clust]
            #print("AFTER MERGE",cluster_vectors[vector_cluster[score[0]]])
    #print("AFTER",cluster_vectors)
    output = []
    for cluster in cluster_vectors.keys():
        output.append(cluster_vectors[cluster])
    return output
