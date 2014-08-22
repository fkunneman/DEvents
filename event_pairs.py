
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

    def __init__(self,action,wikidir,tmpdir,pos=False):
        self.tweets = []
        if action != "ngram":
            self.load_commonness(tmpdir + "coco",[wikidir + "1_grams.txt",wikidir + "2_grams.txt",
                wikidir + "3_grams.txt",wikidir + "4_grams.txt",wikidir + "5_grams.txt"])
        if pos:
            self.fc = pynlpl.clients.frogclient.FrogClient('localhost',pos,returnall = True)

    def detect_events(self,tweetfile):
        #start from last modeltweets
        try:
            eventfile = open("tmp/modeltweets.txt","r",encoding = "utf-8")
            self.append_eventtweets(eventfile.readlines())
            eventfile.close()
        except:
            print("no modeltweets")
        #process tweets
        self.select_date_entity_tweets(tweetfile.split("\n")[1:],"all",True,format = "twiqs")
        #prune tweets
        self.discard_last_day(30)
        #write modeltweets
        tweetinfo = open("tmp/modeltweets.txt","w",encoding = "utf-8")
        for tweet in self.tweets:
            info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
                " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks])]
            if tweet.e:
                info.append(" | ".join(tweet.entities))
            tweetinfo.write("\t".join(info) + "\n")
        tweetinfo.close()
        #rank events
        self.rank_events("cosine")
        eventdict = defaultdict(lambda : {})
        for i,event in enumerate(sorted(self.events,key = lambda x : x.score,reverse=True)):
            #print([(x.entities,x.text) for x in event.tweets])
            event_unit = {"date":event.date,"keyterms":event.entities,"score":event.score,
                "tweets":[{"id":x.id,"user":x.user,"date":x.date,"text":x.text,
                "date references":",".join([str(y) for y in x.daterefs]),
                "entities":",".join(x.entities)} for x in event.tweets]} 
            eventdict[i] = event_unit
        self.tweets = []
        self.events = []
        return eventdict

    def append_eventtweets(self,eventtweets):
        for et in eventtweets:
            info = et.strip().split("\t")
            info[2] = time_functions.return_datetime(info[2],setting="vs").date()
            info[4] = [time_functions.return_datetime(x,setting="vs").date() \
                for x in info[4].split(" ")]
            tweet = self.Tweet()
            units = info[:5]
            units.append([x.strip() for x in info[5].split("|")])
            tweet.set_meta(units)
            if len(info) >= 7:
                tweet.set_entities([x.strip() for x in info[6].split(" | ")])            
            self.tweets.append(tweet)

    def select_date_entity_tweets(self,new_tweets,ent,ht,format):
        for tweet in new_tweets:
            tokens = tweet.strip().split("\t")
            if (format == "twiqs" or (format == "exp" and tokens[0] == "dutch")) \
                    and not re.search("^RT ",tokens[-1]):
                text = tokens[-1].lower()
                if format == "exp":
                    date = time_functions.return_datetime(tokens[3],setting="vs").date()
                else:
                    date = time_functions.return_datetime(tokens[2],setting="vs").date()
                dateref_phrase = self.extract_date(text,date)
                if dateref_phrase:
                    if len(dateref_phrase) > 1:
                        chunks = dateref_phrase[0]
                        refdates = dateref_phrase[1:]
                        dtweet = self.Tweet()
                        if format == "exp":
                            units = [tokens[1],tokens[2],date,text,refdates,chunks]
                        else:
                            units = [tokens[1],tokens[6],date,text,refdates,chunks]
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
                ngramopen.close()
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

    def rank_events(self,ranking,outfile):
        outwrite = open(outfile,"w",encoding="utf-8")
        date_entity_score = []
        date_entity_tweets = defaultdict(lambda : defaultdict(list))
        date_entity_tweets_cleaned = defaultdict(lambda : defaultdict(list))
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
                    for entity in tweet.entities:
                        entity_count[entity] += 1
                        date_entity[date][entity] += 1
                        date_entity_tweets[date][entity].append(tweet)
                        entity_tweets[entity].append(tweet.text)
                        textparts = tweet.text.split(" ")
                        for i,word in enumerate(textparts):
                            if re.search(r"^http",word):
                               textparts[i] = "URL"
                        date_entity_tweets_cleaned[date][entity].append(" ".join(textparts))

        print("calculating score")
        #for each pair
        if ranking == "cosine":
            total = len(self.tweets)
            for date in date_entity.keys():
                #cluster entities
                for entity in date_entity[date].keys():
                    unique_tweets = list(set(date_entity_tweets_cleaned[date][entity]))
                    users = len(list(set([x.user for x in date_entity_tweets[date][entity]])))
                    # print(len([x.text for x in date_entity_tweets[date][entity]]),len(unique_tweets))
                    if len(unique_tweets) >= 5:
                        # print("YES")
                        dc = date_count[date]
                        ec = entity_count[entity]
                        ode = date_entity[date][entity]
                        g2 = calculations.goodness_of_fit(total,dc,ec,ode)
                        # g2_user = g2 * (users / len(date_entity_tweets[date][entity])) 
                          #print("tt",tt_ratio,"g2user",g2_user,"g2usertt",g2_user_tt,[x.text for x in date_entity_tweets[date][entity]])
                        date_entity_score.append([date,(entity,g2),g2,date_entity_tweets[date][entity]])
        elif ranking == "freq":
            for date in date_entity.keys():
                for entity in date_entity[date].keys():
                    date_entity_score.append([date,entity,len(date_entity_tweets[date][entity])])
        top = sorted(date_entity_score,key = lambda x: x[2],reverse=True)[:2500]
        print("resolving overlap")
        documents = [" ".join([y.text for y in x[3]]) for x in top]
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        cos = cosine_similarity(tfidf_matrix,tfidf_matrix)
        new_top = []
        pair_sim = defaultdict(lambda : defaultdict(list))
        self.events = []
        for x in range(len(documents)):
            self.events.append(self.Event(x,top[x]))
        #agglomerative clustering
        #order pairs by similarity
        for i,document in enumerate(documents):
            for j,sim in enumerate(cos[i]):
                pair_sim[i][j] = cos[i][j]
        dates = list(set([x.date for x in self.events]))
        for date in dates:
            events = [x for x in self.events if x.date == date]
            indexes = [x.ids[0] for x in events]
            pairs = [x for x in itertools.combinations(indexes,2)]
            scores = [([x[0]],[x[1]],pair_sim[x[0]][x[1]]) for x in pairs if pair_sim[x[0]][x[1]] > 0.5]
            if len(scores) > 0:
                scores_sorted = sorted(scores,key = lambda x : x[2],reverse = True)
                while scores_sorted[0][2] > 0.5: #scores are not static 
                    highest_sim = scores_sorted[0] #start with top
                    #merge events
                    event1 = [x for x in events if bool(set(highest_sim[0]) & set(x.ids))][0] #collect all events as part of possibly merged event
                    event2 = [x for x in events if bool(set(highest_sim[1]) & set(x.ids))][0] 
                    outwrite.write("\n" + "\t".join([str(event1.date),str(event1.score)]) + "\t" + #for checking 
                        ", ".join([x[0] for x in event1.entities]) + "\n" + 
                        "\n".join([x.text for x in event1.tweets]) + "\n" +
                        "****************\n" + "\t".join([str(event2.date),str(event2.score)]) + 
                        "\t" + ", ".join([x[0] for x in event2.entities]) + "\n" + 
                        "\n".join([x.text for x in event2.tweets]) + "\n")
                    if event1.score > event2.score: #merge to event with highest score
                        event1.merge(event2)
                        events.remove(event2)
                        self.events.remove(event2)
                        event = event1
                    else:
                        event2.merge(event1)
                        events.remove(event1)
                        self.events.remove(event1)
                        event = event2
                    all_s = []
                    remove_s = []
                    event_set = set(event.ids)
                    for score in scores:
                        print(event_set,score[0] + score[1])
                        quit()
                        if bool(event_set & set(score[0] + score[1])):
                            remove_s.append(score)
                    for s in remove_s:
                        scores.remove(s)
                    for e in events:
                        if not bool(event_set & set(e.ids)):
                            sims = [(aa, bb) for aa in event.ids for bb in e.ids]
                            mean_sim = numpy.mean([pair_sim[x[0]][x[1]] for x in sims])
                            if mean_sim > 0.5:
                                scores.append((event.ids,e.ids,mean_sim))
                    scores_sorted = sorted(scores,key = lambda x : x[2],reverse = True)
                    #print([e.entities for e in events])
                    if not len(scores_sorted) > 1:
                        break
        outwrite.close()

        documents = [" ".join([x.text for x in y.tweets]) for y in self.events]
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        word_indexes = tfidf_vectorizer.get_feature_names()
        doc_tfidf = tfidf_matrix.toarray()
        for i,event in enumerate(self.events):
            # if method = "frequency":
            #     #self.postweets = []
            #     words = defaultdict(int)
            #     for tweet in self.tweets:
            #         for word in tweet.text.split(" "):
            #             words[word] += 1
            #     for w in sorted(words.items(),key = lambda x : x[1],reverse = True)[:3]:
            #         new = True
            #         for entity in self.entities:
            #             print(w[0],entity[0])
            #             word = w[0]
            #             word = word.replace(')','\)')
            #             word = word.replace('(','\(')
            #             #print(w[0],entity[0])
            #             if re.search(word,entity[0]):
            #                 new = False
            #                 break
            #         if new:
            #             self.entities.append((word,0))
            # elif method = "commonness":

            #event.g2_rank = i+1
            #adding terms
            event.resolve_overlap_entities()
            if len(event.entities) <= 3:
                tfidf_tuples = [(j,tfidf) for j,tfidf in enumerate(doc_tfidf[i])]
                tfidf_sorted = sorted(tfidf_tuples,key = lambda x : x[1],reverse = True)
                top_terms = [word_indexes[j[0]] for j in tfidf_sorted[:3]]
                print(top_terms)
                current_entities = [x[0] for x in event.entities]
                print("before",[x[0] for x in event.entities])
                for term in top_terms:
                    ap = False
                    for tweet in event.tweets:
                        for chunk in tweet.chunks:
                            if re.search(term,chunk):
                                ap = True
                                break
                    for entity in current_entities:
                        if re.search(term,entity):
                            ap = False
                    if ap:
                        event.entities.append((term,0))
                print("after",[x[0] for x in event.entities])
            # entity_count = defaultdict(int)
            # #print("before",[x[0] for x in event.entities])
            # for tweet in event.tweets:
            #     for chunk in tweet.chunks:
            #         entities = self.extract_entity(chunk,1,"all")
            #         for entity in entities:
            #             new = True
            #             for centity in current_entities:
            #                 if re.search(entity[0],centity):
            #                     new = False
            #                     break
            #             if new:
            #                 entity_count[entity] += 1
            # for entity in entity_count.keys():
            #     if entity_count[entity] / len(event.tweets) > 0.75:
            #         event.entities.append(entity)
            #print("after",[x[0] for x in event.entities])
            event.order_entities()
            #calculate type-token
            event.add_ttratio()
        #rank events
        # tt_sorted = sorted(self.events,key = lambda x : x.tt_ratio,reverse = True)
        # for i,event in enumerate(tt_sorted):
        #     event.tt_rank = i+1
        # event_meanrank = []
        # for event in self.events:
        #     event_meanrank.append((event,numpy.mean([event.g2_rank,event.tt_rank])))
        # self.events = [x[0] for x in sorted(event_meanrank,key=lambda x : x[1])]

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
                if not "month" in nud and not "date" in nud: #overrule by more specific time indication
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
                if not "date" in nud and not "month" in nud and not "timeunit" in nud: # overrule by more specific indication
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
            elif i == 3 and method != "ngram":
                ngrams = zip(c, c[1:], c[2:], c[3:])
            elif i == 4 and method != "ngram":
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
            self.ids = [index]
            self.date = info[0]
            self.entities = [info[1]]
            self.score = info[2]
            self.tweets = info[3]

        def merge(self,clust):
            self.ids.extend(clust.ids)
            self.entities.extend(clust.entities)
            self.score = max([self.score,clust.score])
            self.tweets = list(set(self.tweets + clust.tweets))

        def resolve_overlap_entities(self):
            entities = sorted(self.entities,key = lambda x : x[1],reverse=True)
            new_entities = []
            i = 0
            while i < len(entities):
                one = False
                if i+1 >= len(entities):
                    one = True 
                else:
                    if entities[i][1] > entities[i+1][1]:
                        one = True
                overlap = False
                for e in new_entities:
                    if self.has_overlap(re.sub('#','',entities[i][0]),re.sub('#','',e[0])):
                        overlap = True
                if one:
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
                    sim_entities = sorted(sim_entities,key = lambda x : len(x[0].split(" ")))
                    for se in sim_entities:
                        overlap = False
                        for e in new_entities:
                            if self.has_overlap(se[0],e[0]):
                                overlap = True
                        if not overlap:
                            new_entities.append(se)
            self.entities = new_entities

        def has_overlap(self,s1,s2):
            if set(s1.split(" ")) & set(s2.split(" ")):
                return True
            else:
                return False

        def order_entities(self):
            entity_position = []
            for entity in self.entities:   
                positions = []
                for tweet in self.tweets:
                    if re.search(entity[0],tweet.text):
                        positions.append(tweet.text.index(entity[0]))
                entity_position.append((entity,numpy.mean(positions)))   
            ranked_positions = sorted(entity_position,key = lambda x : x[1])
            self.entities = [x[0] for x in ranked_positions]              

        def add_ttratio(self):
            tokens = []
            for tweet in self.tweets:
                tokens.extend(tweet.text.split(" ")) 
            self.tt_ratio = len(list(set(tokens))) / len(tokens)

