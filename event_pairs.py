
import re
import datetime
from collections import defaultdict
import itertools

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pynlpl.clients.frogclient
import colibricore
import time_functions
import calculations
import numpy

class Event_pairs:

    def __init__(self,pos):
        self.tweets = []
        if pos:
            self.fc = pynlpl.clients.frogclient.FrogClient('localhost',pos,returnall = True)

    def append_eventtweets(self,eventtweets):
        for et in eventtweets:
            info = et.strip().split("\t")
            info[2] = time_functions.return_datetime(info[2],setting="vs").date()
            info[4] = [time_functions.return_datetime(x,setting="vs").date() for x in info[4].split(" ")]
            tweet = self.Tweet()
            units = info[:5]
            units.append([x.strip() for x in info[5].split("|")])
            tweet.set_meta(units)
            if len(info) >= 7:
                tweet.set_entities([x.strip() for x in info[6].split(" | ")])            
            self.tweets.append(tweet)

    def select_date_entity_tweets(self,new_tweets,ent,ht):
        for tweet in new_tweets:
            tokens = tweet.strip().split("\t")
            if tokens[0] == "dutch" and not re.search("^RT ",tokens[-1]):
                text = tokens[-1].lower()
                date = time_functions.return_datetime(tokens[3],setting="vs").date()
                dateref_phrase = self.extract_date(text,date)
                if dateref_phrase:
                    if len(dateref_phrase) > 1:
                        chunks = dateref_phrase[0]
                        refdates = dateref_phrase[1:]
                        textparts = text.split(" ")
                        # for i,word in enumerate(textparts):
                        #     if re.search(r"^@",word):
                        #         textparts[i] = "USER"
                        #     elif re.search(r"^http://",word):
                        #         textparts[i] = "URL"
                        text = " ".join(textparts)
                        dtweet = self.Tweet()
                        units = [tokens[1],tokens[2],date,text,refdates,chunks]
                        dtweet.set_meta(units)
                        if ent:
                            entities = []
                            for chunk in chunks:
                                entities.extend(self.extract_entity(chunk,ht,ent))
                            entities = sorted(entities,key = lambda x: x[1],reverse=True)
                            if len(entities) > 0:
                                if ent == "single":
                                    dtweet.set_entities([entities[0][0]])
                                elif ent == "all":
                                    dtweet.set_entities([x[0] for x in entities])
                                elif ent == "ngram":
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

    def rank_events(self,ranking):
        date_entity_score = []
        date_entity_tweets = defaultdict(lambda : defaultdict(list))
        #count dates and entities and pairs
        date_entity = defaultdict(lambda : defaultdict(int))
        entity_count = defaultdict(int)
        date_count = defaultdict(int)
        entity_tweets = defaultdict(list)
        print("counting dates and entities")
        for tweet in self.tweets:
            for date in tweet.daterefs:
                date_count[date] += 1
                if tweet.e:
                    # if clust:
                    #     tups = calculations.extract_unique(tweet.entities)
                    #     for s in tups:
                    #         entity_count[s] += 1
                    #         date_entity[date][s] += 1
                    #         date_entity_tweets[date][s].append(tweet.text)
                    # else:
                    for entity in tweet.entities:
                        entity_count[entity] += 1
                        date_entity[date][entity] += 1
                        date_entity_tweets[date][entity].append(tweet)
                        entity_tweets[entity].append(tweet.text)

        print("calculating score")
        #for each pair
        if ranking == "fit" or ranking == "cosine":
            total = len(self.tweets)
            for date in date_entity.keys():
                #cluster entities
                for entity in date_entity[date].keys():
                    date_entity_tweets[date][entity] = list(set(date_entity_tweets[date][entity]))
                    users = len(list(set([x.user for x in date_entity_tweets[date][entity]])))
                    if len(date_entity_tweets[date][entity]) >= 5:
                        dc = date_count[date]
                        ec = entity_count[entity]
                        ode = date_entity[date][entity]
                        g2 = calculations.goodness_of_fit(total,dc,ec,ode)
                        g2_user = g2 * (users / len(date_entity_tweets[date][entity]))
                        date_entity_score.append([date,entity,g2_user,[x.text for x in date_entity_tweets[date][entity]]])
        elif ranking == "freq":
            for date in date_entity.keys():
                for entity in date_entity[date].keys():
                    date_entity_score.append([date,entity,len(date_entity_tweets[date][entity])])
        top = sorted(date_entity_score,key = lambda x: x[2],reverse=True)[:2500]
        #resolve overlap
        if ranking == "fit":
            print("resolving overlap")
            new_top = []
            merged = {}
            for i in range(len(top)):
                merged[i] = False
            for i in range(len(top)):
                if merged[i]:
                    continue
                date = top[i][0]
                entity1 = top[i][1]
                a = top[i][3]
                af = a[:5]
                for j in range(i+1,len(top)):
                    if merged[j]:
                        continue
                    #print(i,j)
                    if date == top[j][0]:    
                        entity2 = top[j][1] 
                        b = top[j][3]
                        #print("overlap")
                        if calculations.return_overlap(af,b[:5]) > 0.30:
                            #check ngram overlap 
                            #print("YES")
                            a_ngram = entity1.split()
                            b_ngram = entity2.split()
                            tweets = list(set(a+b))
                            a = tweets
                            #print("ngram")
                            if bool(set(a_ngram) & set(b_ngram)):
                                if not self.classencoder.buildpattern(entity1).unknown:
                                    entity = entity1
                                elif not self.classencoder.buildpattern(entity2).unknown:
                                    entity = entity2
                                elif len(entity1) < len(entity2):
                                    entity = entity2
                                else:
                                    entity = entity1
                            else:
                                if not self.classencoder.buildpattern(entity1 + " " + entity2).unknown:
                                    entity = entity1 + " " + entity2
                                else:
                                    entity = entity2 + " " + entity1
                           # print("done")
                            entity1 = entity
                            merged[j] = True
                new_top.append([date,entity1,top[i][2],a])
            return new_top
        elif ranking == "cosine":
            print("resolving overlap cosine style")
            documents = [" ".join(x[3]) for x in top]
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
            cos = cosine_similarity(tfidf_matrix,tfidf_matrix)
            new_top = []
            pair_sim = defaultdict(lambda : defaultdict(list))
            sim_pair = defaultdict(list)
            self.events = []
            for x in range(len(documents)):
                self.events.append(self.Event(x,top[x]))
            #agglomerative clustering
            #order pairs by similarity
            print("saving similarity scores")
            for i,document in enumerate(documents):
                for j,sim in enumerate(cos[i]):
                    pair_sim[i][j] = cos[i][j]
                    sim_pair[cos[i][j]].append([i,j]) 
            dates = list(set([x.date for x in self.events]))
            for date in dates:
                events = [x for x in self.events if x.date == date]
                indexes = [x.id[0] for x in events]
                pairs = [x for x in itertools.combinations(indexes,2)]
                print(date)
                scores = [([x[0]],[x[1]],pair_sim[x[0]][x[1]]) for x in pairs]
                #print(date,len(events),indexes,scores)
                if len(scores) > 0:
                    scores_sorted = sorted(scores,key = lambda x : x[2],reverse = True)
                    #print(scores_sorted)
                    while scores_sorted[0][2] > 0.7:
                        #print([x[2] for x in scores_sorted])
                        print(len(scores_sorted),len(events))
                        highest_sim = scores_sorted[0]
                        #merge events
                        event1 = [x for x in events if bool(set(highest_sim[0]) & set(x.id))][0]
                        event2 = [x for x in events if bool(set(highest_sim[1]) & set(x.id))][0]
                        if event1.score > event2.score:
                            event1.merge(event2)
                            events.remove(event2)
                            self.events.remove(event2)
                            event = event1
                        else:
                            event2.merge(event1)
                            events.remove(event1)
                            self.events.remove(event1)
                            event = event2
                        #recalculate similarity graph
                        all_s = []
                        remove_s = []
                        event_set = set(event.id)
                        #print(event_set)
                        for score in scores:
                            if bool(event_set & set(score[0] + score[1])):
                                remove_s.append(score)
                        for s in remove_s:
                            scores.remove(s)
                        for e in events:
                            if not bool(event_set & set(e.id)):
                                sims = [(aa, bb) for aa in event.id for bb in e.id]
                                mean_sim = numpy.mean([pair_sim[x[0]][x[1]] for x in sims])
                                scores.append((event.id,e.id,mean_sim))
                        scores_sorted = sorted(scores,key = lambda x : x[2],reverse = True)
