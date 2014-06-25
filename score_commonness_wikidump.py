
import sys
import re
import codecs
import colibricore
import xml.etree.ElementTree as etree

tmp = sys.argv[1]
wiki = sys.argv[2]

list_patterns = (["{{","}}","^:","^;","^\#","^:","^<","^afbeelding:",
    'bestand:','==','\*',"\|{2}","\|-","class=","categorie:",
    '^[\!\|]'])

#for each page
for event, elem in etree.iterparse(wiki, events=('start', 'end', 
    'start-ns', 'end-ns')):
    if event == 'end':
        if elem.tag == '{http://www.mediawiki.org/xml/export-0.8/}text':
            all_text = ""
            b = elem.text.lower().split("\n")
            for u in b:
                if re.match(r'^\s*$',u) or re.findall('|'.join(list_patterns),u):
                    continue
                else:
                    all_text = all_text + u
                all_text = all_text.replace(',',' ,')
                all_text = all_text.replace('.',' .')
                all_text = all_text.replace(':',' :')
            atfile = tmp + "page.txt"
            f = codecs.open(atfile,'w','utf-8')
            f.write(all_text)
            f.close()
            classfile = tmp + "page.colibri.cls"
            classencoder = colibricore.ClassEncoder()
            classencoder.build(atfile)
            classencoder.save(classfile)
            corpusfile = tmp + "page.colibri.dat"
            classencoder.encodefile(atfile, corpusfile)
            corpusdata = colibricore.IndexedCorpus(corpusfile)
            for sentence in corpusdata.sentences():
                for fivegram in sentence.ngrams(5):
                    print(fivegram.tostring(classdecoder))
            print "***********************************************"


