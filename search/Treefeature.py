#-*- coding: UTF-8 -*-
# d1,d2,d3: distance of edge between key node and parent, child, and siblings.
import nltk
#from stanford_corenlp_pywrapper import CoreNLP
#from nltk.parse import stanford
import math, re
from Node import Node
from nltk import Tree, ParentedTree
import xml.etree.ElementTree as ET
import requests
#from nltk.parse.stanford import StanfordParser
import os, copy
from math import sqrt
import numpy as np

#parser = StanfordParser(model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")


url = "http://localhost:8081/v2/check"
payload = {'language':'en', 'text':''}
#st = CoreNLP("parse", corenlp_jars=["H:/Server/stanford-corenlp-full-2015-12-09/*"])
POSlists = ['$','``', '\'\'', '(', ')', ',', '--', '.', ':', 'CC', 'CD',\
                    'DT', 'EX', 'FW', 'IN', 'JJ', 'JJR', 'JJS', 'LS', 'MD', 'NN', \
                    'NNP', 'NNPS', 'NNS', 'PDT', 'POS','PRP', 'PRP$', 'RB', \
                    'RBR', 'RBS', 'RP', 'SYM', 'TO', 'UH', 'VB', 'VBD', \
                    'VBG', 'VBN', 'VBP', 'VBZ', 'WDT', 'WP', 'WP$', 'WRB']

jj = ['JJ', 'JJR', 'JJS']
nn = ['NN', 'NNP', 'NNPS', 'NNs']
prp = ['PRP', 'PRP\$']
rb = ['RB', 'RBR', 'RBS']
vb = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']

def concepttags(name):
    datatxt = open(name, 'r').readlines()
    datafeature = []
    N=len(datatxt)
    for i in range(0,N):
        w=datatxt[i].split(";")
        lw = len(w)
        datafeature.append(w[:lw-1])
    return datafeature

def taglist(answer):
    tag = []
    confeature = concepttags('conceptindex.txt')
    ct = 0
    for i in answer:
        for cell in confeature:
            if i in cell:
                tag.append(cell[0])
                ct = 1
    return tag, ct
def concept(answers):
    #concepts = []
    answers = answers.split(";")
    answers = [cell.lower() for cell in answers]
    tag, ct = taglist(answers)
    return tag

class myTree(ParentedTree):
    def myleaves(self):
        leaves = []
        for child in self:
            if isinstance(child, Tree):
                if isinstance(child[0], Tree):
                    leaves.extend(child.myleaves())
                else:
                    leaves.append(child)
        return leaves
class myNode:
    cnt = 0
    def __init__(self):
        self.id = myNode.cnt
        self.children = []
        self.father = None
        self.data = ''
        myNode.cnt += 1
    def __str__(self):
        return '('+str(self.id)+','+str(self.data)+')'

def judgecontent(content):
    pay1 = dict(payload)
    pay1['text']=content
    #pay1['enabledOnly']='yes'
    pay1['disabledCategories']='MYRULE'
    t = requests.post(url, data = pay1)
    root = ET.fromstring(t.text.encode('utf8'))
    error = 0
    for child in root[1:]:
        if not (child.attrib['ruleId'].startswith('COMMA') or child.attrib['ruleId'].startswith('WHITE') or child.attrib['ruleId'].startswith('UPPER') or child.attrib['ruleId'].startswith('EN_QUOTES')):
            if child.attrib['categoryid']!='PUNCTUATION':
                error = 1

    return error
def judgeparse(parse,k):
    if k==1:
        pay2 = dict(payload)
        pay2['text']=parse.replace('\n','').replace('(',' ').replace(')',' ').replace('    ',' ').replace('   ',' ').replace('  ',' ')
        print pay2['text']
        pay2['enabledOnly']='yes'
        pay2['enabledCategories']='MYRULE1'
        t = requests.post(url, data = pay2)
        root = ET.fromstring(t.text.encode('utf8'))

        for child in root[1:]:
            print child.attrib
        error = 0
        if len(root)>1:
            error = 1
    if k==2:
        pay2 = dict(payload)
        pay2['text']=parse.replace('\n','').replace('(',' ').replace(')',' ').replace('    ',' ').replace('   ',' ').replace('  ',' ')
        pay2['enabledOnly']='yes'
        pay2['enabledCategories']='MYRULE2'
        t = requests.post(url, data = pay2)
        root = ET.fromstring(t.text.encode('utf8'))
        for child in root[1:]:
            print child.attrib
        error = 0
        if len(root)>1:
            error = 1
    return error
