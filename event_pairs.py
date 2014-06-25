
import re
import time_functions
import datetime

class Event_pairs:

    def __init__(self,eventtweets):
        self.tweets = []
        if eventtweets:
            for et in eventtweets:
                tweet = self.Tweet(et)
                self.tweets.append(tweet)

    def select_date_tweets(self,new_tweets):
        for tweet in new_tweets:
            tokens = tweet.strip().split("\t")
            text = tokens[-1].lower()
            date = time_functions.return_datetime(tokens[3],
                setting="vs")
            dateref = self.extract_date(text,date)
            if dateref:
                dtweet = self.Tweet()
                dtweet.set_date(dateref)
                self.tweets.append(dtweet)

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

        # m1 = re.compile(r"(over|nog) (minimaal |maximaal |tenminste |"
        #     "bijna |ongeveer |maar |slechts |pakweg |ruim |krap |"
        #     "(maar )?een kleine |(maar )?iets (meer|minder) dan )?" + 
        #     (nums) + " " + (timeunits))
        # m2 = re.compile((nums) + " " + (timeunits) + r"( slapen)? tot")
        # m3 = re.compile(r"met( nog)? (minimaal |maximaal |tenminste |"
        #     "bijna |ongeveer |maar |slechts |pakweg |ruim |krap |"
        #     "(maar )?een kleine |(maar )?iets (meer|minder) dan )?" + 
        #     (nums) + " " + (timeunits) + r"( nog)? te gaan")
        list_patterns = ([r"(over|nog) (minimaal |maximaal |tenminste |"
            "bijna |ongeveer |maar |slechts |pakweg |ruim |krap |"
            "(maar )?een kleine |(maar )?iets (meer|minder) dan )?" + 
            (nums) + " " + (timeunits), (nums) + " " + (timeunits) + 
            r"( slapen)? tot", r"met( nog)? (minimaal |maximaal |"
            "tenminste |bijna |ongeveer |maar |slechts |pakweg |ruim |"
            "krap |(maar )?een kleine |"
            "(maar )?iets (meer|minder) dan )?" + (nums) + " " + 
            (timeunits) + r"( nog)? te gaan",(nums) + " " + (months) + 
            "(\b|$)",r"([1,2,3]?\d)(-|/)(0?[1,2,3,4,5,6,7,8,9][0,1,2]?)"])
        # d1 = re.compile((nums) + " " + (months) + "(\b|$)")
        # d2 = re.compile(r"[1-3]?\d(-|/)[1-12]")

        ns = convert_nums.keys()
        timeus = convert_timeunit.keys()
        ms = convert_month.keys()
        #lines = []
        # for tweet in new_tweets:
            # text = tweet.strip().split("\t")[-1].lower()
        if re.findall('|'.join(list_patterns), tweet):
            units = re.findall('|'.join(list_patterns), tweet)[0]
            #lines.append(text)
