
import re
import codecs
import sys
import random
from collections import defaultdict

outdir = sys.argv[1]
ngramf = sys.argv[2]
csf = sys.argv[3]
csxf = sys.argv[4]

twothird = 13*[14] + 4*[17]
onethird = 14*[16] + 2*[13]
filled = []
counts = defaultdict(int)
asets = []

def generate_indexlist(r,s):
    asets_f =[]
    for i in range(r):
        index = 0
        aset = []
        for j,e in enumerate(s):
            es = range(index,index+e)
            es_clean = []
            es_clean = [v for v in es if v not in (set(es) & set(filled))]
            if len(es_clean) == 0:
                rc = random.choice([v for v in range(250) if v not in (set(range(250)) & set(filled))])
            else:
                rc = random.choice(es_clean)
            aset.append(rc)
            counts[rc] += 1
            if counts[rc] == 2:
                filled.append(rc)
            index += e
        asets_f.append(aset)
    return asets_f

def parse_outputfile(filename):
    outputfile = codecs.open(filename,"r","iso-8859-2")
    #outputfile = codecs.open(filename,"r","utf-8")
    units = []
    unit = ""
    for line in outputfile.readlines():
        line = unicode(line)
#        print line
        line = line.replace("width: 500px","width: 750px")
#        try:
#            line = line.encode("iso-8859-2")
#        except:
#            print "encode error"
        unit += line
        if re.search("Slecht",line):
            units.append(unit)
            unit = ""
    return units[:250]

#generate index lists
asets = generate_indexlist(20,twothird)
asets += generate_indexlist(10,onethird)

#parse outputfiles
ngram = parse_outputfile(ngramf)
cs = parse_outputfile(csf)
csx = parse_outputfile(csxf)

#print ngram,cs,csx

#extract events per annotator
for i in range(30):
    outfile = codecs.open(outdir + "annotator_" + str(i) + ".txt","w","iso-8859-2")
    #outfile = open(outdir + "annotator_" + str(i) + ".txt","w")
    indexfile = codecs.open(outdir + "indexes_annotator_" + str(i) + ".txt","w","utf-8")
    outfile.write("[[AdvancedFormat]]\n\n[[Block:MC Block]]\n\n")
    #outfile.write(r"<div>Lama Events detecteert volledig automatisch gebeurtenissen in de grote " + \
    #    "stroom van Nederlandse tweets.&nbsp;Je gaat de output van dit systeem testen, en wordt " + \
    #    "daarbij wellicht verrast door interessante gebeurtenissen waar je geen weet van had. In " + \
    #    "totaal krijg je 50 gebeurtenissen ter beoordeling te zien.&nbsp;De duur is ongeveer 20 " + \
    #    "minuten. Je voortgang wordt bijgehouden, dus je kunt deze survey op ieder moment afsluiten " + \
    #    "en later weer de link aanklikken om verder te gaan. Lees om te beginnen de instructies " + \
    #    "hieronder goed door.&nbsp;&nbsp;</div><div>&nbsp;</div><div>Je krijgt steeds 5 tweets te zien " + \
    #    "en wordt gevraagd aan te geven&nbsp;of ze alle 5 naar dezelfde gebeurtenis verwijzen. Voor het " + \
    #    "identificeren van een gebeurtenis kun je de volgende definitie hanteren:</div><div>&nbsp;</div>" + \
    #    "<div><i>Een gebeurtenis vindt plaats op een specifiek tijdstip en is van belang voor een grotere " + \
    #    "groep mensen.&nbsp;</i></div><div>&nbsp;</div><div>Sportwedstrijden en wetsveranderingen zijn in " + \
    #    "deze definitie een gebeurtenis, terwijl een vakantie naar Turkije te persoonlijk is om een " + \
    #    "gebeurtenis te zijn. Let op dat ook hashtags een verwijzing naar een gebeurtenis kunnen zijn, zoals #tvoh voor 'The Voice of Holland', of #ajafey voor 'Ajax-Feyenoord'. <br /><br />Verder is het belangrijk dat de 5 tweets naar dezelfde gebeurtenis " + \
    #    "verwijzen. Soms worden er meerdere gebeurtenissen in een tweet beschreven, zoals een supportersactie " + \
    #    "tijdens een voetbalwedstrijd. Als alle 5 de tweets op deze manier zijdelings naar dezelfde " + \
    #    "voetbalwedstrijd verwijzen is dit toch goed. Echter, als ze alle vijf een verschillende gebeurtenis " + \
    #    "in Amsterdam beschrijven is het niet goed. Deze gebeurtenissen worden dan niet door een gezamenlijke " + \
    #    "gebeurtenis overkoepeld.&nbsp;<br /><br />Als je de eerste vraag bevestigend beantwoordt volgt nog " + \
    #    "een tweede vraag.&nbsp;In het geval van een positief antwoord verschijnt nog een tweede vraag. Je " + \
    #    "krijgt dan&nbsp;&eacute;&eacute;n of meerdere termen te zien die de gebeurtenis beschrijven, met de " + \
    #    "vraag of ze zich goed, matig of slecht tot de gebeurtenis verhouden. Gegeven wat je over de " + \
    #    "gebeurtenis weet op basis van de 5 tweets, in welke mate&nbsp;geven de termen dan relevante en " + \
    #    "afdoende informatie over wat voor gebeurtenis het is?<br /><br />Wees vooral kritisch en onbevooroordeeld in je beoordeling, het gaat erom dat we een indruk krijgen van de kwaliteit van het systeem. Veel succes!</div>\n[[PageBreak]]\n")
    j = i
#    print i,"index",j
    indexes = range(50)
    index_event = {}
    ngrami = asets[j]
#    print ngrami
#    print ngram
    for h in range(len(ngrami)):
#        print h
        index_event[h] = ("ngram",ngrami[h],ngram[ngrami[h]])
    j += 10
    if j >= 30:
        j = j - 30
#    print i,"index",j
    csi = asets[j]
    for k,h in enumerate(range(len(index_event.keys()),len(ngrami) + len(csi))):
        index_event[h] = ("cs",csi[k],cs[csi[k]])
    j += 10
    if j >= 30:
        j = j - 30
#    print i,"index",j
    csxi = asets[j]
    for k,h in enumerate(range(len(index_event.keys()),len(ngrami) + len(csi) + len(csxi))):
        index_event[h] = ("csx",csxi[k],csx[csxi[k]])
#    print len(index_event.keys()),len(ngrami),len(csi),len(csxi)
    random.shuffle(indexes)
    for index in indexes:
#        print index
        outfile.write(index_event[index][2] + unicode("\n[[PageBreak]]\n"))
        indexfile.write(str(index_event[index][0]) + " " + str(index_event[index][1]) + "\n")
    outfile.close()
    indexfile.close()

     
