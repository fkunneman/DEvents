
import re

class Event_pairs:

    def __init__(self,eventtweets):
        self.tweets = []
        if eventtweets:
            for et in eventtweets:
                tweet = Tweet(et)
                self.tweets.append(tweet)

    def extract_date(self,new_tweets):
        convert_nums = {"een":1, "twee":2, "drie":3, "vier":4, "vijf":5, "zes":6, "zeven":7, 
            "acht":8, "negen":9, "tien":10, "elf":11, "twaalf":12, "dertien":13, "veertien":14, 
            "vijftien":15, "zestien":16, "zeventien":17, "achtien":18, "negentien":19, 
            "twintig":20,"eenentwintig":21,"tweeentwintig":22,"drieentwintig":23,"vierentwintig":24,
            "vijfentwintig":25,"zesentwintig":26,"zevenentwintig":27,"achtentwintig":28,
            "negenentwintig":29,"dertig":30}
        convert_timeunit = {"dagen":1, "daagjes":1, "nachten":1, "nachtjes":1, "week": 7, "weken":7, 
            "weekjes":7, "maand": 30, "maanden":30, "maandjes":30}
        nums = (r"(\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien|elf|twaalf|dertien|" 
            "veertien|vijftien|zestien|zeventien|achtien|negentien|twintig|eenentwintig|"
            "tweeentwintig|drieentwintig|vierentwintig|vijfentwintig|zesentwintig|"
            "zevenentwintig|achtentwintig|negenentwintig|dertig)")
        timeunits = (r"(dag|dagje|dagen|daagjes|nacht|nachtje|nachten|nachtjes|week|weekje|weken|"
            "weekjes|maand|maandje|maanden|maandjes)")
        # check = re.compile(r"\b(dagen|daagjes|nachten|nachtjes|weken|weekjes|maanden|maandjes)\b",re.IGNORECASE)
        days = re.compile(r"(over|nog) (bijna |ongeveer |maar |slechts |"
            pakweg |ruim |krap |(maar )?een kleine |(maar )?iets (meer|"
            minder) dan )?" + (nums) + " " + (timeunits))
        # days1 = re.compile(r"(over|nog) pakweg " + (nums) + " " + (timeunits),re.IGNORECASE)
        # days2 = re.compile(r"nog slechts (een kleine )?" + (nums) + " " + (timeunits),re.IGNORECASE)
        days3 = re.compile((nums) + " " + (timeunits) + r"( slapen)? tot")
        days4 = re.compile(r"(met )?nog (een kleine |maar |slechts )?" + (nums) + " " + (timeunits),re.IGNORECASE)
        # days5 = re.compile(r"nog (maar )?" + (nums) + " " + (timeunits),re.IGNORECASE)
        # days6 = re.compile((nums) + " " + (timeunits) + r"( slapen)? tot",re.IGNORECASE)
        # days7 = re.compile(r"(over|nog) " + (nums) + " " + (timeunits),re.IGNORECASE)
        # days8 = re.compile(r"(over|nog) (ruim|krap|een kleine|ongeveer|bijna) " + (nums) + " " + (timeunits),re.IGNORECASE)
        days9 = re.compile(r"(over|nog) (maar |slechts |minimaal |maximaal |tenminste )?" + (nums) + " " + (timeunits),re.IGNORECASE)
        days10 = re.compile(r"met (nog)? (maar |slechts )?(1|een) (dag|week|maand|jaar)( nog)? te gaan",re.IGNORECASE)
        days11 = re.compile(r"met (nog)? (maar|slechts)?( een| 1) (dag|week|maand) te gaan",re.IGNORECASE)

        lines = []
        for tweet in new_tweets:
            text = tweet.strip().split("\t")[-1].lower()
            if days.search(text):
                lines.append(text)
            elif days3.search(text):
                lines.append(text)
        print lines,len(lines)



    # def extract_date(self):
    #     convert_nums = {"een":1, "twee":2, "drie":3, "vier":4, "vijf":5, "zes":6, "zeven":7, "acht":8, "negen":9, "tien":10, "elf":11, "twaalf":12, "dertien":13, "veertien":14, "vijftien":15, "zestien":16, "zeventien":17, "achtien":18, "negentien":19, "twintig":20}
    #     convert_month = {"jan":1, "januari":1, "feb":2, "februari":2, "mrt":3, "maart":3, "apr":4, "april":4, "mei":5, "jun":6, "juni":6, "jul":7, "juli":7, "aug":8, "augustus":8, "sep":9, "september":9, "okt":10, "oktober":10, "nov":11, "november":11, "dec":12, "december":12}
    #     dates = re.compile(r"([1,2,3]?\d|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien|elf|twaalf|dertien|veertien|vijftien|zestien|zeventien|achtien|negentien|twintig) (jan|januari|feb|februari|mrt|maart|apr|april|mei|jun|juni|jul|juli|aug|augustus|sep|september|okt|oktober|nov|november|dec|december)(\b|$)",re.IGNORECASE)
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
        def __init__(self,units):
                self.id = units[0]
                self.user = units[1]
                self.date = units[2]
                self.entities = units[3:]

        def set_date(self,date):
            self.date = date

        def set_entities(self,entities):
            self.entities = entities
