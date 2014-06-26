
import sys
import re
import string

import json
import colibricore

tmp = sys.argv[1]
infiles = sys.argv[2:]

options = colibricore.PatternModelOptions(mintokens=1,maxlength=7)
exclude = set(string.punctuation)
for infile in infiles:
    f = open(infile,encoding = "utf-8")
    for l in f.readlines():
        js = json.loads(l)
        text = js["text"].lower()
        #text = text.replace(',',' ,')
        #text = text.replace('.',' .')
        #text = text.replace(':',' :')
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
        model = colibricore.UnindexedPatternModel()
        model.train(corpusfile, options)
        for pattern in model:
            print(pattern.tostring(classdecoder))
        # corpusdata = colibricore.IndexedCorpus(corpusfile)
        # for sentence in corpusdata.sentences():
        #     for fivegram in sentence.ngrams(5):
        #         print(fivegram.tostring(classdecoder))
        anchors = js["annotations"]
        print([x["surface_form"].lower() for x in anchors])
    f.close()
    quit()
