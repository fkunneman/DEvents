
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
                    dtweet = self.Tweet()
                    units = [tokens[1],tokens[2],date,text,dateref_phrase[0],dateref_phrase[1]]
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
                entities = sorted(entities,key = lambda x: x[1],reverse=True)
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
        weekdays=["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
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
            "(\b|$)",r"(\b|$)(maandag|dinsdag|woensdag|donderdag|vrijdag|"
            "zaterdag|zondag|overmorgen)(avond|nacht|ochtend|middag)?"])

        date_eu = re.compile(r"(\d{1,2})-(\d{1,2})-?(\d{2,4})?")
        date_vs = re.compile(r"(\d{2,4})?/?(\d{1,2})/(\d{1,2})")
        ns = convert_nums.keys()
        timeus = convert_timeunit.keys()
        ms = convert_month.keys()
        if re.findall('|'.join(list_patterns), tweet):
            print re.findall('|'.join(list_patterns), tweet)
            units = re.findall('|'.join(list_patterns), tweet)[0]
            nud = {}
            for unit in units:
                if unit in ns:
                    nud["num"] = convert_nums[unit]
                elif unit in timeus:
                    nud["timeunit"] = convert_timeunit[unit]
                elif unit in ms:
                    nud["month"] = convert_month[unit]
                elif re.search(r"\d{1,2}-\d{1,2}",unit) or re.search(r"\d{1,2}/\d{1,2}",unit):
                    nud["date"] = unit
                elif re.search(r"-\d{2,4}",unit) or re.search(r"\d{2,4}/",unit):
                    nud["year"] = unit
                elif re.match(r"\d+",unit):
                    if int(unit) in range(2010,2020):
                        nud["year"] = int(unit)
                    elif "num" in nud: 
                        if int(unit) in range(1,13):
                            nud["month"] = int(unit)
                    else:
                        nud["num"] = int(unit)
                elif unit in weekdays:
                    nud["weekday"] = unit
                elif unit in spec_days:
                    nud["sday"] = unit

            if "timeunit" in nud: 
                days = nud["timeunit"] * nud["num"]
                timephrase = " ".join([x for x in units if len(x) > 0])
                print units,timephrase 
                return (date + datetime.timedelta(days=days),tweet.split(timephrase))
            elif "month" in nud:
                m = nud["month"]
                d = nud["num"]
                if "year" in nud:
                    y = nud["year"]
                else:
                    y = date.year
                timephrase = " ".join([x for x in units if len(x) > 0])
                print tweet,units,timephrase
                return (datetime.date(y,m,d),tweet.split(timephrase))
            elif "date" in nud:
                da = nud["date"]
                timephrase = "".join([x for x in units if len(x) > 0])
                print tweet,units,timephrase
                if re.search("-",da):
                    if "year" in nud: 
                        ds = date_eu.search(da + nud["year"]).groups()
                    else:
                        ds = date_eu.search(da).groups()
                    dsi = [int(x) for x in ds if x != None]
                    if dsi[1] in range(1,13) and \
                        dsi[0] in range(1,32):

                        if ds[2] == None:
                            return (datetime.date(date.year,dsi[1],
                                dsi[0]),tweet.split(timephrase))
                        else:
                            if dsi[2] in range(2010,2020):
                                return (datetime.date(dsi[2],dsi[1],
                                    dsi[0]),tweet.split(timephrase)) 
                elif re.search("/",da):
                    if "year" in nud:
                        ds = date_vs.search(nud["year"] + da).groups()
                    else:
                        ds = date_vs.search(da).groups()
                    dsi = [int(x) for x in ds if x != None]
                    if dsi[0] in range(1,13) and \
                        dsi[1] in range(1,32):
                        return (datetime.date(date.year,dsi[0],dsi[1]),tweet.split(timephrase))
                    elif dsi[0] in range(2010,2020):
                        if dsi[1] in range(1,13) and \
                            dsi[2] in range(1,32):
                            return (datetime.date(dsi[0],dsi[1],dsi[2]),tweet.split(timephrase))
            elif "weekday" in nud:
                timephrase = " ".join([x for x in units if len(x) > 0])
                print tweet,units,timephrase
                tweet_weekday=date.weekday()
                ref_weekday=weekdays.index(nud["weekday"])
                if ref_weekday == tweet_weekday:
                    days_ahead = 7
                elif tweet_weekday < ref_weekday:
                    days_ahead = ref_weekday - tweet_weekday
                else:
                    days_ahead = ref_weekday + (7-tweet_weekday)
                return (date + datetime.timedelta(days=days_ahead),tweet.split(timephrase))
            elif "sday" in nud:
                timephrase = " ".join([x for x in units if len(x) > 0])
                u = nud["sday"]
                #if u == "morgen":
                #    return (date + datetime.timedelta(days=1),tweet.split(timephrase))
                if u == "overmorgen":
                    return (date + datetime.timedelta(days=2),tweet.split(timephrase))
            else:
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
        """Class containing the characteristics of a tweet that mentions an entity and time"""
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
