import json
import os
from nltk import tag

st = ['she is a dog.', 'she go to school.']
k = [tag.pos_tag(sent.split()) for sent in st]
k1 =[]
for sent in k:
    newsent= [word[1] for word in sent]
    k1.append(newsent)
        
print k1
'''
if 1==1:
    os.system('java -cp "/home/VMadmin/stanford-corenlp-full-2015-12-09/*" \-Xmx2g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,parse -file input -outputFormat json')
    with open('input.json') as data_file:
        fo = json.load(data_file)
    dependency = []
    t = []
    for k in fo['sentences']:
        for k1 in k["basic-dependencies"]:
            print k1
            t1 = [k1['dep'],k1['dependent'],k1['governor']]
            t.append(t1)
        dependency.append(t)
print dependency
'''