def judge(content, parse):
    pay1 = dict(payload)
    pay2 = dict(payload)

    pay1['text']=content
    pay1['disabledCategories']='MYRULE'
    t = requests.post(url, data = pay1)
    root = ET.fromstring(t.text.encode('utf8'))
    error = 0
    for child in root[1:]:
        if not (child.attrib['ruleId'].startswith('COMMA') or child.attrib['ruleId'].startswith('WHITE') or child.attrib['ruleId'].startswith('UPPER') or child.attrib['ruleId'].startswith('EN_QUOTES')):
            if child.attrib['categoryid']!='PUNCTUATION':
                error = 1
    pay2['text']=parse.replace('\n','').replace('(',' ').replace(')',' ').replace('    ',' ').replace('   ',' ').replace('  ',' ')
    pay2['enabledOnly']='yes'
    pay2['enabledCategories']='MYRULE'
    t = requests.post(url, data = pay2)
    root = ET.fromstring(t.text.encode('utf8'))
    if len(root)>1:
        error = 1
    return error
def questionConstruct(content, answer):
    keywordPosition = []
    posKeyword = []
    content = nltk.sent_tokenize(content)
    splitContent = [nltk.word_tokenize(sent) for sent in content]
    eachanswer = answer.split(';')
    index_ans=0
    recontent=[]
    sentenceIndex = []
    for sc in range(len(splitContent)):
        eachsentence = []
        knum = 0
        eachposition = []
        for index in range(len(splitContent[sc])):
            if '*' in splitContent[sc][index]:
                if index_ans<len(eachanswer):
                    splitAnswer = eachanswer[index_ans].split(' ')
                    splitAnswer = [c.strip() for c in splitAnswer]
                    kwLen = len(splitAnswer)
                    index_ans = index_ans+1
                    for sa in splitAnswer:
                        eachsentence.append(sa)
                    for kl in range(0,kwLen):
                        eachposition.append(index+kl+knum)
                knum = kwLen-1
            else:
                eachsentence.append(splitContent[sc][index])
        keywordPosition.append(eachposition[:1])

        recontent = recontent + eachsentence
    stcontent = ' '.join(recontent)
    content = ' '.join(content)
    return stcontent, keywordPosition, content
def buildeditTree(t, node, leaves):
    if isinstance(t, tuple):
        node.label = t[0]
        for i in range(1, len(t)):
            n = Node('')
            node.addkid(n)
            n.father = node
            n.level = node.level + 1
            leaves = buildeditTree(t[i], n, leaves)
    else:
        node.label = t
        leaves.append(node)
    return leaves

def parsesentence_ABCD(sentences, answersABCD):
    newsent = []
    KP = []
    for answers in answersABCD:
        for sent, ans in zip(sentences, answers):
            sentence, keywordposition = questionConstruct(sent, ans)
            newsent.append(sentence.replace("’","'"))
            KP.append(keywordposition)
    fo = open('newsent', 'w')
    for sent in newsent:
        if sent[len(sent)-1]!=('.' or '?' or '!'):
            sent = sent + '.'
        fo.write(sent+'\n')
    fo.close()
    os.system("java -mx5g edu.stanford.nlp.parser.lexparser.LexicalizedParser -nthreads 4 edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz newsent > file.stp")
    fo = open('file.stp','r').readlines()
    fos = ' '.join(fo)
    fos = fos.split(' \n ')
    parsers = []
    for sent in fos:
        sent1 = sent.replace('\n','')
        parsers.append(sent1)
    #parsers = parser.raw_parse_sents(newsent)

    MQpar = []
    MQcont = []
    for i in range(0, len(newsent), 4):
        parse = parsers[i:i+4]
        cont = newsent[i:i+4]
        MQpar.append(parse)
        MQcont.append(cont)
    return MQcont, MQpar
