
import sys
import re
import codecs
import json
import colibricore

tmp = sys.argv[1]
infiles = sys.argv[2:]

for infile in infiles:
    with codecs.open(infile,"r","utf-8") as f:
        for l in f:
            js = json.loads(l)
            text = js["text"]
            text = text.replace(',',' ,')
            text = text.replace('.',' .')
            text = text.replace(':',' :') 
            textfile = tmp + "_page.txt"
            tf = codecs.open(textfile,'w','utf-8')
            tf.write(text)
            tf.close()
            options = colibricore.PatternModelOptions(maxlength=7)
            classfile = tmp + "page.colibri.cls"
            classencoder = colibricore.ClassEncoder()
            classencoder.build(textfile)
            classencoder.save(classfile)
            print len(classencoder)
            corpusfile = tmp + "page.colibri.dat"
            classencoder.encodefile(textfile, corpusfile)
            classdecoder = colibricore.ClassDecoder(classfile)
            decoded = classdecoder.decodefile(corpusfile)
            print decoded
           
            #corpusdata = colibricore.IndexedCorpus(corpusfile)
            #model = colibricore.UnindexedPatternModel()
            #model.train(corpusfile, options)
            #for pattern in model:
            #    print pattern.tostring(classdecoder)
            #for sentence in corpusdata.sentences():
            #    for trigram in sentence.ngrams(3):
            #        print trigram.tostring()
            #        print trigram.tostring(classdecoder)
    quit()


