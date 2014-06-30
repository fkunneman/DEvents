
import re
import datetime
from collections import defaultdict
import codecs

# import colibricore
import time_functions


class Event_pairs:

    def __init__(self):
        self.tweets = []

    def append_eventtweets(self,eventtweets):
        for et in eventtweets:
            tweet = self.Tweet()
            tweet.set_meta(et)
            self.tweets.append(tweet)   

    def select_date_tweets(self,new_tweets):
        for tweet in new_tweets:
            tokens = tweet.strip().split("\t")
            if tokens[0] == "dutch":
                text = tokens[-1].lower()
                date = time_functions.return_datetime(tokens[3],
                    setting="vs")
                dateref_phrase = self.extract_date(text,date)
                if dateref_phrase:
                    print tweet,dateref_phrase
                    for entry in dateref_phrase:
                        dtweet = self.Tweet()
                        units = [tokens[1],tokens[2],date,text,
                            entry[0],[x[1] for x in dateref_phrase]]
                        dtweet.set_meta(units)
                        self.tweets.append(dtweet)
        print len(self.tweets),len(new_tweets)

    def select_entity_tweets(self,wiki_commonness,approach = "single"):
        #load in commonness files per ngram
        self.ngramdicts = []
        for ngramfile in wiki_commonness:
            ngramdict = defaultdict(float)
            ngramopen = codecs.open(ngramfile,"r","utf-8")
            for line in ngramopen.readlines():
                tokens = line.strip().split("\t")
                ngramdict[tokens[0]] = float(tokens[3])
            ngramopen.close()
            self.ngramdicts.append(ngramdict)
        #extract entities from tweets
        for tweet in self.tweets:
            entities = []
            for chunk in tweet.chunks:
                entities.extend(self.extract_entity(chunk))
        #print tweet.text,sorted(entities,key = lambda x: x[1],reverse=True)
            if approach == "single":
                entities = sorted(entities,key = lambda x: x[1],
                    reverse=True)
                if len(entities) > 0:
                    tweet.entities = [entities[0][0]]
                    print tweet.text,tweet.dateref,tweet.entities

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
            (nums) + " " + (timeunits), (nums) + " " + (timeunits) + 
            r"( slapen)? tot", r"met( nog)? (minimaal |maximaal |"
            "tenminste |bijna |ongeveer |maar |slechts |pakweg |ruim |"
            "krap |(maar )?een kleine |"
            "(maar )?iets (meer|minder) dan )?" + (nums) + " " + 
            (timeunits) + r"( nog)? te gaan",r"(\b|^)" + (nums) + " " +
            (months) + r"( (\d{2,4}))?(\b|$)",r"(\b|^)(\d{1,2}-\d{1,2})"
            r"(-\d{2,4})?(\b|$)",r"(\b|^)(\d{2,4}/)?(\d{1,2}/\d{1,2})"
            "(\b|$)",r"(\b|$)((volgende week) )?(maandag|dinsdag|"
            "woensdag|donderdag|vrijdag|zaterdag|zondag|overmorgen)"
            "(avond|nacht|ochtend|middag)?"])

        date_eu = re.compile(r"(\d{1,2})-(\d{1,2})-?(\d{2,4})?")
        date_vs = re.compile(r"(\d{2,4})?/?(\d{1,2})/(\d{1,2})")
        ns = convert_nums.keys()
        timeus = convert_timeunit.keys()
        ms = convert_month.keys()
        if re.findall('|'.join(list_patterns), tweet):
            #print tweet,re.findall('|'.join(list_patterns), tweet)
            matches = re.findall('|'.join(list_patterns), tweet)
            nud = defaultdict(list)
            for i,units in enumerate(matches):
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
                    elif re.search(r"-\d{2,4}",unit) or \
                        re.search(r"\d{2,4}/",unit):
                        nud["year"].append((unit,i))
                    elif re.match(r"\d+",unit):
                        if int(unit) in range(2010,2020):
                            nud["year"].append((int(unit),i))
                        elif "num" in nud: 
                            if int(unit) in range(1,13):
                                nud["month"].append((int(unit),i))
                        else:
                            nud["num"].append((int(unit),i))
                    elif unit in weekdays:
                        nud["weekday"].append((unit,i))
                    elif unit in spec_days:
                        nud["sday"].append((unit,i))
                    elif unit == "volgende week":
                        print tweet
                        nud["nweek"].append((unit,i))
            
            print tweet
            if "timeunit" in nud:
                pairs = []
                for t in nud["timeunit"]: 
                    num_match = t[1]
                    days = t[0] * nud["num"][num_match]
                    timephrase = " ".join([x for x in \
                        matches[num_match] if len(x) > 0])
                    # print units,timephrase 
                    pairs.append((date + datetime.timedelta(days=days),
                        tweet.split(timephrase)))
                return pairs
            if "month" in nud:
                pairs = []
                for t in nud["month"]:
                    num_match = t[1]
                    m = t[0]
                    d = nud["num"][num_match][0]
                    if "year" in nud:
                        if num_match in [x[1] for x in nud["year"]]:
                            y = [x[0] for x in nud["year"] if \
                                x[1] == [num_match]][0]
                    else:
                        y = date.year
                    timephrase = " ".join([x for x in \
                        matches[num_match] if len(x) > 0])
                    # print tweet,units,timephrase
                    pairs.append((datetime.date(y,m,d),
                        tweet.split(timephrase)))
                return pairs
            if "date" in nud:
                pairs = []
                for da in nud["date"]:
                    num_match = da[1]
                    timephrase = "".join([x for x in \
                        matches[num_match] if len(x) > 0])
                    # print tweet,units,timephrase
                    if re.search("-",da[0]):
                        if "year" in nud:
                            if num_match in [x[1] for x in \
                                nud["year"]]:
                                ds = date_vs.search([x[0] for x in \
                                    nud["year"] if x[1] == \
                                    [num_match]][0] + da).groups()
                        else:
                            ds = date_eu.search(da).groups()
                        dsi = [int(x) for x in ds if x != None]
                        if dsi[1] in range(1,13) and \
                            dsi[0] in range(1,32):

                            if ds[2] == None:
                                pairs.append((datetime.date(\
                                    date.year,dsi[1],
                                    dsi[0]),tweet.split(timephrase)))
                            else:
                                if dsi[2] in range(2010,2020):
                                    pairs.append((datetime.date(dsi[2],
                                        dsi[1],dsi[0]),
                                        tweet.split(timephrase))) 
                    elif re.search("/",da):
                        if "year" in nud:
                            if num_match in [x[1] for x in \
                                nud["year"]]:
                                ds = date_vs.search([x[0] for x in \
                                    nud["year"] if x[1] == \
                                    [num_match]][0] + da).groups()
                        else:
                            ds = date_vs.search(da).groups()
                        dsi = [int(x) for x in ds if x != None]
                        if dsi[0] in range(1,13) and \
                            dsi[1] in range(1,32):
                            pairs.append((datetime.date(date.year,
                                dsi[0],dsi[1]),
                                tweet.split(timephrase)))
                        elif dsi[0] in range(2010,2020):
                            if dsi[1] in range(1,13) and \
                                dsi[2] in range(1,32):
                                pairs.append((datetime.date(dsi[0],
                                    dsi[1],dsi[2]),
                                    tweet.split(timephrase)))
                return pairs
            if "weekday" in nud:
                if not "date" in nud and not "month" in nud and \
                    not "timeunit" in nud:
                    pairs = []
                    tweet_weekday=date.weekday()
                    for w in nud["weekday"]:
                        num_match = w[1]
                        timephrase = " ".join([x for x in \
                            matches[num_match] if len(x) > 0])
                        # print tweet,units,timephrase
                        ref_weekday=weekdays.index(nud["weekday"])
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
                        pairs.append((date + \
                            datetime.timedelta(days=days_ahead),
                            tweet.split(timephrase)))
                    return pairs
            if "sday" in nud:
                pairs = []
                for s in nud["sday"]:
                    num_match = s[1] 
                    timephrase = " ".join([x for x in \
                        matches[num_match] if len(x) > 0])
                    u = s[0]
                    if u == "overmorgen":
                        pairs.append((date + \
                            datetime.timedelta(days=2),
                            tweet.split(timephrase)))
                return pairs
            if len(nud.keys()) == 0:
                return False

    def extract_entity(self,chunk):
        ngram_score = []
        #get all n-grams up to 5
        for i in range(len(self.ngramdicts)):
            ngdict = self.ngramdicts[i]
            dng = set(ngdict)
            c = chunk.split()
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
                if ngram in dng:
                    ngram_score.append((ngram,ngdict[ngram]))
        return ngram_score

    class Tweet:
        """
        Class containing the characteristics of a tweet that mentions 
            an entity and time
        """
        def __init__(self):
            self.id = ""
            self.user = ""

        def set_meta(self,units):
            self.id = units[0]
            self.user = units[1]
            self.date = units[2]
            self.text = units[3]
            self.dateref = units[4]
            self.chunks = units[5]
            if len(units) > 5:
                self.entities = units[6:]

        def set_entities(self,entities):
            self.entities = entities