def parsesentencs(sentences, answers):
    print sentences
    newsent = []
    KP = []
    sentlab = 0
    labs = [0]
    quescont = []
    for sent, ans in zip(sentences, answers):
        resentence, keywordposition, sentence = questionConstruct(sent, ans)
        quescont.append(sentence)
        sentence = nltk.sent_tokenize(sentence)
        sentlen = len(sentence)
        sentlab = sentlab + sentlen
        labs.append(sentlab)
        for s in sentence:
            newsent.append(s.replace("’","'"))
        KP.append(keywordposition)
    #parsers = parser.raw_parse_sents(newsent)
    print newsent
    fo = open('newsent', 'w')
    for sent in newsent:
        if sent[len(sent)-1]!=('.' or '?' or '!'):
            sent = sent + '.'
        fo.write(sent+'\n')
    fo.close()
    os.system('java -mx5g edu.stanford.nlp.parser.lexparser.LexicalizedParser -nthreads 4 edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz newsent > file.stp') ## -cp "C:/stanford-corenlp-full-2015-12-09/*" \
    fo = open('file.stp','r').readlines()
    fos = ' '.join(fo)
    fos = fos.split(' \n ')
    parsers = []
    for sent in fos:
        sent1 = sent.replace('\n','')
        parsers.append(sent1)
    newparsers = []
    for i in range(len(labs)-1):
        cell = parsers[labs[i]:labs[i+1]]
        newparsers.append(cell)
    '''
    APOS = []
    for p in parsers:
        POS = []
        for ele in p.pos():
            POS.append(ele[1])
        APOS.append(POS)
   '''
    return parsers, KP, quescont, newparsers
