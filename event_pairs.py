
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

class Event_pairs:

    def __init__(self,wikidir=False,tmpdir=False,t=False):
        self.tweets = []
        self.tmpdir = tmpdir
        if wikidir:
            self.load_commonness(self.tmpdir + "coco",[wikidir + "1_grams.txt",wikidir + "2_grams.txt",
                wikidir + "3_grams.txt",wikidir + "4_grams.txt",wikidir + "5_grams.txt"])
        c = "/vol/customopt/uvt-ru/etc/frog/frog-twitter.cfg"
        if t:
            fo = frog.FrogOptions(threads=t)
        else:
            fo = frog.FrogOptions()
        self.frogger = frog.Frog(fo,c)
        self.ucto_settingsfile = "/vol/customopt/uvt-ru/etc/ucto/tokconfig-nl-twitter"

    def detect_events(self,tweetfile):
        #start from last modeltweets
        try:
            eventfile = open("tmp/modeltweets.txt","r",encoding = "utf-8")
            self.append_eventtweets(eventfile.readlines())
            eventfile.close()
        except:
            print("no modeltweets")
        #process tweets
        self.select_date_entity_tweets(tweetfile.split("\n")[1:],format = "twiqs")
        #prune tweets
        self.discard_last_day(30)
        #write modeltweets
        tweetinfo = open("tmp/modeltweets.txt","w",encoding = "utf-8")
        for tweet in self.tweets:
            info = [tweet.id,tweet.user,str(tweet.date),tweet.text,
                " ".join([str(x) for x in tweet.daterefs]),"|".join([x for x in tweet.chunks]),
                " | ".join(tweet.entities)," | ".join(",".join(x) for x in tweet.postags)]
            tweetinfo.write("\t".join(info) + "\n")
        tweetinfo.close()
        #rank events, resolve overlap and enrich events
        self.rank_events("csx")
        self.resolve_overlap_events()
        self.enrich_events("csx")
        #output events
        eventdict = defaultdict(lambda : {})
        for i,event in enumerate(sorted(self.events,key = lambda x : x.score,reverse=True)):
            event_unit = {"date":event.date,"keyterms":event.entities,"score":event.score,
                "tweets":[{"id":x.id,"user":x.user,"da§te":x.date,"text":x.text,
                "date references":",".join([str(y) for y in x.daterefs]),
                "entities":",".join(x.entities),"postags":" | ".join(",".join(x) for x in tweet.postags)} for x in event.tweets]} 
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
            units.append([x.strip() for x in info[5].split("|")]) #chunks
            tweet.set_meta(units)
            if len(info) >= 7:
                entities = [x.strip() for x in info[6].split(" | ")]
                if len(entities) == 1 and entities[0] == "--":
                    tweet.set_entities([])
                else:
                    tweet.set_entities(entities)
                if len(info) == 8:
                    postags = [tuple(x.split(",")) for x in info[7].split(" | ")]
                    if len(postags) == 1 and postags[0][0] == "--":
                        tweet.set_postags([])
                    else:
                        tweet.set_postags(postags)
                else:
                    tweet.set_postags([])
            else:
                tweet.set_entities([])
                tweet.set_postags([])
            self.tweets.append(tweet)

    def select_date_entity_tweets(self,new_tweets,format):
        tokenizer = ucto.Tokenizer(self.ucto_settingsfile)
        for tweet in new_tweets:
            tokens = tweet.strip().split("\t")
            if (format == "twiqs" or (format == "exp" and tokens[0] == "dutch")) \
                    and not re.search(r"\bRT\b",tokens[-1]):
                tokenizer.process(tokens[-1])
                text = " ".join([x.text.lower() for x in tokenizer])
                if format == "exp":
                    date = time_functions.return_datetime(tokens[3],setting="vs").date()
                else:
                    try:
                        date = time_functions.return_datetime(tokens[2],setting="vs").date()
                    except:
                        print("dateerror",tweet,tokens)
                dateref_phrase = calculations.extract_date(text,date,self.frogger)
                if dateref_phrase:
                    if len(dateref_phrase) > 1:
                        chunks = dateref_phrase[0]
                        refdates = dateref_phrase[1:]
                        dtweet = self.Tweet()
                        dtweet.set_postags(calculations.return_postags(text,self.frogger))
                        if format == "exp":
                            units = [tokens[1],tokens[2],date,text,refdates,chunks]
                        else:
                            units = [tokens[1],tokens[6],date,text,refdates,chunks]
                        dtweet.set_meta(units)
                        entities = []
                        if self.tmpdir:
                            for chunk in chunks:
                                entities.extend(calculations.extract_entity(chunk,self.classencoder,self.dmodel))
                        else:
                            for chunk in chunks:
                                entities.extend(calculations.extract_entity(chunk))
                        entities = sorted(entities,key = lambda x: x[1],reverse=True)
                        if len(entities) > 0:
                            dtweet.set_entities([x[0] for x in entities])
                        else:
                            dtweet.set_entities([])
                        #add hashtags to process
                        for chunk in chunks:
                            hashtags = [x for x in chunk.split(" ") if re.search(r"^#",x) and len(x) > 1]
                            if len(hashtags) > 0:
                                if dtweet.e:
                                    dtweet.entities.extend(hashtags)
                                else:
                                    dtweet.set_entities(hashtags)
                        self.tweets.append(dtweet)
                       
    def rank_events(self,method):
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
        #for each pair
        total = len(self.tweets)
        for date in date_entity.keys():
            #cluster entities
            for entity in date_entity[date].keys():
                unique_tweets = list(set(date_entity_tweets_cleaned[date][entity]))
                if len(unique_tweets) >= 5:
                    dc = date_count[date]
                    ec = entity_count[entity]
                    ode = date_entity[date][entity]
                    g2 = calculations.goodness_of_fit(total,dc,ec,ode)
                    users = [x.user for x in date_entity_tweets[date][entity]]
                    g2_user = (len(list(set(users))) / len(users)) * g2
                    date_entity_score.append([date,(entity,g2_user),g2_user,date_entity_tweets[date][entity]])
        if method == "ngrams":
            top = sorted(date_entity_score,key = lambda x: x[2],reverse=True)[:7500]    
        else:
            top = sorted(date_entity_score,key = lambda x: x[2],reverse=True)[:2500]    
        self.events = []
        for x in range(len(top)):
            self.events.append(self.Event(x,top[x]))
        print("rank",len(self.events))

    def resolve_overlap_events(self,outfile = False):
        if outfile:
            outwrite = open(outfile,"w",encoding="utf-8")
        documents = [" ".join([y.text for y in x.tweets]) for x in self.events]
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        cos = cosine_similarity(tfidf_matrix,tfidf_matrix)
        pair_sim = defaultdict(lambda : defaultdict(list))
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
            scores = [([x[0]],[x[1]],pair_sim[x[0]][x[1]]) for x in pairs if pair_sim[x[0]][x[1]] > 0.7]
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
                    #to check clustering performance
                    if outfile:
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
                    for score in scores: #remove event sets that contain the same event(s)
                        if bool(event_set & set(score[0] + score[1])): 
                            remove_s.append(score)
                    for s in remove_s:
                        scores.remove(s)
                    for e in events: #add new similarities as mean of the similarity between seperate events
                        if not bool(event_set & set(e.ids)):
                            sims = [(aa, bb) for aa in event.ids for bb in e.ids]
                            mean_sim = numpy.mean([pair_sim[x[0]][x[1]] for x in sims])
                            scores.append((event.ids,e.ids,mean_sim))
                    scores_sorted = sorted(scores,key = lambda x : x[2],reverse = True) #resort scores
                    if not len(scores_sorted) > 1:
                        break
        if outfile:
            outwrite.close()
        print("overlap",len(self.events))

    def enrich_events(self,method,xpos = False):
        documents = [" ".join([" ".join(x.chunks) for x in y.tweets]) for y in self.events]
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        word_indexes = tfidf_vectorizer.get_feature_names()
        doc_tfidf = tfidf_matrix.toarray()
        #for each event
        for i,event in enumerate(self.events):
            event.resolve_overlap_entities() #resolve overlap
            tfidf_tuples = [(j,tfidf) for j,tfidf in enumerate(doc_tfidf[i])]
            tfidf_sorted = sorted(tfidf_tuples,key = lambda x : x[1],reverse = True)
            event.add_tfidf(tfidf_sorted,word_indexes)
            if method == "csx": #add terms
                top_terms = [word_indexes[j[0]] for j in tfidf_sorted][:5]
                term_postag_counts = defaultdict(lambda : defaultdict(int))
                #acquire most frequent postag for each term (provided postag is a verm, adjective or noun)
                for tweet in event.tweets:
                    #print(tweet,xpos)
                    if xpos:
                        tweet.set_postags(calculations.return_postags(tweet.text,self.frogger))
                    for postag in tweet.postags:
                        term_postag_counts[postag[0]][postag[1]] += 1 
                new_candidates = [x for x in term_postag_counts.keys() if x in top_terms]          
                #remove term that is already in entity set
                current_entities = [x[0] for x in event.entities]
                for term in top_terms:
                    ap = True
                    for entity in current_entities:
                        if re.search(term,entity) or not term in new_candidates:
                            ap = False
                    if ap:
                        event.entities.append((term,0))
            event.order_entities() #order entities by their average position in the tweets
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

        def set_entities(self,entities):
            if len(entities) == 0:
                self.entities = ["--"]
            else:
                self.entities = entities
                self.e = True

        def set_postags(self,tags):
            if len(tags) == 0:
                self.postags = [("--","--")]
            else:
                self.postags = tags

    class Event:
        """
        Class containing an event generated from tweets
        """
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
                    if re.search(re.escape(entity[0]),tweet.text):
                        positions.append(re.search(re.escape(entity[0]),tweet.text).span()[0])
                entity_position.append((entity,numpy.mean(positions)))   
            ranked_positions = sorted(entity_position,key = lambda x : x[1])
            self.entities = [x[0] for x in ranked_positions]    

        def add_ttratio(self):
            tokens = []
            for tweet in self.tweets:
                tokens.extend(tweet.text.split(" ")) 
            self.tt_ratio = len(list(set(tokens))) / len(tokens)

        def add_tfidf(self,sorted_tfidf,w_indexes):
            self.word_tfidf = {}
            sorted_word_tfidf = [(w_indexes[x[0]],x[1]) for x in sorted_tfidf if x[1] > 0]
            for word_score in sorted_word_tfidf:
                self.word_tfidf[word_score[0]] = word_score[1]

        def rank_tweets(self,rep = False):
            tweet_score = []
            exclude = set(string.punctuation)
            for tweet in self.tweets:
                score = 0
                for chunk in tweet.chunks:
                    chunk = chunk.replace('#','').replace('-',' ')
                    chunk = ''.join(ch for ch in chunk if ch not in exclude)
                    for word in chunk.split():
                        try:
                            wordscore = self.word_tfidf[word]
                            score += wordscore
                        except KeyError:
                            continue
                tweet_score.append((tweet.text,score))
            if rep:
                self.reptweets = []
                noadds = []
                ht = re.compile(r"^#")
                usr = re.compile(r"^@")
                url = re.compile(r"^http")
                for x in sorted(tweet_score,key = lambda x : x[1],reverse=True):
                    add = True
                    content = [x for x in x[0].split() if not ht.search(x) and not usr.search(x) and not url.search(x)]
                    for rt in self.reptweets:
                        overlap = len(set(content) & set(rt[1])) / max(len(set(content)),len(set(rt[1])))
                        if overlap > 0.8:              
                            add = False
                            noadds.append(x[0])
                            break
                    if add:
                        self.reptweets.append((x[0],content))
                    if len(self.reptweets) == 5:
                        break
                self.reptweets = [x[0] for x in self.reptweets]
                if len(self.reptweets) < 5:
                    for rt in noadds:
                        self.reptweets.append(rt)
                        if len(self.reptweets) == 5:
                            break
                nreptweets = []
                for x in self.reptweets:
                    tweetwords = []
                    for word in x.split():
                        if url.search(word):
                            word = "URL"
                        tweetwords.append(word)
                    nreptweets.append(" ".join(tweetwords))
                self.reptweets = nreptweets
