
import sys
import re

import json
import colibricore

tmp = sys.argv[1]
infiles = sys.argv[2:]



for infile in infiles:
    with open(infile,"r","utf-8") as f:
        for l in f:
            js = json.loads(l)
            text = js["text"]
            text = text.replace(',',' ,')
            text = text.replace('.',' .')
            text = text.replace(':',' :') 
            textfile = tmp + "_page.txt"
            with open(textfile,'w','utf-8') as g:
                tf.write(text)
            classfile = tmp + "page.colibri.cls"
            classencoder = colibricore.ClassEncoder()
            classencoder.build(atfile)
            classencoder.save(classfile)
            corpusfile = tmp + "page.colibri.dat"
            classencoder.encodefile(textfile, corpusfile)
            classdecoder = colibricore.ClassDecoder(classfile)
            corpusdata = colibricore.IndexedCorpus(corpusfile)
            for sentence in corpusdata.sentences():
                for fivegram in sentence.ngrams(5):
                    print(fivegram.tostring(classdecoder))
    quit()