#                print units,text
            nud = {}
            for unit in units:
                if unit in ns:
                    nud["num"] = convert_nums[unit]
                elif re.match(r"\d+",unit):
                    if "num" in nud:
                        nud["month"] = int(unit)
                    else:
                        nud["num"] = int(unit)
                elif unit in timeus:
                    nud["timeunit"] = convert_timeunit[unit]
                elif unit in ms:
                    nud["month"] = convert_month[unit]
            if "timeunit" in nud: 
                days = nud["timeunit"] * nud["num"]
                return date + datetime.timedelta(days=days)
            elif "month" in nud:
                m = nud["month"]
                d = nud["num"]
                y = date.year
                if m < date.month:
                    y += 1
                elif m == date.month:
                    if d < date.day:
                        y += 1
                return datetime.date(y,m,d)
            else:
                return False
            #print re.findall('|'.join(list_patterns), text),text
            #lines.append(text)
            # print text,nud,days
            # if m1.search(text) or m2.search(text) or m3.search(text):
            #     lines.append(text)
            # if d2.search(text):
            #     lines.append(text)

        #print len(lines)





    # def extract_date(self):
        
    #     for instance in self.instances:
    #         ws = " ".join(instance.wordsequence)
    #         if dates.search(ws):
    #             tweet_date = time_functions.return_datetime(instance.date,setting="vs")
    #             sh = dates.search(ws)
    #             if re.search(r"\d+",sh.groups()[0]):
    #                 day = int(sh.groups()[0])
    #             else:
    #                 day = convert_nums[sh.groups()[0]]
    #             month = convert_month[sh.groups()[1]]
    # #                
    #             #print month,ws,sh.groups()
    #             try:
    #                 date = datetime.datetime(tweet_date.year,month,day,0,0,0)
    #                 feature = "date_" + date.strftime("%d-%m-%Y")
    #             except:
    #                 continue
    #             # dif = time_functions.timerel(date,tweet_date,"day")
    #             # if dif < 0:
    #             #     date += datetime.timedelta(days=365)
    #             # feature = str(time_functions.timerel(date,tweet_date,"day")) + "_days"
    #             #print sh.groups(),feature
    #             instance.features.append(feature)  
    #     # quit()

    # def extract_weekday(self):
    #     future=re.compile(r"(straks|zometeen|vanmiddag|vanavond|vannacht|vandaag|morgenmorgenavond|morgenmiddag|morgenochtend|overmorgen|weekend|maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|maandagavond|dinsdagavond|woensdagavond|donderdagavond|vrijdagavond|zaterdagavond|zondagavond)")       
    #     today=re.compile(r"(straks|zometeen|vanmiddag|vanavond|vannacht|vandaag)",re.IGNORECASE)
    #     tomorrow=re.compile(r"(morgen|morgenavond|morgenmiddag|morgenochtend)",re.IGNORECASE)
    #     day_after_t=re.compile(r"overmorgen",re.IGNORECASE)
    #     weekend=re.compile(r"\b(weekend)\b",re.IGNORECASE)
    #     weekday=re.compile(r"(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)(avond|middag|ochtend)?",re.IGNORECASE)
    #     weekdays=["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]

    #     for instance in self.instances:
    #         ws = " ".join(instance.wordsequence)
    #         da = False
    #         if weekend.search(ws,re.IGNORECASE) or weekday.search(ws):
    #             da = True
    #             tweet_date=time_functions.return_datetime(instance.date,setting="vs")
    #             tweet_weekday=tweet_date.weekday()
    #             if weekend.search(ws):
    #                 ref_weekday=weekdays.index("zaterdag")
    #             else:
    #                 ref_weekday=weekdays.index(weekday.search(ws).groups()[0])
    #             if ref_weekday == tweet_weekday:
    #                 days_ahead = 0
    #             elif tweet_weekday < ref_weekday:
    #                 days_ahead = ref_weekday - tweet_weekday
    #             else:
    #                 days_ahead = ref_weekday + (7-tweet_weekday)
    #         elif today.search(ws):
    #             da = True
    #             days_ahead = 0
    #         elif tomorrow.search(ws):
    #             da = True
    #             days_ahead = 1
    #         elif day_after_t.search(ws):
    #             da = True
    #             days_ahead = 2

    #         if da:
    #             days_ahead = int(days_ahead)
    #             tweet_datetime = time_functions.return_datetime(instance.date,time=instance.time,setting="vs")
    #             event_datetime = tweet_datetime + datetime.timedelta(days = days_ahead)
    #             feature = "date_" + event_datetime.strftime("%d-%m-%Y")
    #             #print ws,feature                
    #             instance.features.append(feature)

    class Tweet:
        """Class containing the characteristics of a tweet that mentions an entity and time"""
        def __init__(self):
            self.id = ""
            self.user = ""

        def __init__(self,units):
            self.id = units[0]
            self.user = units[1]
            self.date = units[2]
            self.text = units[3]
            self.entities = units[4:]

        def set_date(self,date):
            self.date = date

        def set_entities(self,entities):
            self.entities = entities
