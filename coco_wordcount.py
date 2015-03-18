#!/usr/bin/env 

import sys
import os

outdir = sys.argv[1]
for filename in sys.argv[2:]:
    fn = filename.split("/")[-1]
    print(fn)
    os.system("cp " + filename + " tweets")
    os.system("colibri-classencode tweets")
    os.system("colibri-patternmodeller -f tweets.colibri.dat -t 1 -l 5 -o tweets.colibri.indexedpatternmodel")
    os.system("colibri-patternmodeller -i tweets.colibri.indexedpatternmodel -c tweets.colibri.cls -P > " + outdir + fn)