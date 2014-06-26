
import sys
import re

import json
import colibricore

tmp = sys.argv[1]
infiles = sys.argv[2:]

for infile in infiles:
    f = open(infile,encoding = "utf-8")
    for l in f.readlines():
        js = json.loads(l)
        text = js["text"]
        text = text.replace(',',' ,')
        text = text.replace('.',' .')
        text = text.replace(':',' :') 
        textfile = tmp + "_page.txt"
        options = colibricore.PatternModelOptions(maxlength=7)
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
            for fivegram in sentence.ngrams(5):
                print(fivegram.tostring(classdecoder))
    f.close()
    quit()