def buildsubTree3(t, loc, bfnum, afnum):
    editleaves = []
    newtree = Node(t[0])
    editleaves = buildeditTree(t, newtree, editleaves)
    keywords = []
    for i in loc:
        keywords.append(editleaves[i])
    before2id = []
    beforeid = []
    afterid = []
    after2id = []
    after3id = []
    keyid = []
    for nd in keywords:
        keyid.append(nd.id)
        while nd.father != None:
            nd = nd.father
            keyid.append(nd.id)
    beforeids = []
    afterids = []
    for i in range(1,11):
        beforeid =[]
        if loc[0] > i-1:
            nb = editleaves[loc[0]-i]
            while nb.id not in keyid:
                beforeid.append(nb.id)
                nb = nb.father
        beforeids.append(beforeid)
        afterid = []
        if loc[len(loc)-1] < len(editleaves)-i:
            na = editleaves[loc[len(loc)-1]+i]
            while na.id not in keyid:
                afterid.append(na.id)
                na = na.father
        afterids.append(afterid)
    '''
    if loc[0] > 1:
        nb2 = editleaves[loc[0]-2]
        while nb2.id not in keyid:
            before2id.append(nb2.id)
            nb2 = nb2.father
    if loc[len(loc)-1] != len(editleaves)-1:
        na = editleaves[loc[len(loc)-1]+1]
        while na.id not in keyid:
            afterid.append(na.id)
            na = na.father
    if loc[len(loc)-1] < len(editleaves)-2:
        na2 = editleaves[loc[len(loc)-1]+2]
        while na2.id not in keyid:
            after2id.append(na2.id)
            na2 = na2.father
    if loc[len(loc)-1] < len(editleaves)-3:
        na3 = editleaves[loc[len(loc)-1]+3]
        while na3.id not in (keyid or beforeid or afterid or after2id):
            after3id.append(na3.id)
            na3 = na3.father
    '''
    for i in range(len(editleaves)):
        if editleaves[i].father != None:

            if 1==1:

            #if editleaves[i].label.isalpha() or editleaves[i].label == '*':
                if i == loc[0]:
                    n = Node('key')
                    n.father = editleaves[i].father
                    n.level = editleaves[i].level
                    editleaves[i].father.addkid(n)
                    keyid.append(n.id)

                for j in range(1,11):
                    if i == loc[0]-j:
                        n = Node('B'+str(j))
                        n.father = editleaves[i].father
                        n.level = editleaves[i].level
                        editleaves[i].father.addkid(n)
                        beforeids[j-1].append(n.id)
                    if i == loc[0]+j:
                        n = Node('A'+str(j))
                        n.father = editleaves[i].father
                        n.level = editleaves[i].level
                        editleaves[i].father.addkid(n)
                        afterids[j-1].append(n.id)


            '''
                if i == loc[0]-2:
                    tags, ct = taglist(editleaves[i].label)
                    if ct == 1:
                        for tag in tags:
                            n = Node(tag)
                            n.father = editleaves[i].father
                            n.level = editleaves[i].level
                            editleaves[i].father.addkid(n)
                    editleaves[i].label= 'B2'
                if i == loc[0]-1:

                    tags, ct = taglist(editleaves[i].label)

                    if ct == 1:
                        for tag in tags:
                            n = Node(tag)
                            editleaves[i].addkid(n)
                            n.father = editleaves[i]
                            n.level = editleaves[i].level+1
                            #keyid.append(n.id)

                    n = Node('B1')
                    n.father = editleaves[i].father
                    n.level = editleaves[i].level
                    editleaves[i].father.addkid(n)
                    beforeid.append(n.id)
                    #editleaves[i].label= 'B1'
                '''
            '''
                elif i == loc[len(loc)-1]+1:
                    tags, ct = taglist(editleaves[i].label)
                    if ct == 1:
                        for tag in tags:
                            n = Node(tag)
                            editleaves[i].father.addkid(n)
                            n.father = editleaves[i].father
                            n.level = editleaves[i].level
                            #keyid.append(n.id)

                    n = Node('A1')
                    n.father = editleaves[i].father
                    n.level = editleaves[i].level
                    editleaves[i].father.addkid(n)
                    afterid.append(n.id)
                    #editleaves[i].label= 'A1'
                elif i == loc[len(loc)-1]+2:

                    tags, ct = taglist(editleaves[i].label)
                    if ct == 1:
                        for tag in tags:
                            n = Node(tag)
                            editleaves[i].father.addkid(n)
                            n.father = editleaves[i].father
                            n.level = editleaves[i].level
                            #keyid.append(n.id)

                    n = Node('A2')
                    editleaves[i].father.addkid(n)
                    n.father = editleaves[i].father
                    n.level = editleaves[i].level
                    after2id.append(n.id)
                    #editleaves[i].label= 'A2'
                elif i == loc[len(loc)-1]+3:
                    tags, ct = taglist(editleaves[i].label)
                    if ct == 1:
                        for tag in tags:
                            n = Node(tag)
                            editleaves[i].addkid(n)
                            n.father = editleaves[i]
                            n.level = editleaves[i].level+1
                    editleaves[i].label= 'A3'

                else:
                    editleaves[i].father.children = list()
                '''

    myq = [newtree]

    #focusid = keyid+ beforeid + afterid+after2id
    focusid = keyid
    for i in range(0,bfnum):
        focusid = focusid + beforeids[i]
    for i in range(0,afnum):
        focusid = focusid + afterids[i]
    #for child in editleaves[i].father.children:
        #focusid.append(child.id)
    while len(myq) != 0:
        for c in myq[0].children:
            myq.append(c)
        if myq[0].id not in focusid:
            for i in range(len(myq[0].father.children)):
                if myq[0].father.children[i].id == myq[0].id:
                    myq[0].father.children.pop(i)
                    break
        del myq[0]


    #printEditEdges(newtree)
    return newtree

def nodeSimilar(T1,T2):

    if T1.label != T2.label or len(T1.children) != len(T2.children):
        sim = 0
    else:
        leaf = 0
        for child in T1.children:
            if len(child.children) > 0:
                leaf = 1
                break
        if len(T1.children)==0 and len(T2.children)==0:
            sim = 1
        elif leaf == 0:
            if T1.children != T2.children:
                #sim =0

                if T2.children[0].label.isalpha():
                    T2.children[0].theta = 0
                else:
                    T2.children[0].theta = 1
                if T1.children[0].label.isalpha():
                    T1.children[0].theta = 0
                else:
                    T1.children[0].theta = 1
                T1.children[1].theta = 1
                T2.children[1].theta = 1

                sim = 0
                for child1, child2 in zip(T1.children, T2.children):
                    if child1.label == child2.label:
                        sim = child1.theta*child2.theta

                '''
                if T2.children[0].label.isalpha():
                    T2.theta = 0
                else:
                    T2.theta = 1
                if T1.children[0].label.isalpha():
                    T1.theta = 0
                else:
                    T1.theta = 1

                if T1.children[1].label == T2.children[1].label :
                    sim = 1
                elif T1.children[0].label == T2.children[0].label:
                    sim = T1.theta * T2.theta
                else:
                    sim = 0
                '''
            else:
                sim = 1

        else:
            if T1.label != T2.label or T1.children != T2.children:
                sim = 0
            else:
                sim = T1.theta*T2.theta
                for child1, child2 in zip(T1.children, T2.children):
                    sim = sim*(1 + nodeSimilar(child1, child2))
    return sim
