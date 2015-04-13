#!/usr/bin/env 

import numpy
import re
import string
from collections import defaultdict
import datetime
import itertools
import copy

import calculations
import time_functions

class Tweet:
    """
    Class containing the characteristics of a tweet that mentions 
        an entity and time
    """
    def __init__(self):
        self.e = False

    def set_meta(self,units,phr = False):
        self.id = units[0]
        self.user = units[1]
        self.date = units[2]
        self.text = units[3]
        if phr:
            self.phrase = units[4]
            self.daterefs = units[5]
            self.chunks = units[6]
        else:
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

    def set_phrase(self,phrase):
        self.phrase = phrase

    def set_cities(self,cities):
        if len(cities) == 0:
            self.cities = ["--"]
        else:
            self.cities = cities

class Event:
    """
    Class containing an event generated from tweets
    """
    def __init__(self,index,info):
        self.ids = [index]
        self.date = info[0]
        self.entities = info[1] #list
        self.score = info[2]
        self.tweets = info[3]
        self.periodics = []

    def add_tids(self,tids):
        self.tids = tids

    def set_periodics(self,events):
        self.periodics = events

    def merge(self,clust):
        self.ids.extend(clust.ids)
        self.entities.extend(clust.entities) 
        self.entities = list(set(self.entities))
        self.score = max([self.score,clust.score])
        self.tweets = list(set(self.tweets + clust.tweets))

    def resolve_overlap_entities(self):
        self.entities = calculations.resolve_overlap_entities(sorted(self.entities,key = lambda x : x[1],reverse=True))

    def order_entities(self):
        new_entities = calculations.order_entities([x[0] for x in self.entities],[x.text for x in self.tweets])
        new_entities_score = []
        for x in new_entities:
            entity_score = [y for y in self.entities if y[0] == x][0]
            new_entities_score.append(entity_score)
        self.entities = new_entities_score

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
            scores = []
            for chunk in tweet.chunks:
                chunk = chunk.replace('#','').replace('-',' ')
                chunk = ''.join(ch for ch in chunk if ch not in exclude)
                for word in chunk.split():
                    try:
                        wordscore = self.word_tfidf[word]
                        scores.append(wordscore)
                    except KeyError:
                        continue
            score = numpy.mean(scores)
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
                try:
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
                except:
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

