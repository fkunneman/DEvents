
import re
import datetime
from collections import defaultdict
import itertools
import string

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy
import frog
import ucto
import colibricore
import time_functions
import calculations

import event_classes

class Event_pairs:

    def __init__(self,wikidir=False,tmpdir=False,f = False, cities=False):
        self.tweets = []
        self.tmpdir = tmpdir
        if wikidir:
            self.load_commonness(self.tmpdir + "coco",[wikidir + "1_grams.txt",wikidir + "2_grams.txt",
                wikidir + "3_grams.txt",wikidir + "4_grams.txt",wikidir + "5_grams.txt"])
        if cities:
            cityfile = open(cities,"r",encoding='iso-8859-1')
            cts = [x.strip().lower() for x in cityfile.read().split("\n")]
            cityfile.close()
            li = sorted(cts, key=len, reverse=True)
            li = [tx.replace('.','\.').replace('*','\*') for tx in li] # not to match anything with . (dot) or *
            self.cities = re.compile('\\b' + '\\b|\\b'.join(li) + '\\b')
        else:
            self.cities = False
        if f:
            c = "/vol/customopt/uvt-ru/etc/frog/frog-twitter.cfg"
            fo = frog.FrogOptions()
            self.frogger = frog.Frog(fo,c)
        else:
            self.frogger = False
        self.ucto_settingsfile = "/vol/customopt/uvt-ru/etc/ucto/tokconfig-nl-twitter"

    #total procedure of event extraction in one function
    def detect_events(self,tweetfile,events = True):
        #start from last modeltweets
        print("appending modeltweets")
        eventfile = open(self.tmpdir + "modeltweets.txt","r",encoding = "utf-8")
        self.append_eventtweets(eventfile.readlines())
        eventfile.close()
        #process tweets
        print("processing new tweets")
        self.select_date_entity_tweets(tweetfile.split("\n")[1:])
        #prune tweets
        self.discard_last_day(31)
        #write modeltweets
        self.write_modeltweets(self.tmpdir + "modeltweets.txt")
        if events:
            #rank events, resolve overlap and enrich events
            self.rank_events()
            self.write_term_scores(self.tmpdir + "term_scores.txt")
            self.resolve_overlap_events()
            self.enrich_events()
            #output events
            eventdict = []
            for i,event in enumerate(sorted(self.events,key = lambda x : x.score,reverse=True)):
                if event.tt_ratio > 0.30:
                    event.rank_tweets(rep=True)
                    event_unit = {"date":event.date,"keyterms":event.entities,"score":event.score,
                        "tweets":[{"id":x.id,"user":x.user,"date":x.date,"text":x.text,
                        "date references":",".join([str(y) for y in x.daterefs]),
                        "entities":",".join(x.entities),
                        "postags":" | ".join(",".join(y) for y in x.postags)} for x in event.tweets]} 
                    eventdict.append(event_unit)
        else:
            eventdict = []
        self.tweets = []
        self.events = []
        return eventdict

    #load an existing model of event tweets
    def append_eventtweets(self,eventtweets):
        tokenizer = ucto.Tokenizer(self.ucto_settingsfile)
        for et in eventtweets:
            ent = False
            info = et.strip().split("\t")
            try:
                #set information to the right field given different inputs
                if len(info) > 12:
                    ent = True
                    if re.search(r"\d{1}(/|-)\d{1}",info[13]):
                        continue
                    else:
                        pattern = [(True,1),(True,4),(True,7),(True,10),(True,11),(True,12),
                            (False,0),(False,0),(True,13),(False,0)]
                else:
                    if re.match(r"\d{4}-\d{2}-\d{2}",info[4]):
                        pattern = [(True,0),(True,1),(True,2),(True,3),(True,4),(True,5),(True,6),
                            (True,7),(True,8),(True,9)]
                    else:
                        pattern = [(True,0),(True,1),(True,2),(True,3),(True,5),(True,6),(True,7),
                            (True,8),(True,4),(True,9)]           
                    if len(info) < 10:
                        pattern[9] = (False,0)
                        if len(info) < 9:
                            if pattern[8][1] == 8:
                                pattern[8] = (False,0)
                            else:
                                pattern[7] = (False,0)
                            if len(info) < 8:
                                if pattern[7][1] == 7:
                                    pattern[7] = (False,0)
                                else:
                                    pattern[6] = (False,0)
                                if len(info) < 7:
                                    pattern[6] = (False,0)
                #write fields to a tweet object
                fields = []
                for field in pattern:
                    if field[0]:
                        fields.append(info[field[1]])
                    else:
                        fields.append([])
                fields[2] = time_functions.return_datetime(fields[2],setting="vs").date() #tweetdate
                fields[4] = [time_functions.return_datetime(x,setting="vs").date() \
                            for x in fields[4].split(" ")] #refdates
                fields[5] = [x.strip() for x in fields[5].split("|")] #chunks
                if len(fields[6]) > 0:
                    fields[6] = [x.strip() for x in fields[6].split(" | ")] #entities
                    if len(fields[6]) == 1 and fields[6][0] == "--":
                        fields[6] = []
                if len(fields[7]) > 0:
                    fields[7] = [tuple(x.split(",")) for x in fields[7].split(" | ")] #postags
                    if len(fields[7]) == 1 and fields[7][0][0] == "--":
                        fields[7] = []
                if len(fields[9]) > 0:
                    fields[9] = fields[9].split(", ") #cities
                tweet = event_classes.Tweet()
                tweet.set_meta(fields[:6])
                tweet.set_entities(fields[6])
                tweet.set_postags(fields[7])
                tweet.set_phrase(fields[8])
                tweet.set_cities(fields[9])
                if ent:
                    if self.cities:
                        citymatch = calculations.return_cities(tweet.chunks,self.cities)
                        tweet.chunks = citymatch[0]
                        tweet.set_cities(citymatch[1])
                    if self.frogger: 
                        tweet.set_postags(calculations.return_postags(tweet.text,self.frogger))
                    entities = []
                    new_chunks = []
                    for chunk in tweet.chunks:
                        tokenizer.process(chunk)
                        chunk = " ".join([x.text.lower() for x in tokenizer])
                        new_chunks.append(chunk)
                    tweet.chunks = new_chunks
                    for chunk in tweet.chunks:
                        entities.extend(calculations.extract_entity(chunk,self.classencoder,self.dmodel))
                    entities = sorted(entities,key = lambda x: x[1],reverse=True)
                    for chunk in tweet.chunks:
                        entities.extend([(x,0) for x in chunk.split(" ") if re.search(r"^#",x) and len(x) > 1])
                    tweet.set_entities([x[0] for x in entities])
                self.tweets.append(tweet)
            except:
              continue
        print(len(self.tweets),"tweets")

    #extract temporal information and entities from tweets
    def select_date_entity_tweets(self,new_tweets):
        tokenizer = ucto.Tokenizer(self.ucto_settingsfile)
        for tweet in new_tweets:
            tokens = tweet.strip().split("\t")
            tokenizer.process(tokens[-1])
            text = " ".join([x.text.lower() for x in tokenizer])
            try:
                date = time_functions.return_datetime(tokens[2],setting="vs").date()
            except:
                print("dateerror",tweet,tokens)
            dateref_phrase = calculations.extract_date(text,date)
            if dateref_phrase:
                if len(dateref_phrase) > 2:
                    dtweet = event_classes.Tweet()
                    chunks = dateref_phrase[0]
                    if self.cities:
                        citymatch = calculations.return_cities(chunks,self.cities)
                        chunks = citymatch[0]
                        cities = citymatch[1]
                        dtweet.set_cities(cities)
                    units = [tokens[1],tokens[6],date,text,dateref_phrase[2:],chunks]
                    dtweet.set_meta(units)
                    dtweet.set_phrase(dateref_phrase[1])
                    if self.frogger:
                        dtweet.set_postags(calculations.return_postags(text,self.frogger))
                    else:
                        dtweet.set_postags([])
                    entities = []
                    for chunk in chunks:
                        entities.extend(calculations.extract_entity(chunk,self.classencoder,self.dmodel))
                    entities = sorted(entities,key = lambda x: x[1],reverse=True)
                    for chunk in chunks:
                        entities.extend([(x,0) for x in chunk.split(" ") if re.search(r"^#",x) and len(x) > 1])
                    dtweet.set_entities([x[0] for x in entities])
                    self.tweets.append(dtweet)
                       
    #find probable events from date_entity pairs
    def rank_events(self):
        date_entity_score = []
        date_entity_tweets = defaultdict(lambda : defaultdict(list))
        date_entity_tweets_cleaned = defaultdict(lambda : defaultdict(list))
        #count dates and entities and pairs
        date_entity = defaultdict(lambda : defaultdict(int))
        entity_count = defaultdict(int)
        date_count = defaultdict(int)
        for tweet in self.tweets:
            for date in tweet.daterefs:
                date_count[date] += 1
                if tweet.e:
                    for entity in tweet.entities:
                        entity_count[entity] += 1
                        date_entity[date][entity] += 1
                        date_entity_tweets[date][entity].append(tweet)
                        textparts = tweet.text.split(" ")
                        for i,word in enumerate(textparts):
                            if re.search(r"^http",word):
                               textparts[i] = "URL"
                        date_entity_tweets_cleaned[date][entity].append(" ".join(textparts))
        #calculate goodness of fit
        total = len(self.tweets)
        for date in date_entity.keys():
            for entity in date_entity[date].keys():
                unique_tweets = list(set(date_entity_tweets_cleaned[date][entity]))
                if len(unique_tweets) >= 5:
                    dc = date_count[date]
                    ec = entity_count[entity]
                    ode = date_entity[date][entity]
                    g2 = calculations.goodness_of_fit(total,dc,ec,ode)
                    # users = [x.user for x in date_entity_tweets[date][entity]]
                    # g2_user = (len(list(set(users))) / len(users)) * g2
                    date_entity_score.append([date,[(entity,g2)],g2,date_entity_tweets[date][entity]])
        top = sorted(date_entity_score,key = lambda x: x[2],reverse=True)[:2500]
        self.events = []
        for x in range(len(top)):
            self.events.append(event_classes.Event(x,top[x]))
        print("rank",len(self.events))

    def resolve_overlap_events(self):
        documents = calculations.tfidf_docs([" ".join([y.text for y in x.tweets]) for x in self.events])
        pairsims = calculations.return_similarities(documents,documents)
        dates = list(set([x.date for x in self.events]))
        for date in dates:
            events = [x for x in self.events if x.date == date]
            indexes = [x.ids[0] for x in events]
            pairs = [x for x in itertools.combinations(indexes,2)]
            scores = [([x[0]],[x[1]],pairsims[x[0]][x[1]]) for x in pairs if pairsims[x[0]][x[1]] > 0.7]
            if len(scores) > 0:
                scores_sorted = sorted(scores,key = lambda x : x[2],reverse = True)
                while scores_sorted[0][2] > 0.7: #scores are not static 
                    highest_sim = scores_sorted[0] #start with top
                    #merge events
                    for x in events: #collect the event that matches the id list
                        if highest_sim[0] == x.ids: 
                            event1 = x
                        if highest_sim[1] == x.ids:
                            event2 = x
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
                    for score in scores: #remove event sets that contain the same event(s)
                        if bool(event_set & set(score[0] + score[1])): 
                            remove_s.append(score)
                    for s in remove_s:
                        scores.remove(s)
                    for e in events: #add new similarities as mean of the similarity between seperate events
                        if not bool(event_set & set(e.ids)):
                            sims = [(aa, bb) for aa in event.ids for bb in e.ids]
                            mean_sim = numpy.mean([pairsims[x[0]][x[1]] for x in sims])
                            scores.append((event.ids,e.ids,mean_sim))
                    scores_sorted = sorted(scores,key = lambda x : x[2],reverse = True) #resort scores
                    if not len(scores_sorted) > 1:
                        break
        print("overlap",len(self.events))

    def enrich_events(self,add=True,xpos = False,order = True):
        documents = [" ".join([" ".join(x.chunks) for x in y.tweets]) for y in self.events]
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        word_indexes = tfidf_vectorizer.get_feature_names()
        doc_tfidf = tfidf_matrix.toarray()
        #for each event
        for i,event in enumerate(self.events):
            event.resolve_overlap_entities() #resolve overlap
            if add:
                tfidf_tuples = [(j,tfidf) for j,tfidf in enumerate(doc_tfidf[i])]
                tfidf_sorted = sorted(tfidf_tuples,key = lambda x : x[1],reverse = True)
                event.add_tfidf(tfidf_sorted,word_indexes)
                top_terms = [word_indexes[j[0]] for j in tfidf_sorted][:4]
                term_postag_counts = defaultdict(lambda : defaultdict(int))
                #acquire most frequent postag for each term (provided postag is a verb, adjective or noun)
                for tweet in event.tweets:
                    if xpos:
                        tweet.set_postags(calculations.return_postags(tweet.text,self.frogger))
                    for postag in tweet.postags:
                        term_postag_counts[postag[0]][postag[1]] += 1 
                new_candidates = [x for x in term_postag_counts.keys() if x in top_terms]          
                #remove term that is already in entity set
                current_entities = [x[0] for x in event.entities]
                for term in top_terms:
                    if not (re.match("~",term) or re.match(r"\d+",term)):
                        ap = True
                        for entity in current_entities:
                            if re.search(term,entity) or not term in new_candidates:
                                ap = False
                        if ap:
                            event.entities.append((term,0))
            if self.cities:
                #check if city in terms
                places = defaultdict(int)
                total = 0
                for t in event.tweets:
                    for city in t.cities:
                        if not (city == "nederland" or city == "--"):
                            places[city] += 1
                            total += 1
                if len(places.keys()) > 0:
                    top_place = sorted(places, key=places.get, reverse=True)[0]
                    if places[top_place]/total > 0.8:
                        event.entities.append((top_place,0)) 
            if order:
                event.order_entities()
                event.add_ttratio() #calculate type-token to erase events with highly simplified tweets
        print("enrich",len(self.events))

    def discard_last_day(self,window):
        days = sorted(set([x.date for x in self.tweets]))
        size = len(days)
        while size > window:
            ld = days[0]
            self.tweets = [t for t in self.tweets if t.date != ld]
            days = sorted(set([x.date for x in self.tweets]))
            size = len(days)
        print(len(self.tweets),"tweets")

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

    def write_modeltweets(self,outfile):
        tweetinfo = open(outfile,"w",encoding = "utf-8")
        for tweet in self.tweets:
            info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
                    " ".join([str(x) for x in tweet.daterefs]),
                    "|".join([x for x in tweet.chunks]),
                    " | ".join(tweet.entities)]
            if hasattr(tweet, 'postags'):
                info.append(" | ".join(",".join(x) for x in tweet.postags))
            else:
                info.append(",".join("--","--"))
            if hasattr(tweet, 'phrase'):
                info.append(tweet.phrase)
            else:
                info.append("-")
            if hasattr(tweet, "cities"):
                info.append(", ".join(tweet.cities))
            else:
                info.append("-")
            print(info)
            tweetinfo.write("\t".join(info) + "\n")
        tweetinfo.close()

    def write_term_scores(self,outfile):
        terminfo = open(outfile,"w",encoding = "utf-8")
        for event in self.events:
            terminfo.write(event.entities[0][0] + "\t" + str(event.score) + "\n")
        terminfo.close()
