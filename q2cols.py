
import argparse
from collections import defaultdict

"""
Script to extract annotations from the NLE_experiment and link them to the proper event
"""
parser = argparse.ArgumentParser(description = "Script to extract annotations from the NLE_experiment and link them to the proper event")
parser.add_argument('-a', nargs = '+', action = 'store', required = True, help = "the annotation files") 
parser.add_argument('-i', nargs = '+', action = 'store', required = True, help = "the annotation index files") 
parser.add_argument('-d', action = 'store', required = True, help = "the output dir")
# parser.add_argument('--cs', action = 'store', required = True, help = "the output file for the 250 cs events")  
# parser.add_argument('--csx', action = 'store', required = True, help = "the output file for the 250 csx events")
#parser.add_argument('--ngram', action = 'store', required = True, help = "the output file for the 250 ngram events")    
args = parser.parse_args() 

#check if annotation and index can be linked
if len(args.i) != len(args.a):
    print "indexfiles and annotationfiles do not align; exiting program"
    exit()

#initiate event rankings
event_ranking = {}
event_ranking["ngram"] = defaultdict(lambda : defaultdict(list))
event_ranking["cs"] = defaultdict(lambda : defaultdict(list))
event_ranking["csx"] = defaultdict(lambda : defaultdict(list))

#print event_ranking
#for each annotationfile
for afile in args.a:
    aid = afile[15:17]
    ifile = [x for x in args.i if x[28:30] == aid][0]
    print (aid,ifile[28:30])
    #make index-event-ranking list
    index_event = []
    ifileo = open(ifile)
    for i,line in enumerate(ifileo.readlines()):
        index_event.append(line.strip().split(" "))
    ifileo.close()
    #walk through annotations
    afileo = open(afile)
    annotations = [x for x in afileo.readlines()[2].split(",")[10:] if x in ["","0","1","2","3"]][2:-1]
    print len(annotations)
    for i,j in enumerate(range(0,100,2)):
        event = index_event[i]
        a1 = annotations[j]
        a2 = annotations[j+1]
        #print "a1",a1,"a2",a2
        system = event[0]
        index = int(event[1])
        #print system,index

        event_ranking[system][index]["1"].append(a1)
        event_ranking[system][index]["2"].append(a2)
    afileo.close()

for system in ["ngram","cs","csx"]:
    systemout1 = open(args.d + system + "_ranked.txt","w")
    systemout2 = open(args.d + system + "_terms.txt","w")
    for key in sorted(event_ranking[system].keys()):
        q1 = event_ranking[system][key]["1"]
        q2 = event_ranking[system][key]["2"]
        #print "before",q1
        if len(q1) == 1:
            q1.append("")
            q2.append("")
        #print "after",q1
        #print q1,q2,"\t".join(q1) + "\t" + "\t".join(q2) + "\n"
        systemout1.write("\t".join(q1) + "\n")
        systemout2.write("\t".join(q2) + "\n")


# infile = codecs.open(args.i,"r","utf-8")
# outfile = codecs.open(args.o,"a","utf-8")

# qfile = open(sys.argv[1])

