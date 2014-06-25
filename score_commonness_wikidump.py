
import sys
import colibricore
import xml.etree.ElementTree as etree

tmp = sys.argv[1]
wiki = sys.argv[2]

#for each page
for event, elem in etree.iterparse(wiki, events=('start', 'end', 'start-ns', 'end-ns')):
    if event == 'end':
        if elem.tag == '{http://www.mediawiki.org/xml/export-0.8/}text':
            print elem.text

