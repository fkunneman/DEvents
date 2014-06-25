
import sys
import re
import colibricore
import xml.etree.ElementTree as etree

tmp = sys.argv[1]
wiki = sys.argv[2]

#for each page
for event, elem in etree.iterparse(wiki, events=('start', 'end', 'start-ns', 'end-ns')):
    if event == 'end':
        if elem.tag == '{http://www.mediawiki.org/xml/export-0.8/}text':
            print '****************************************************'
            #print elem.text
            b = elem.text.lower().split("\n")
            for u in b:
                if re.match(r'^\s*$',u) or re.search("}}",u) or re.search("^:",u) or re.search("^;",u) or re.search("^\#",u) or re.search("math>",u) or re.search("{{",u) or re.search('bestand:',u) or re.search('==',u) or re.search('\*',u) or re.search(r"\|{2}",u) or re.search("\|-",u) or re.search("class=",u) or re.search("categorie:",u) or re.search('^[\!\|]',u):
                    continue
                else:
                    print u
            print '****************************************************'
            

