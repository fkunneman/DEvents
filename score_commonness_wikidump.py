
import sys
import re
import colibricore
import xml.etree.ElementTree as etree

tmp = sys.argv[1]
wiki = sys.argv[2]

list_patterns = (["{{","}}","^:","^;","^\#","^:","^<","^afbeelding:",
    'bestand:','==','\*',"\|{2}","\|-","class=","categorie:",
    '^[\!\|]'])

#for each page
for event, elem in etree.iterparse(wiki, events=('start', 'end', 'start-ns', 'end-ns')):
    if event == 'end':
        if elem.tag == '{http://www.mediawiki.org/xml/export-0.8/}text':
            print '****************************************************'
            #print elem.text
            b = elem.text.lower().split("\n")
            for u in b:
                if re.match(r'^\s*$',u) or re.findall('|'.join(list_patterns),u):
                    continue
                else:
                    print u
            print '****************************************************'
            

