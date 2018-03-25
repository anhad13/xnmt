import unicodecsv
import sys 
import argparse
import re
source_file_name="/Users/anhadmohananey/Downloads/en-de/train.tags.en-de.en"
target_file_name="/Users/anhadmohananey/Downloads/en-de/train.tags.en-de.de"
source = open(source_file_name).readlines()
target = open(target_file_name).readlines()

def clean(sentence):
    return sentence.replace("  ", " ").strip()

def fails(sentence):
    return (
        sentence.count('"') % 2 
        or " " not in sentence
        or len(re.split(r'[.!?]+?[ ]+', sentence))>1
        or ": " in sentence
        or re.search(r'[\%]+', sentence)
        or not re.search("^[A-Z]", sentence)
        or sentence[-1] not in (".", "!", "?")
    )   
sf=open("train_en.s", "w")
tf=open("train_de.s","w")
vs=[]
vt=[]
for index in range(len(source)):
    s = clean(source[index])
    t = clean(target[index])
    if (
        fails(s)
        or fails(t)
        or s == t
    ):  
        continue
    sf.write(s+"\n")
    vs+=s.replace("."," .").replace("?", " ?").replace("!", " !").replace(","," ,").split()
    tt=t.replace("."," .").replace("?", " ?").replace("!", " !").replace(","," ,")
    vt+=tt.split()
    tf.write(tt+"\n")
vs=list(set(vs))
vt=list(set(vt))
fvs=open("vocab.s", "w")
fvt=open("vocab.t", "w")
fvs.write("\n".join(vs))
fvt.write("\n".join(vt))
fvs.close()
fvt.close()
sf.close()
tf.close()