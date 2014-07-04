
from __future__ import division
import math
import itertools
import numpy

def goodness_of_fit(total,dc,ec,ode):
    g2 = 0
    ede = (dc + ec) / total
    if ode > 0 and ede > 0:
        g2 += ode * (math.log(ode/ede)/math.log(2))
    odne = dc - ode
    edne = (dc + (total-ec)) / total
    if edne > 0 and odne > 0:
        g2 += odne * (math.log(odne/edne)/math.log(2))
    onde = ec - ode
    ende = (ec + (total-dc)) / total
    if onde > 0 and ende > 0:
        g2 += onde * (math.log(onde/ende)/math.log(2))
    ondne = total - (ode+odne+onde) 
    endne = ((total-dc) + (total-ec)) / total
    if ondne > 0 and endne > 0:
        g2 += ondne * (math.log(ondne/endne)/math.log(2))
    return g2

def extract_unique(l):
    ss = []
    for u in range(1,5):
        for subset in itertools.combinations(l, u):
#            print(u,l,subset)
            s1 = []
            s2 = []
            half = int(len(subset) / 2)
            for y in subset[:half]:
                #print(y)
                s1.extend(y.split(" "))
            for y in subset[half:]:
                s2.extend(y.split(" "))
            if not bool(set(s1) & set(s2)):
                s = tuple(sorted(subset))
                ss.append(s)
    return ss

def return_overlap(l1,l2):
    overlaps = []
    for x in l1:
        for y in l2:
            t1 = x.split()
            t2 = y.split()
            overlaps.append(len(set(t1) & set(t2)) / numpy.mean([len(t1),len(t2)]))
    return numpy.mean(overlaps)