def treeSimilar(T1, T2):
    myq1 = [T1]
    myq2 = [T2]
    nodes1 = []
    nodes2 = []
    sim = nodeSimilar(T1, T2)
    while myq1:
        for c in myq1[0].children:
            if len(c.children)>0:
                nodes1.append(c)
                myq1.append(c)
        del myq1[0]
    while myq2:
        for c in myq2[0].children:
            if len(c.children)>0:
                nodes2.append(c)
                myq2.append(c)
        del myq2[0]
    l1 = len(nodes1)
    l2 = len(nodes2)

    for node1 in nodes1:
        for node2 in nodes2:
            sim = sim + nodeSimilar(node1, node2)

    return sim, l1, l2
def printEditEdges(root):
    myq = [root]
    while myq:
        for c in myq[0].children:
            print myq[0].id, myq[0].label, c.id, c.label, c.level, c.theta
            myq.append(c)
        del myq[0]
def settheta(root, level):
    myq = [root]
    while myq:
        for c in myq[0].children:
            if c.level== level:
                c.theta = 1
            myq.append(c)
        del myq[0]
def kfsTags(t, loc, bfnum, afnum):
    leaves = []
    subPOS = []
    root = Node(t[0])
    leaves = buildeditTree(t, root, leaves)
    keywords = []
    keytags = []
    fathertags = []
    for lc in loc:
        keywords.append(leaves[lc])
        keytags.append(leaves[lc].father.label)
        ff = leaves[lc].father.father
        fathertags.append(ff.label)
    for i in range(len(leaves)):
        if leaves[i].id == leaves[loc[0]].id:
            start = i
        if leaves[i].id == leaves[loc[len(loc)-1]].id:
            end = i
    words = leaves[start-1:end+3]
    for word in words:
        subPOS.append(word.father.label)
    subtree3 = buildsubTree3(t, loc, bfnum, afnum)
    subleave = subtree3.myleaves()
    for leave in subleave:
        if leave.label == '*':
            level = leave.level
            nd = leave.father
            while nd.father != None:
                nd.theta = 1
                nd = nd.father
            nd = leave.father
            while len(nd.children)<2:
                nd = nd.father
            for c in nd.children:
                if c.id != leaves[lc].father.id:
                    nd.theta = 1
    #settheta(subtree3,level)
    return keytags,fathertags,subPOS, subtree3, words

def QFeature (parse, KP, bfnum, afnum):
    F = dict({})
    F2 = [] #father tag
    F6 = []
    for t,kt in zip(parse, KP):
        if len(kt)>0:
            k1 = t
            #k1 = t.pprint()
            k2 = ','.join(k1.split())
            k2 = k2.replace(',,,', '",",","').replace('(,,','(",",')
            k3 = re.sub(r"([A-Z\.a-z\'a-zA-Z\'a-zA-Z$A-Z-A-Z\*\:\;\?\!\%\`\`0-9-0-9]+)",r'"\1"',k2)
            k4 = eval(k3)
            t = k4
            keytag,fathertag, keyPOS, subtree3, words= kfsTags(t, kt, bfnum, afnum)
            F2=F2+fathertag
            for s in keyPOS:
                F6.append(s)
            lenkt = len(kt)
    F['fathertag'] = F2
    F['subPOS'] = F6
    #F['lenkey'] = lenkt
    subTree = []
    subTree.append(subtree3)
    return F,subTree
def dot_product(v1, v2):
    return sum(map(lambda x: x[0] * x[1], zip(v1, v2)))
