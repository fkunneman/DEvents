#!/usr/bin/env 

import calculations
import numpy
import re
import string
from collections import defaultdict
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
        self.extensions = []
        self.editions = []

    def add_tids(self,tids):
        self.tids = tids

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
        self.event_string = {}
        self.string_events = defaultdict(list)
        self.strings = 0
        self.event_pattern = {}
        self.pattern_events = defaultdict(list)
        self.term_sequences = defaultdict(lambda : defaultdict(list))
        self.date_terms = defaultdict(list)

    def add_event(self,event):
        #update term sequences
        for term in event.entities:
            sequence = self.term_sequences[term]
            #print("INCOMING",event.ids[0],term,event.date)
            sequence["dates"].append(event.date)
            if len(sequence["dates"]) > 1:
                #add interval
                interval = time_functions.timerel(event.date,sequence["dates"][-2],unit="day")
                #print(term,event.date,sequence["dates"][-2],interval)
                if interval == 0: #merge
                    #print("MERGE",event.entities,sequence["events"][-1].entities)
                    if event.ids[0] not in sequence["events"][-1].ids:
                        sequence["events"][-1].merge(event)
                    sequence["dates"].pop()
                    #string = self.event_string[sequence["events"][-2].ids[0]]
                    #self.event_string[event.ids[0]] = string
                    #self.string_events[string].append(event)
                else:
                    sequence["events"].append(event)
                    sequence["intervals"].append(interval)
                    if interval == 1: #link
                        #link events
                        #print("LINK",sequence["events"][-2].entities,event.entities)
                        string = self.event_string[sequence["events"][-2].ids[0]]
                        self.event_string[event.ids[0]] = string
                        self.string_events[string].append(event)
                    else:
                        sequence["merged_dates"].append(event.date)
                        merged_interval = time_functions.timerel(event.date,sequence["merged_dates"][-2],unit="day")
                        sequence["merged_intervals"].append(merged_interval)
                        try:
                            string = self.event_string[event.ids[0]]
                        except KeyError:
                            self.event_string[event.ids[0]] = self.strings
                            self.string_events[self.strings].append(event)
                            self.strings += 1
                        #print("origine",sequence["dates"],sequence["intervals"],"\nMerged",sequence["merged_dates"],sequence["merged_intervals"])
                        #if merged_interval >= 6: #score periodicity
            else:
                sequence["events"].append(event)
                sequence["merged_dates"].append(event.date)
                try:
                    string = self.event_string[event.ids[0]]
                except KeyError:
                    self.event_string[event.ids[0]] = self.strings
                    self.string_events[self.strings].append(event)
                    self.strings += 1
