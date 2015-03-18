#!/usr/bin/env 

import sys
import os

outdir = sys.argv[1]
max_l = sys.argv[2]
min_t = sys.argv[3]
for filename in sys.argv[4:]:
    fn = filename.split("/")[-1]
    print(fn)
    os.system("cp " + filename + " tweets")
    os.system("colibri-classencode tweets")
    os.system("colibri-patternmodeller -f tweets.colibri.dat -t " + min_t + " -l " + max_l + " -o tweets.colibri.indexedpatternmodel")
    os.system("colibri-patternmodeller -i tweets.colibri.indexedpatternmodel -c tweets.colibri.cls -P > " + outdir + fn)
    os.system("rm tw*")