def cosine(v1, v2):
    score = 0
    prod = dot_product(v1, v2)
    len1 = math.sqrt(dot_product(v1, v1))
    len2 = math.sqrt(dot_product(v2, v2))
    if (len1 * len2) != 0:
        score = prod / (len1 * len2)
    return score
def LCS(X, Y):
    m = len(X)
    n = len(Y)
    # An (m+1) times (n+1) matrix
    C = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if X[i-1] == Y[j-1]:
                C[i][j] = C[i-1][j-1] + 1
            else:
                C[i][j] = max(C[i][j-1], C[i-1][j])
    return C
def backTrackAll(C, X, Y, i, j):
    if i == 0 or j == 0:
        return set([""])
    elif X[i-1] == Y[j-1]:
        return set([Z + "..." + X[i-1] for Z in backTrackAll(C, X, Y, i-1, j-1)])
    else:
        R = set()
        if C[i][j-1] >= C[i-1][j]:
            R.update(backTrackAll(C, X, Y, i, j-1))
        if C[i-1][j] >= C[i][j-1]:
            R.update(backTrackAll(C, X, Y, i-1, j))
        return R
def nindex(mystr, substr, n=0, index=0):
    for _ in xrange(n+1):
        index = mystr.index(substr, index) + 1
    return index - 1
def orderscore2(l1, l2):
    C = LCS(l1,l2)
    m = len(l1)
    n = len(l2)
    R = list(backTrackAll(C, l1, l2, m, n))
    R = R[0].split('...')
    R = R[1:]
    keys = 0
    data1 = []
    data2 = []
    if len(l1) < len(l2):
        for i in R:
            ni = data1.count(i)
            data1.append(i)
            k1 = nindex(l1,i,ni)
            ni = data2.count(i)
            data2.append(i)
            k2 = nindex(l2,i,ni)
            key = abs(k1 - k2)
            key = float(1)/(key+1)
            keys = keys + key
        F5 = keys/len(l2)
    else:
        for i in R:
            ni = data1.count(i)
            data1.append(i)
            k1 = nindex(l1,i,ni)
            ni = data2.count(i)
            data2.append(i)
            k2 = nindex(l2,i,ni)
            key = abs(k1 - k2)
            key = float(1)/(key+1)
            keys = keys + key
        if len(l1) != 0:
            F5 = keys/len(l1)
        else:
            F5 = 0
    return F5
def pairFeature(p1,p2,Trees1, Trees2):
    F = []
    l2= len(set(p1['fathertag'])) if len(set(p1['fathertag']))>len(set(p2['fathertag'])) else len(set(p2['fathertag']))
    F2 = float(len(set(p1['fathertag'])&set(p2['fathertag'])))/(1 if l2==0 else l2)
    l1 = p1['subPOS']
    l2 = p2['subPOS']
    F6 = orderscore2(l1, l2)
    T = []
    LT = []
    Tker = []
    DLT = []
    for tree1, tree2 in zip(Trees1, Trees2):

        treesim, lt1, lt2 = treeSimilar(tree1, tree2)
        #treesim1, aa,bb = treeSimilar(tree1, tree1)
        #treesim2, aa,bb = treeSimilar(tree2, tree2)
        #add3 = float(treesim)/sqrt(treesim1*treesim2)
        T.append(treesim)
        #treedis = simple_distance(tree1, tree2)
        #T.append(treedis)
        #LT.append(lt1)
        #LT.append(lt2)
        fadd = float(treesim)
        dislt = abs(lt1-lt2)
        #fadd2 =treedis-dislt
        #fadd2 = treedis
        DLT.append(dislt)
        LT.append(fadd)
        #LT.append(fadd2)
        #Tker.append(add3)

    #F = [F6]+ DLT + LT
    #F = LT
    F=LT + [F6]
    #F = Tker
    #score = combinedsimilarity(F, answer1, answer2)
    return F
def combinedsimilarity(TPKscore, Qc, Dc):
    Qtag = concept(Qc)
    Dtag = concept(Dc)
    if len(set(Qtag+Dtag))==0:
        conceptscore =0
    else:
        conceptscore = float(len(set(Qtag)&set(Dtag)))/len(set(Qtag+Dtag))
    if Qc == Dc:
        textscore = 1
    else:
        textscore = 0
    Score = TPKscore + [conceptscore, textscore]
    return Score