#                        for ss in scores_sorted:
#                            if s[0] == event.id or ss[1] == event.id:
#                                print("YES!!",ss)
#                            else:
#                                print(ss)
#                        print('******************************************************************')
                        if not len(scores_sorted) > 2:
                            break
                    print([(x.id,x.entities) for x in events])
#            quit()

            # sorted_pairs = sorted(sim_pair.keys(),reverse = true)
            

            # for pair in sorted_pairs:
            #     if pair[1] > 0.7:

            #         nums = [str(x) for x in pair[0].split("_")]

            # #1: find highest similarity pair       
            #     date = top[i][0]
            #     date_matches = [(j,m) for j,m in enumerate(cos[i]) if top[j][0] == date and m > 0.7]
            #     if len(date_matches) > 0:

            #     for j,d in enumerate(cos):
            #         print(cos[i][j])
            #         if cos[i][j] > 0.7:
            #             t = top[j]
            #             if t[0] == date:
            #                 print("SIM",top[j][:2],top[i][3],top[j][3]) 
        else:
            return top

    # def pos_tweets(self,tweets):
    #     for tweet in tweets:
    #         for output in fc.process(text):
    #             if output[0] == None or (args.punct and output[3] == "LET()"):
    #                 continue
    #             else:    
    #                 if args.events:
    #                     for hashtag in events:
    #                         if re.search(output[0],hashtag):
    #                             outstring = output[0]
    #                             break
    #                 if args.ne and output[4] != "O":
    #                     cat = re.search(r"B-([^_]+)",output[4])
    #                     word = "[" + cat.groups()[0] + " " + output[0] + "]"
    #                 else:
    #                     word = output[0]
    #                 words.append(word)    
        
    #         outfields[-1] = " ".join(words)
    #         for field in outfields:
    #             if outstring == "":
    #                 outstring = field
    #             else:
    #                 try:
    #                     outstring = outstring + "\t" + field
    #                 except UnicodeDecodeError:
    #                     outstring = outstring + "\t" + field.decode("utf-8")

    #         outstring = outstring + "\n"
    #         o.put(outstring)
    #     if args.v:
    #         print "Chunk " + str(i) + " done."



    def extract_date(self,tweet,date):
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
        spec_days=["morgen","overmorgen"]

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
            r"( nog)? te gaan",r"(\b|^)" + (nums) + " " + (months) + r"( |$)" + r"(\d{2,4})?",
            r"(\b|^)(\d{1,2}-\d{1,2})(-\d{2,4})?(\b|$)",r"(\b|^)(\d{2,4}/)?(\d{1,2}/\d{1,2})(\b|$)",
            r"(\b|$)(volgende week)? ?(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|"
            "overmorgen) ?(avond|nacht|ochtend|middag)?( |$)"])

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
                    elif re.search(r"-\d{2,4}",unit) or re.search(r"\d{2,4}/",unit):
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
            output = [re.split(regexPattern, tweet)]
            if "timeunit" in nud:
                for t in nud["timeunit"]: 
                    num_match = t[1]
                    if "num" in nud:
                        days = t[0] * [x[0] for x in nud["num"] if x[1] == num_match][0]
                        try:
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
                                ds = date_vs.search(da[0] + [x[0] for x in nud["year"] if x[1] == \
                                    num_match][0]).groups()
                            else:
                                ds = date_vs.search(da[0]).groups()
                        else:
                            ds = date_vs.search(da[0]).groups()
                        dsi = [int(x) for x in ds if x != None]
                        try:
                            if dsi[0] in range(1,13) and dsi[1] in range(1,32):
                                if date < datetime.date(date.year,dsi[0],dsi[1]):
                                    output.append(datetime.date(date.year,dsi[0],dsi[1]))
                            elif dsi[0] in range(2010,2020):
                                if dsi[1] in range(1,13) and dsi[2] in range(1,32):
                                    if date < datetime.date(dsi[0],dsi[1],dsi[2]):
                                        output.append(datetime.date(dsi[0],dsi[1],dsi[2]))
                        except:
                            continue
            if "weekday" in nud:
                if not "date" in nud and not "month" in nud and not "timeunit" in nud:
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

    def extract_entity(self,text,no_hashtag,method):
        ngram_score = []
        c = text.split()
        if not no_hashtag:
            c = [x.replace("#","") for x in c]
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
            if method == "all" or method == "single":
                for ngram in ngrams:
                    ngram = " ".join(ngram)
                    pattern = self.classencoder.buildpattern(ngram)
                    if not pattern.unknown():
                        if self.dmodel[pattern] > 0.05:
                            ngram_score.append((ngram,self.dmodel[pattern]))
            elif method == "ngram":
                for ngram in ngrams:
                    ngram_score.append((" ".join(ngram),1))
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

    class Event:

        def __init__(self,index,info):
            self.id = [index]
            self.date = info[0]
            self.entities = [info[1]]
            self.score = info[2]
            self.tweets = info[3]

        def merge(self,clust):
            self.id.extend(clust.id)
            self.entities.extend(clust.entities)
            self.score = max([self.score,clust.score])
            self.tweets = list(set(self.tweets + clust.tweets))

        def resolve_overlap_entities(self):
            new_entities = []
            for entity1 in entities:
                part = False
                for entity2 in entities:
                    if entity1 < entity2:
                        if re.search(entity1,entity2):
                            part = True
                            break
                if not part:
                    new_entities.append(entity1)
            self.entities = new_entities

#        def sort_entities(self):