class Calendar:
    """
    Class containing a set of event (clusters)
    """
    def __init__(self):
        self.events = []
        self.expected_events = [] #list of (date,eventobj,certainty)
        self.periodics = [] #dict: pattern,score,entities,events
        self.entity_sequences = defaultdict(lambda : defaultdict(list))
        self.entity_periodicity = defaultdict(lambda : {})
        #= defaultdict(lambda : defaultdict(list))
        #self.entity_calper = {}
        #self.term_counts = defaultdict(int)
        #self.cooc_counts = defaultdict(lambda : defaultdict(int))
        #self.num_docs = 0

    #TODO event merge (but not in any case)
    def add_event(self,event,stdev,calc):
        self.events.append(event)
        #make counts
        #self.num_docs += 1
        #combis = itertools.combinations(event.entities,2)
        #for comb in combis:
        #    s_comb = sorted(list(comb))
        #    self.cooc_counts[s_comb[0]][s_comb[1]] += 1
        for i,entity in enumerate(event.entities):
        #    self.term_counts[entity] += 1
            #append temporal information
            sequence = self.entity_sequences[entity]
            interval = True
            if len(sequence.keys()) > 0: #there are one or more earlier entries with the term
                #check interval
                interval = time_functions.timerel(event.date,sequence["dates_events"][-1][0],unit="day")
                if interval: #interval is more than zero days
                    sequence["intervals"].append(interval)
            if interval:
                sequence["date_info"].append([event.date,event.date.year,event.date.month,
                    event.date.isocalendar()[1],event.date.day,event.date.weekday(),
                    int(time_functions.timerel(event.date,datetime.datetime(event.date.year,\
                    event.date.month,1),"day") / 7) + 1])
                sequence["events"].append(event)
                sequence["entities"].extend([x for x in event.entities if x != entity])
                sequence["entities"] = list(set(sequence["entities"]))
                #update stdev
                if len(sequence["intervals"]) >= 2:
                    if stdev:
                        if len([x for x in sequence["intervals"] if x > 5]) == \
                            len(sequence["intervals"]):
                            stdev = calculations.return_relative_stdev(sequence["intervals"])
                            self.entity_periodicity["stdev"][entity] = [stdev,
                            list(set([x[0] for x in sequence["dates_events"]])),[event.date],
                            sequence["intervals"]]
                    if calc:
                        if not (len(sequence["intervals"]) > 15 and \
                            (sequence["intervals"].count(1) / len(sequence["intervals"])) > 0.3):
                            dateinfo = copy.deepcopy(sequence["date_info"])
                            periodicities = calculations.return_calendar_periodicities(dateinfo) 
                            if len(periodicities) > 0:
                                self.entity_periodicity["calendar"][entity] = periodicities
            sequence["dates_events"].append([event.date,event])

    def cluster_entities_periodicity(self,cluster_threshold):
        print("generating bigdocs")
        #generate bigdocs per entity
        all_entities = self.entity_sequences.keys()
        entities = self.entity_periodicity["calendar"].keys()
        entity_index = {}
        index_entity = {}
        for i,entity in enumerate(all_entities):
            entity_index[entity] = i
            index_entity[i] = entity
        documents = []
        for entity in all_entities:
            documents.append(" ".join([" ".join(x.tweets) for \
                x in self.entity_sequences[entity]["events"]]))
        vectors = calculations.tfidf_docs(documents)
        print("calculating similarities")
        pairsims = calculations.return_similarities(vectors,vectors)
        print("grouping entities")
        #group entities
        pattern_entities = defaultdict(list)
        patterns = []
        for entity in entities:
            entity_patterns = [x[-1] for x in self.entity_periodicity["calendar"][entity]]
            patterns.extend(entity_patterns)
            for pattern in entity_patterns:
                pattern_entities[pattern].append(entity)
        patterns = list(set(patterns))
        for pattern in patterns:
            ents = list(set(pattern_entities[pattern]))
            #print(pattern,ents)
            if len(ents) > 1:
                # print(">1")
                indices = [entity_index[x] for x in ents]
                clusters = calculations.cluster_documents(pairsims,indices,cluster_threshold)
                groups = []
                for cluster in clusters:
                    groups.append([index_entity[x] for x in cluster])
            else:
                groups = [ents]
            #print(pattern,[g for g in groups if len(g) > 1])
            print(groups)
            for group in groups:
                if len(group) > 1: #rescore periodicity
                    all_dates = []
                    periodic_dates = []
                    events = []
                    event_ids = []
                    for entity in group:
                        dates_events = self.entity_sequences[entity]["dates_events"]
                        all_dates.extend([x[0] for x in dates_events])
                        for e in [x[1] for x in dates_events]:
                            if not e.ids[0] in event_ids:
                                event_ids.append(e.ids[0])
                                events.append(e)
                        periodic = [x for x in self.entity_periodicity["calendar"][entity] if \
                            x[7] == pattern][0]
                        periodic_dates.extend(periodic[5])
                    listpattern = pattern[1:-1].split(",")
                    unique_dates = []
                    unique_periodic_dates = []
                    for pd in periodic_dates:
                        if not pd[0] in unique_dates:
                            unique_periodic_dates.append(pd)
                            unique_dates.append(pd[0])
                    events = [x for x in events if x.date in unique_dates]
                    print(group)                     
                    new_periodic = calculations.score_calendar_periodicity(listpattern,
                        copy.deepcopy(unique_periodic_dates),len(list(set(all_dates))))
                else:
                    print(group)
                    new_periodic = [x for x in self.entity_periodicity["calendar"][group[0]] if \
                                x[7] == pattern][0]
                    unique_dates = list(set([x[0] for x in new_periodic[5]]))
                    events = [x[1] for x in self.entity_sequences[group[0]]["dates_events"] if \
                        x[1].date in unique_dates] 
                self.periodics.append({"score":new_periodic[0],"coverage":new_periodic[1],
                    "consistency":new_periodic[2],"step":new_periodic[3],"len":new_periodic[4],
                    "dates":new_periodic[5],"gaps":new_periodic[6],"pattern":pattern,
                    "events":events,"entities":group})

    def predict_events(until_date,threshold):
        #select above threshold patterns
        good_periodics = [p for p in self.periodics if p["score"] > threshold]
        #for each pattern
        for periodic in good_periodics:
            last_date = max(sorted([e.date for e in periodic["events"]]))
            extensions = calculations.extract_future_dates(periodic["pattern"],
                last_date,until_date) #list of future dates
            for date in extensions:
                event = Event("x",[date,periodic["entities"],"-",[]])
                event.set_periodics(periodic["events"])
                expected_events.append(event)
