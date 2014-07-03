
import re
import datetime
from collections import defaultdict
import math
import itertools

import colibricore
import time_functions
import calculations

class Event_pairs:

    def __init__(self):
        self.tweets = []

    def append_eventtweets(self,eventtweets):
        for et in eventtweets:
            info = et.strip().split("\t")
            info[2] = time_functions.return_datetime(info[2],
                    setting="vs").date()
            info[4] = [time_functions.return_datetime(x,
                    setting="vs").date() for x in info[4].split(" ")]
            tweet = self.Tweet()
            units = info[:5]
            #print("chunks",[x.strip() for x in info[5].split("|")])
            units.append([x.strip() for x in info[5].split("|")])
            tweet.set_meta(units)
            if len(info) > 6:
                #print("entities",[x.strip() for x in info[6].split(" ")])
                tweet.set_entities([x.strip() for x in info[6].split(" ")])            
            self.tweets.append(tweet)
        print("all",[t.entities for t in self.tweets if t.e])

    def select_date_entity_tweets(self,new_tweets,ent,ht):
        for tweet in new_tweets:
            tokens = tweet.strip().split("\t")
            if tokens[0] == "dutch" and not re.search("^RT ",
                tokens[-1]):
                text = tokens[-1].lower()
                date = time_functions.return_datetime(tokens[3],
                    setting="vs").date()
                dateref_phrase = self.extract_date(text,date)
                if dateref_phrase:
                    if len(dateref_phrase) > 1:
                        chunks = dateref_phrase[0]
                        refdates = dateref_phrase[1:]
                        dtweet = self.Tweet()
                        units = [tokens[1],tokens[2],date,text,
                            refdates,chunks]
                        dtweet.set_meta(units)
                        if ent:
                            entities = []
                            for chunk in chunks:
                                entities.extend(self.extract_entity(chunk))
                            entities = sorted(entities,key = lambda x: x[1],reverse=True)
                            if len(entities) > 0:
                                if ent == "single":
                                    dtweet.set_entities([entities[0][0]])
                                elif ent == "all":
                                    dtweet.set_entities([x[0] for x in entities])
                        if ht:
                            hashtags = [x for x in text.split(" ") if re.search(r"^#",x)]
                            if len(hashtags) > 0:
                                if dtweet.e:
                                    dtweet.entities.extend(hashtags)
                                else:
                                    dtweet.set_entities(hashtags)
                        self.tweets.append(dtweet)

    def load_commonness(self,tmp,wiki_commonness):
        #load in commonness files per ngram
        print("reading in text")
        classfile = tmp + "_page.colibri.cls"
        textfile = tmp + "_page.txt"
        corpusfile = tmp + "_page.colibri.dat"
        with open(textfile,'w',encoding = 'utf-8') as g:
            for ngramfile in wiki_commonness:
                ngramopen = open(ngramfile,encoding = "utf-8")
                for line in ngramopen.readlines():
                    tokens = line.strip().split("\t")
                    g.write(tokens[0] + "\n")
                    # ngramdict[tokens[0]] = float(tokens[3])
                ngramopen.close()
        # g.close()
            # self.ngramdicts.append(ngramdict)
        self.classencoder = colibricore.ClassEncoder()
        self.classencoder.build(textfile)
        self.classencoder.save(classfile)
        self.classencoder.encodefile(textfile, corpusfile)
        self.classdecoder = colibricore.ClassDecoder(classfile)
        self.dmodel = colibricore.PatternDict_float()
        #assign values to ngrams
        print("making dict")
        for ngramfile in wiki_commonness:
            ngramopen = open(ngramfile,encoding = "utf-8")
            for line in ngramopen.readlines():
                tokens = line.strip().split("\t")
                pattern = self.classencoder.buildpattern(tokens[0])
                self.dmodel[pattern] = float(tokens[3])
            ngramopen.close()

    # def select_entity_tweets(self,approach = "single"):
    #     #extract entities from tweets
    #     print("extracting entities")
    #     for tweet in self.tweets:
    #         entities = []
    #         for chunk in tweet.chunks:
    #             entities.extend(self.extract_entity(chunk))
    #         entities = sorted(entities,key = lambda x: x[1],
    #             reverse=True)
    #         if len(entities) > 0:
    #             if approach == "single":
    #                 tweet.entities = [entities[0][0]]
    #             elif approach == "all":
    #                 tweet.entities = [x[0] for x in entities]

    # def select_hashtags_tweets(self):
    #     for tweet in self.tweets:
    #         hashtags = [x for x in tweet.text.split(" ") if re.search(r"^#",x)]
    #         if len(hashtags) > 0:
    #             try:
    #                 tweet.entities.extend(hashtags)
    #             except:
    #                 tweet.set_entities(hashtags)

    def rank_events(self,ranking,clust = False):
        date_entity_score = []
        date_entity_tweets = defaultdict(lambda : defaultdict(list))
        #count dates and entities and pairs
        date_entity = defaultdict(lambda : defaultdict(int))
        entity_count = defaultdict(int)
        date_count = defaultdict(int)
        print("counting dates and entities")
        for tweet in self.tweets:
            for date in tweet.daterefs:
                date_count[date] += 1
                if tweet.e:
                    if clust:
                        for u in range(2,len(tweet.entities)+1):
                            for subset in itertools.combinations(tweet.entities, u):
                                s1 = []
                                s2 = []
                                half = int(len(subset) / 2)
                                for y in subset[:half]:
                                    s1.extend(y.split(" "))
                                for y in subset[half:]:
                                    s2.extend(y.split(" "))
                                if not bool(set(s1) & set(s2)):
                                    s = tuple(sorted(subset))
                                    print(s)
                                    entity_count[s] += 1
                                    date_entity[date][s] += 1
                    else:
                        for entity in tweet.entities:
                            entity_count[entity] += 1
                            date_entity[date][entity] += 1
                            date_entity_tweets[date][entity].append(tweet.text)
        print("calculating score")
        #for each pair
        if ranking == "fit":
            total = len(self.tweets)
            for date in date_entity.keys():
                for entity in date_entity[date].keys():
                    if len(date_entity_tweets[date][entity]) >= 5:
                        g2 = 0
                        dc = date_count[date]
                        ec = entity_count[entity]
                        ode = date_entity[date][entity]
                        ede = (dc + ec) / total
                        if ode > 0 and ede > 0:
                            g2 += ode * (math.log(ode/ede)/math.log(2))
                        odne = dc - ode
                        edne = (dc + (total-ec)) / total
                        if edne > 0 and odne > 0:
                            g2 += odne * (math.log(odne/edne)/math.log(2))
                        onde = ec - ode
                        ende = (ec + (total-dc)) / total
                        if onde > 0 and ende > 0:
                            g2 += onde * (math.log(onde/ende)/math.log(2))
                        ondne = total - (ode+odne+onde) 
                        endne = ((total-dc) + (total-ec)) / total
                        if ondne > 0 and endne > 0:
                            g2 += ondne * (math.log(ondne/endne)/math.log(2))
                        date_entity_score.append([date,entity,g2,date_entity_tweets[date][entity]])
        elif ranking == "freq":
            for date in date_entity.keys():
                for entity in date_entity[date].keys():
                    date_entity_score.append([date,entity,len(date_entity_tweets[date][entity]),date_entity_tweets[date][entity]])
        return sorted(date_entity_score,key = lambda x: x[2],
                reverse=True)

    def extract_date(self,tweet,date):
        convert_nums = {"een":1, "twee":2, "drie":3, "vier":4,
            "vijf":5, "zes":6, "zeven":7, "acht":8, "negen":9, 
            "tien":10, "elf":11, "twaalf":12, "dertien":13,
            "veertien":14, "vijftien":15, "zestien":16, "zeventien":17,
            "achtien":18, "negentien":19, "twintig":20,
            "eenentwintig":21,"tweeentwintig":22,"drieentwintig":23,
            "vierentwintig":24,"vijfentwintig":25,"zesentwintig":26,
            "zevenentwintig":27,"achtentwintig":28,"negenentwintig":29,
            "dertig":30,"eenendertig":31}
        convert_month = {"jan":1, "januari":1, "feb":2, "februari":2,
            "mrt":3, "maart":3, "apr":4, "april":4, "mei":5, "jun":6,
            "juni":6, "jul":7, "juli":7, "aug":8, "augustus":8,
            "sep":9, "september":9, "okt":10, "oktober":10, "nov":11,
            "november":11,"dec":12, "december":12}
        convert_timeunit = {"dagen":1, "daagjes":1, "dag":1,"dagje":1,
            "nachten":1,"nachtjes":1,"nacht":1,"nachtje":1,"weken":7,
            "weekjes":7,"week":7,"weekje":7,"maanden":30,
            "maandjes":30,"maand": 30,"maandje":30}
        weekdays=["maandag","dinsdag","woensdag","donderdag","vrijdag",
            "zaterdag","zondag"]
        spec_days=["morgen","overmorgen"]

        nums = (r"(\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|"
            "tien|elf|twaalf|dertien|veertien|vijftien|zestien|"
            "zeventien|achtien|negentien|twintig|eenentwintig|"
            "tweeentwintig|drieentwintig|vierentwintig|vijfentwintig|"
            "zesentwintig|zevenentwintig|achtentwintig|negenentwintig|"
            "dertig|eenendertig)")
        months = (r"(jan|januari|feb|februari|mrt|maart|apr|april|mei|"
            "jun|juni|jul|juli|aug|augustus|sep|september|okt|oktober|"
            "nov|november|dec|december)")
        timeunits = (r"(dagen|daagjes|dag|dagje|nachten|"
            "nachtjes|nacht|nachtje|weken|weekjes|week|weekje|maanden|"
            "maandjes|maand|maandje)")

        list_patterns = ([r"(over|nog) (minimaal |maximaal |tenminste |"
            "bijna |ongeveer |maar |slechts |pakweg |ruim |krap |"
            "(maar )?een kleine |(maar )?iets (meer|minder) dan )?" + 
            (nums) + " " + (timeunits) + r"($| )", (nums) + " " + (timeunits) + 
            r"( slapen)? tot", r"met( nog)? (minimaal |maximaal |"
            "tenminste |bijna |ongeveer |maar |slechts |pakweg |ruim |"
            "krap |(maar )?een kleine |"
            "(maar )?iets (meer|minder) dan )?" + (nums) + " " + 
            (timeunits) + r"( nog)? te gaan",r"(\b|^)" + (nums) + " " +
            (months) + r"( |$)" + r"(\d{2,4})?",r"(\b|^)(\d{1,2}-\d{1,2})"
            r"(-\d{2,4})?(\b|$)",r"(\b|^)(\d{2,4}/)?(\d{1,2}/\d{1,2})"
            "(\b|$)",r"(\b|$)(volgende week)? ?(maandag|dinsdag|"
            "woensdag|donderdag|vrijdag|zaterdag|zondag|overmorgen) ?"
            r"(avond|nacht|ochtend|middag)?( |$)"])

        date_eu = re.compile(r"(\d{1,2})-(\d{1,2})-?(\d{2,4})?")
        date_vs = re.compile(r"(\d{2,4})?/?(\d{1,2})/(\d{1,2})")
        ns = convert_nums.keys()
        timeus = convert_timeunit.keys()
        ms = convert_month.keys()
        if re.findall('|'.join(list_patterns), tweet):
            #print tweet,re.findall('|'.join(list_patterns), tweet)
            timephrases = []
            matches = re.findall('|'.join(list_patterns), tweet)
            nud = defaultdict(list)
            for i,units in enumerate(matches):
                timephrases.append(" ".join([x for x in \
                        units if len(x) > 0 and not x == " "]))
                for unit in units:
                    if unit in ns:
                        nud["num"].append((convert_nums[unit],i))
                    elif unit in timeus:
                        if not "weekday" in nud:
                            nud["timeunit"].append\
                                ((convert_timeunit[unit],i))
                    elif unit in ms:
                        nud["month"].append((convert_month[unit],i))
                    elif re.search(r"\d{1,2}-\d{1,2}",unit) or \
                        re.search(r"\d{1,2}/\d{1,2}",unit):
                        nud["date"].append((unit,i))
                        timephrases[i] = "".join([x for x in \
                            units if len(x) > 0 and not x == " "])
                    elif re.search(r"-\d{2,4}",unit) or \
                        re.search(r"\d{2,4}/",unit):
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
                        if re.search(unit + \
                            r"(avond|middag|ochtend|nacht)",tweet):
                            timephrases[i] = "".join([x for x in \
                                units if len(x) > 0 and not x == " "])
                    elif unit in spec_days:
                        nud["sday"].append((unit,i))
                    elif unit == "volgende week":
                        nud["nweek"].append((unit,i))
                timephrases[i] = timephrases[i].replace("  "," ")
            regexPattern = '|'.join(map(re.escape, timephrases))
            output = [re.split(regexPattern, tweet)]
            if "timeunit" in nud:
                for t in nud["timeunit"]: 
                    num_match = t[1]
                    if "num" in nud:
                        days = t[0] * [x[0] for x in nud["num"] if \
                            x[1] == num_match][0]
                        try:
                            output.append(date + datetime.timedelta(days=days))
                        except OverflowError:
                            continue
            if "month" in nud:
                for t in nud["month"]:
                    num_match = t[1]
                    m = t[0]
                    try:
                        d = [x[0] for x in nud["num"] if x[1] == \
                            num_match][0]
                        if "year" in nud:
                            if num_match in [x[1] for x in nud["year"]]:
                                y = [x[0] for x in nud["year"] if \
                                    x[1] == num_match][0]
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
                            if num_match in [x[1] for x in \
                                nud["year"]]:
                                ds = date_eu.search(da[0] + [x[0] for x in \
                                    nud["year"] if x[1] == \
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
                                    if date < datetime.date(\
                                        date.year,dsi[1],
                                        dsi[0]):
                                        output.append(datetime.date(\
                                            date.year,dsi[1],
                                            dsi[0]))
                                else:
                                    if dsi[2] in range(2010,2020):
                                        if date < datetime.date(dsi[2],
                                            dsi[1],dsi[0]):
                                            output.append(datetime.date(dsi[2],
                                                dsi[1],dsi[0])) 
                            except:
                                continue
                    elif re.search("/",da[0]):
                        if "year" in nud:
                            if num_match in [x[1] for x in \
                                nud["year"]]:
                                ds = date_vs.search(da[0] + [x[0] for x in \
                                    nud["year"] if x[1] == \
                                    num_match][0]).groups()
                            else:
                                ds = date_vs.search(da[0]).groups()
                        else:
                            ds = date_vs.search(da[0]).groups()
                        dsi = [int(x) for x in ds if x != None]
                        try:
                            if dsi[0] in range(1,13) and \
                                dsi[1] in range(1,32):
                                if date < datetime.date(date.year,
                                    dsi[0],dsi[1]):
                                    output.append(datetime.date(date.year,
                                        dsi[0],dsi[1]))
                            elif dsi[0] in range(2010,2020):
                                if dsi[1] in range(1,13) and \
                                    dsi[2] in range(1,32):
                                    if date < datetime.date(dsi[0],
                                        dsi[1],dsi[2]):
                                        output.append(datetime.date(dsi[0],
                                            dsi[1],dsi[2]))
                        except:
                            continue
            if "weekday" in nud:
                if not "date" in nud and not "month" in nud and \
                    not "timeunit" in nud:
                    tweet_weekday=date.weekday()
                    for w in nud["weekday"]:
                        num_match = w[1]
                        ref_weekday=weekdays.index(w[0])
                        if num_match in [x[1] for x in nud["nweek"]]:
                            add = 7
                        else:
                            add = 0
                        if ref_weekday == tweet_weekday:
                            days_ahead = 7
                        elif tweet_weekday < ref_weekday:
                            days_ahead = ref_weekday - tweet_weekday + \
                                add
                        else:
                            days_ahead = ref_weekday + \
                                (7-tweet_weekday) + add
                        output.append(date + \
                            datetime.timedelta(days=days_ahead))
            if "sday" in nud:
                for s in nud["sday"]:
                    num_match = s[1] 
                    timephrase = " ".join([x for x in \
                        matches[num_match] if len(x) > 0])
                    u = s[0]
                    if u == "overmorgen":
                        output.append(date + \
                            datetime.timedelta(days=2))
            if len(nud.keys()) == 0:
                return False
            else:
                return output

    def extract_entity(self,text):
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
            for ngram in [" ".join(x).replace("#","") for x in ngrams]:
                pattern = self.classencoder.buildpattern(ngram)
                if not pattern.unknown():
                    if self.dmodel[pattern] > 0.05:
                        ngram_score.append((ngram,self.dmodel[pattern]))
        return ngram_score

    def discard_last_day(self,window):
        print("before",len(self.tweets))
        days = sorted(set([x.date for x in self.tweets]))
        size = len(days)
        if size <= window:
            print("not enough days, no discard") 
        while size > window:
            ld = days[0]
            print("last day",ld)
            self.tweets = [t for t in self.tweets if t.date != ld]
            days = sorted(set([x.date for x in self.tweets]))
            size = len(days)
        print("after",len(self.tweets))

    class Tweet:
        """
        Class containing the characteristics of a tweet that mentions 
            an entity and time
        """
        def __init__(self):
            self.e = False

        def set_meta(self,units):
            self.id = units[0]
            self.user = units[1]
            self.date = units[2]
            self.text = units[3]
            self.daterefs = units[4]
            self.chunks = units[5]
            if len(units) > 6:
                self.entities = units[6]

        def set_entities(self,entities):
            self.entities = entities
            self.e = True
