#!/usr/bin/env python

from __future__ import unicode_literals
import sys
import codecs
import json
import re

infile = open(sys.argv[1])
outfile = codecs.open(sys.argv[2],"w","utf-8")


qidm = re.compile(r"QID(\d+)")

try:
    decoded = json.loads(infile.read()).replace("\u00e2\u0080\"","-").replace("\u00f0\u009f'\u0096","").replace("& amp ;","&").replace("caf\u00e9","").replace("& gt ;",">").replace("\u00c3\u00ab \u00e2\u0080\"","e").replace("\u00c3\u00ab",u"e").replace("\u00e2\u0080\u009c","").replace("& amp ; #39 ;","\'"))
 
    # pretty printing of json-formatted string
    print decoded.keys()
    for i,entry in enumerate(decoded["SurveyElements"]):
        if not isinstance(entry["Payload"],list):
            if entry["PrimaryAttribute"] not in ["Survey Flow","Survey Options","Scoring","Survey Statistics","Survey Question Count"] and not entry["Payload"] == None:
                if entry["Payload"]["QuestionType"] == "MC": 
                    try:
                        entry["Payload"]["Validation"] = {}
                        entry["Payload"]["Validation"]["Settings"] = {}
                        entry["Payload"]["Validation"]["Settings"]["ForceResponse"] = "ON"
                    except:
                        print "FR"
                    print entry["Payload"]["Validation"]
                    if len(entry["Payload"]["Choices"].keys()) == 3:
                        QID = "QID" + str(int(qidm.search(entry["Payload"]["QuestionID"]).groups()[0]) - 1)
                        print entry["Payload"].keys()
                        entry["Payload"]["InPageDisplayLogic"] = {}
                        entry["Payload"]["InPageDisplayLogic"]["0"] = {}
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"] = {}
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["QuestionID"] = QID
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["QuestionIsInLoop"] = "no"
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["ChoiceLocator"] = "q://" + QID + "/SelectableChoice/1"
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["Operator"] = "Selected"
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["QuestionIDFromLocator"] = QID
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["LeftOperand"] = "q://" + QID + "/SelectableChoice/1"
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["Type"] = "Expression"
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["LogicType"] = "Question"
                        entry["Payload"]["InPageDisplayLogic"]["0"]["0"]["Description"] = "<span class=\"ConjDesc\">If</span> <span class=\"QuestionDesc\">Verwijzen deze 5 tweets naar dezelfde gebeurtenis?\n zuidtangent deels afgesloten op 16 augustus :...</span> <span class=\"LeftOpDesc\">Ja</span> Is <span class=\"OpDesc\">Selected</span> "
                        entry["Payload"]["InPageDisplayLogic"]["0"]["Type"] = "If"
                        entry["Payload"]["InPageDisplayLogic"]["Type"] = "BooleanExpression"
                        entry["Payload"]["InPageDisplayLogic"]["inPage"] = True
                        entry["Payload"]["Choices"] = {1:{"Display":"Goed"},2:{"Display":"Matig"},3:{"Display":"Slecht"}}
                        print entry["Payload"].keys()
    json.dump(decoded, outfile, ensure_ascii=False)
 
except (ValueError, KeyError, TypeError): 
    print "JSON format error",entry

