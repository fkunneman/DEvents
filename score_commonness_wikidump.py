
import sys
import re
import string
from collections import defaultdict

import json
import colibricore

tmp = sys.argv[1]
infiles = sys.argv[2:]

five = defaultdict(lambda : defaultdict(int))
four = defaultdict(lambda : defaultdict(int))
three = defaultdict(lambda : defaultdict(int))
two = defaultdict(lambda : defaultdict(int))
one = defaultdict(lambda : defaultdict(int))
ngramcounters = [one,two,three,four,five]
exclude = set(string.punctuation)
for infile in infiles:
    f = open(infile,encoding = "utf-8")
    for l in f.readlines():
        js = json.loads(l)
        text = js["text"].lower()
        text = ''.join(ch for ch in text if ch not in exclude)
        textfile = tmp + "_page.txt"
        with open(textfile,'w',encoding='utf-8') as g:      
            g.write(text)
        classfile = tmp + "page.colibri.cls"
        classencoder = colibricore.ClassEncoder()
        classencoder.build(textfile)
        classencoder.save(classfile)
        corpusfile = tmp + "page.colibri.dat"
        classencoder.encodefile(textfile, corpusfile)
        classdecoder = colibricore.ClassDecoder(classfile)
        corpusdata = colibricore.IndexedCorpus(corpusfile)
        for sentence in corpusdata.sentences():
            for i in range(1,6):
                for ngrams in sentence.ngrams(i):
                    for ngram in ngrams.tostring(classdecoder):
                        ngramcounters[i-1][ngram]["count"] += 1
        anchors = js["annotations"]
        surface = [x["surface_form"].lower() for x in anchors]
        for ngram in surface:
            num_grams = len(ngram.split(" "))
            if num_grams <= 5:
                ngramcounters[num_grams-1][ngram]["anchor"] += 1
    f.close()
    print(three)
    quit()
