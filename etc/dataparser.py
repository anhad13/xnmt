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
        or ": " in sentence
        or not re.search("^[A-Z]", sentence)
        or sentence[-1] not in (".", "!", "?")
    )   
sf=open("train_en.s", "w")
tf=open("train_de.s","w")

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
    tf.write(t+"\n")
sf.close()
tf.close()