
import re
import time_functions
import datetime

class Event_pairs:

    def __init__(self,eventtweets):
        self.tweets = []
        if eventtweets:
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
                dateref = self.extract_date(text,date)
                if dateref:
                    dtweet = self.Tweet()
                    units = [tokens[1],tokens[2],date,text,dateref]
                    dtweet.set_meta(units)
                    self.tweets.append(dtweet)
        print len(self.tweets),len(new_tweets)
#        print [(x.text,x.dateref) for x in self.tweets]

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
            "zaterdag|zondag|morgen|overmorgen)"])

        date_eu = re.compile(r"(\d{1,2})-(\d{1,2})-?(\d{2,4})?")
        date_vs = re.compile(r"(\d{2,4})?/?(\d{1,2})/(\d{1,2})")
        ns = convert_nums.keys()
        timeus = convert_timeunit.keys()
        ms = convert_month.keys()
        if re.findall('|'.join(list_patterns), tweet):
            units = re.findall('|'.join(list_patterns), tweet)[0]
            nud = {}
            print tweet,units
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
                elif unit in weekdays:
                    nud["weekday"] = unit
                elif unit in spec_days:
                    nud["sday"] = unit

            if "timeunit" in nud: 
                days = nud["timeunit"] * nud["num"]
                return date + datetime.timedelta(days=days)
            elif "month" in nud:
                m = nud["month"]
                d = nud["num"]
                if "year" in nud:
                    y = nud["year"]
                else:
                    y = date.year
                return datetime.date(y,m,d)
            elif "date" in nud:
                da = nud["date"]
                if re.search("-",da):
                    if "year" in nud:
                        ds = date_eu.search(da + nud["year"]).groups()
                    else:
                        ds = date_eu.search(da).groups()
                    dsi = [int(x) for x in ds if x != None]
                    if  dsi[1] in range(1,13) and \
                        dsi[0] in range(1,32):
                        if ds[2] == None:
                            return datetime.date(date.year,dsi[1],
                                dsi[0])
                        else:
                            if dsi[2] in range(2010,2020):
                                return datetime.date(dsi[2],dsi[1],
                                    dsi[0]) 
                elif re.search("/",da):
                    if "year" in nud:
                        ds = date_vs.search(nud["year"] + da).groups()
                    else:
                        ds = date_vs.search(da).groups()
                    dsi = [int(x) for x in ds if x != None]
                    if dsi[0] in range(1,13) and \
                        dsi[1] in range(1,32):
                        return datetime.date(date.year,dsi[0],dsi[1])
                    elif dsi[0] in range(2010,2020):
                        if dsi[1] in range(1,13) and \
                            dsi[2] in range(1,32):
                            return datetime.date(dsi[0],dsi[1],dsi[2])
            elif "weekday" in nud:
                tweet_weekday=date.weekday()
                ref_weekday=weekdays.index(nud["weekday"])
                if ref_weekday == tweet_weekday:
                    days_ahead = 7
                elif tweet_weekday < ref_weekday:
                    days_ahead = ref_weekday - tweet_weekday
                else:
                    days_ahead = ref_weekday + (7-tweet_weekday)
                print date,date + datetime.timedelta(days=days_ahead),days_ahead,nud["weekday"]
                return date + datetime.timedelta(days=days_ahead)
            elif "sday" in nud:
                u = nud["sday"]
                print "sday",nud["sday"]
                if u == "morgen":
                    return date + datetime.timedelta(days=1)
                elif u == "overmorgen":
                    return date + datetime.timedelta(days=2)
            else:
                return False


    def extract_weekday(self):
        future=re.compile(r"(straks|zometeen|vanmiddag|vanavond|vannacht|vandaag|morgenmorgenavond|morgenmiddag|morgenochtend|overmorgen|weekend|maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|maandagavond|dinsdagavond|woensdagavond|donderdagavond|vrijdagavond|zaterdagavond|zondagavond)")       
        today=re.compile(r"(straks|zometeen|vanmiddag|vanavond|vannacht|vandaag)",re.IGNORECASE)
        tomorrow=re.compile(r"(morgen|morgenavond|morgenmiddag|morgenochtend)",re.IGNORECASE)
        day_after_t=re.compile(r"overmorgen",re.IGNORECASE)
        weekend=re.compile(r"\b(weekend)\b",re.IGNORECASE)
        weekday=re.compile(r"(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)(avond|middag|ochtend)?",re.IGNORECASE)
        weekdays=["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]

        for instance in self.instances:
            ws = " ".join(instance.wordsequence)
            da = False
            if weekend.search(ws,re.IGNORECASE) or weekday.search(ws):
                da = True
                tweet_date=time_functions.return_datetime(instance.date,setting="vs")
                tweet_weekday=tweet_date.weekday()
                if weekend.search(ws):
                    ref_weekday=weekdays.index("zaterdag")
                else:
                    ref_weekday=weekdays.index(weekday.search(ws).groups()[0])
                if ref_weekday == tweet_weekday:
                    days_ahead = 0
                elif tweet_weekday < ref_weekday:
                    days_ahead = ref_weekday - tweet_weekday
                else:
                    days_ahead = ref_weekday + (7-tweet_weekday)
            elif today.search(ws):
                da = True
                days_ahead = 0
            elif tomorrow.search(ws):
                da = True
                days_ahead = 1
            elif day_after_t.search(ws):
                da = True
                days_ahead = 2

            if da:
                days_ahead = int(days_ahead)
                tweet_datetime = time_functions.return_datetime(instance.date,time=instance.time,setting="vs")
                event_datetime = tweet_datetime + datetime.timedelta(days = days_ahead)
                feature = "date_" + event_datetime.strftime("%d-%m-%Y")
                #print ws,feature                
                instance.features.append(feature)

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
            if len(units) > 4:
                self.entities = units[5:]

        def set_entities(self,entities):
            self.entities = entities
