#!/usr/bin/env 

import numpy
import re
import string
from collections import defaultdict
import datetime

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
        # self.event_pattern = {}
        # self.pattern_events = defaultdict(list)
        self.entity_sequences = defaultdict(lambda : defaultdict(list))
        #self.date_terms = defaultdict(list)
        self.periodicities = []
        self.term_stdev = defaultdict(lambda : defaultdict(list))


    #TODO event merge (but not in any case)
    def add_event(self,event):
        for i,entity in enumerate(event.entities):
            #date_terms[event.date].append(entity)
            add = True
            sequence = self.entity_sequences[entity]
            if len(sequence.keys()) > 0: #there are one or more earlier entries with the term
                #check interval
                interval = time_functions.timerel(event.date,sequence["dates"][-1],unit="day")
                if interval == 0:
                    add = False
                else:
                    sequence["intervals"].append(interval)
                    #minimum requirement for periodicity
                    if len(sequence["intervals"]) >= 2 and \
                        len([x for x in sequence["intervals"] if x > 5]) == \
                        len(sequence["intervals"]):
                        """
                        options:
                        - interval stdev (baseline)
                        - segment stdev
                        - segment periodicity
                        - remove / insert by date patterns
                        """
                        stdev = calculations.return_relative_stdev(sequence["intervals"])
                        self.term_stdev[entity][0] = [stdev,sequence["dates"] + \
                            [event.date],sequence["intervals"]]



    #                     if len(sequence["last_periodic"]) > 0:
    #                         last_periodic = sequence["last_periodic"]
    #                         index = last_periodic[0]
    #                         stdev = last_periodic[1]
    #                         intervals = sequence["intervals"][last_periodic[2]:last_periodic[3]]
    #                         if last_periodic[3] == len(sequence["intervals"]): #periodicity until last date
    #                             stdev = calculations.return_relative_stdev(sequence["intervals"])
    #                             if stdev < 10: #update current sequence
    #                                 #self.term_stdev[term][index] = [stdev,", ".join([str(x) for x in sequence["merged_dates"][last_periodic[2]:last_periodic[3]+1]]),",".join([str(x) for x in intervals + [merged_interval]])]
    #                                 self.term_stdev[term][index] = [stdev,sequence["dates"][last_periodic[2]:last_periodic[3]+1] + event.date,intervals + interval]
    #                                 sequence["last_periodic"] = [index,stdev,last_periodic[2],last_periodic[3]+1]
    #                         else:
    #                             if len(sequence["intervals"]) - last_periodic[3] <= 3: #maximum 2 intervals before
    #                                 #merge intervals in gap (possibly outliers)
    #                                 stdev = calculations.return_relative_stdev(intervals + [sum(sequence["merged_intervals"][last_periodic[3]:])])
    #                                 if stdev < 10:
    #                                     #break gap from dates and intervals
    #                                     #sequence["merged_dates"] = sequence["merged_dates"][:last_periodic[3]+1] + [event.date]
    #                                     #sequence["merged_intervals"] = sequence["merged_intervals"][:last_periodic[3]+1] + [sum(sequence["merged_intervals"][last_periodic[3]+1:])]
    #                                     #update current sequence
    #                                     self.term_stdev[term][index] = [stdev,sequence["dates"][last_periodic[2]:last_periodic[3]+1] + event.date,intervals + interval]
    #                                     sequence["last_periodic"] = [index,stdev,last_periodic[2],last_periodic[3]+1]
    #                                     #continue
    # #                            intervals = sequence["merged_intervals"][last_periodic[3]:]
    #                             intervals = sequence["intervals"][last_periodic[3]:]
    #                             if len(intervals) >= 2: #find best periodicity
    #                                 scores = []
    #                                 for i in range(len(intervals[:-1])):
    #                                     seq = intervals[i:]
    #                                     scores.append([i,calculations.return_relative_stdev(seq)])
    #                                 best = sorted(scores,key = lambda x : x[0])[0]
    #                                 if best[1] < 10:
    #                                     sequence["last_periodic"] = [index+1,best[1],last_periodic[3]+best[0],len(sequence["intervals"])]
    #                                     self.term_stdev[term].append([best[1],sequence["dates"][last_periodic[3]+best[0]:] + event.date,sequence["intervals"][last_periodic[3]+best[0]:]])
    #                     else: #calculate from beginning 
    #                         intervals = sequence["intervals"]
    #                         if len(intervals) >= 2: #find best periodicity
    #                             scores = []
    #                             for i in range(len(intervals[:-1])):
    #                                 seq = intervals[i:]
    #                                 scores.append([i,calculations.return_relative_stdev(seq)])
    #                             best = sorted(scores,key = lambda x : x[0])[0]
    #                             if best[1] < 10:
    #                                 sequence["last_periodic"] = [0,best[1],best[0],len(sequence["intervals"])]
    #                                 self.term_stdev[term].append([best[1],sequence["dates"][best[0]:],sequence["intervals"][best[0]:]])
                        # try:      
                        #     string = self.event_string[event.ids[0]]
                        # except KeyError:
                        #     self.event_string[event.ids[0]] = self.strings
                        #     self.string_events[self.strings].append(event)
                        #     self.strings += 1
                #else:
                    #sequence["events"].append(event)
                    #sequence["merged_dates"].append(event.date)


            if add:
                sequence["dates"].append(event.date)
                sequence["weekdays"].append(event.date.weekday())
                sequence["weeknrs"].append(event.date.isocalendar()[1])
                sequence["years"].append(event.date.year)
                sequence["months"].append(event.date.month)
                sequence["month_weekday"].append([event.date.month,event.date.weekday(),
                    int(time_functions.timerel(event.date,datetime.datetime(event.date.year,\
                        event.date.month,1),"day") / 7) + 1])
                sequence["events"].append(event)
                sequence["entities"].extend([x for x in event.entities if x != entity])
                sequence["entities"] = list(set(sequence["entities"]))



    #def cluster_entities(self):



    #def rank_periodicity(self,date_begin,date_end):
        #










                    # try:
                    #     string = self.event_string[event.ids[0]]
                    # except KeyError:
                    #     self.event_string[event.ids[0]] = self.strings
                    #     self.string_events[self.strings].append(event)
                    #    self.strings += 1
