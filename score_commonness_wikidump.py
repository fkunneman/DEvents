
import sys
import re
import string
from collections import defaultdict

import json
import colibricore

tmp = sys.argv[1]
outdir = sys.argv[2]
infiles = sys.argv[3:]

five = defaultdict(lambda : defaultdict(int))
four = defaultdict(lambda : defaultdict(int))
three = defaultdict(lambda : defaultdict(int))
two = defaultdict(lambda : defaultdict(int))
one = defaultdict(lambda : defaultdict(int))
ngramcounters = [one,two,three,four,five]
exclude = set(string.punctuation)
for infile in infiles:
    print(infile)
    f = open(infile,encoding = "utf-8")
    for j,l in enumerate(f.readlines()):
        print(j)
        js = json.loads(l)
        text = js["text"].lower()
        #text = ''.join(ch for ch in text if ch not in exclude)
#        print(text)
        textfile = tmp + "_page.txt"
        with open(textfile,'w',encoding='utf-8') as g:      
            g.write(text)
        print("classfile")
        classfile = tmp + "page.colibri.cls"
        classencoder = colibricore.ClassEncoder()
        classencoder.build(textfile)
        classencoder.save(classfile)
        print("corpusencoder")
        corpusfile = tmp + "page.colibri.dat"
        classencoder.encodefile(textfile, corpusfile)
        print("classdecoder")
        classdecoder = colibricore.ClassDecoder(classfile)
        print("corpusdata")
        corpusdata = colibricore.IndexedCorpus(corpusfile)
        try:
            for sentence in corpusdata.sentences():
                print(sentence.tostring(classdecoder))
                for i in range(1,6):
                    for ngrams in sentence.ngrams(i):
                        ng = ngrams.tostring(classdecoder)
                        print(ng)
                        #ng = ngram.tostring(classdecoder)
                        ngramcounters[i-1][ng]["count"] += 1
        except KeyError:
            print("ckey error")
        anchors = js["annotations"]
        surface = [x["surface_form"].lower() for x in anchors]
        for ngram in surface:
            num_grams = len(ngram.split(" "))
            if num_grams <= 5:
                ngramcounters[num_grams-1][ngram]["anchor"] += 1
                ngramcounters[num_grams-1][ngram]["count"] += 1
    f.close()

for i,c in enumerate(ngramcounters):
    out = sorted([[x,c[x]["anchor"],c[x]["count"]] for x in c.keys()],
        key = lambda y: y[1],reverse=True)
    outfile = open(outdir + str(i+1) + "_grams.txt","w",encoding="utf-8")
    for line in out:
        outfile.write(" ".join(line) + "\n")
    outfile.close()

