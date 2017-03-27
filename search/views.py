from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User
from django.db.models import Avg

from django.contrib.contenttypes.models import ContentType
from django.contrib.comments.models import Comment

from itemrtdb.models import *
from itemrtproject import assessment_engine, formatter_engine

from django.db.models import Q
from datetime import datetime, timedelta

from decimal import *

import math, re, random, sys
import nltk
import nltk.tag, nltk.data
from nltk import tag
from nltk import tokenize

##from home import forms
from conceptlist import concept
from list import lists
from tfidf import tfidftest
from Treefeature import QFeature, pairFeature, parsesentencs
#from sklearn import preprocessing
#==============================================Search Modules ================================
def loadtxttoarray(txtname):
        datatxt = open(txtname, 'r').readlines()
        datafeature = []
        N=len(datatxt)
        for i in range(0, N):
            w=datatxt[i].split(" ")
            lw = len(w)
            w = w[0:lw-1]
            l = [float(j) for j in w]
            datafeature.append(l)
        return datafeature
def loadtxttolist(txtname):
        datatxt = open(txtname, 'r').readlines()
        datafeature = []
        N=len(datatxt)
        for i in range(0, N):
            w=datatxt[i].split(" ")
            lw = len(w)
            w = w[0:lw-1]
            w = ' '.join(w)
            datafeature.append(w)
        return datafeature
posidf = loadtxttoarray('posidf.txt')
myposlist = loadtxttolist('myposlist.txt')
depidf1 = loadtxttoarray('depidf1.txt')
mydependencylist1 = loadtxttolist('mydependencylist1.txt')
depidf2 = loadtxttoarray('depidf2.txt')
mydependencylist2 = loadtxttolist('mydependencylist2.txt')

def dot_product(v1, v2):
    return sum(map(lambda x: x[0] * x[1], zip(v1, v2)))

def cosine(v1, v2):
    prod = dot_product(v1, v2)
    len1 = math.sqrt(dot_product(v1, v1))
    len2 = math.sqrt(dot_product(v2, v2))
    if len1*len2 == 0:
        return 0
    else:
        return prod / (len1 * len2)

def cluster_rank(question, answer):
    #testfeature generation
    mytestposlist, mytestcontentlist, mytestanswerlist, mytestdependencylist1, mytestdependencylist2 = lists(question, answer)
    wtestdata0= tfidftest(mytestposlist, posidf, myposlist)
    wtestdata1_1= tfidftest(mytestdependencylist1, depidf1, mydependencylist1)
    wtestdata1_2= tfidftest(mytestdependencylist2, depidf2, mydependencylist2)
    for i,j,k in zip(wtestdata0,wtestdata1_1,wtestdata1_2):
        arraryX = i+j+k
        testfeature = arraryX
    fq= Question.objects.all()
    filtered_questions = fq
    return filtered_questions, answer, testfeature

def rerank(filtered_questions, ques, answer, testfeature):
    contentquery = nltk.word_tokenize(str(ques).lower())
    maxscore = 0
    for fq in filtered_questions:
        wordscore=0
        conceptscore = 0
        numans = 0
        lw = fq.std_answer.split("...")
        lwc = [c.strip() for c in lw]
        if len(lw) == len(answer[0].split("...")):
            numans = 1
        for word in answer:
            for sw in word.split("..."):
                if sw.strip() in lwc:
                    wordscore = 1
        conceptname = fq.concept.all()
        for name in conceptname:
            selected_tag = Concept.objects.get(name=name.name.encode('utf-8'))
            tags = selected_tag.words.all()
            for t in tags:
                if str(t) in lwc:
                    conceptscore = 1
        contentdb = nltk.word_tokenize(str(fq.content).lower())
        contentvec = set(contentquery)|set(contentdb)
        contentvec = list(contentvec)
        vecquery = []
        vecdb = []
        for i in range(len(contentvec)):
            if contentvec[i] in contentquery:
                vecquery.append(1)
            else:
                vecquery.append(0)
            if contentvec[i] in contentdb:
                vecdb.append(1)
            else:
                vecdb.append(0)
        simcontent = cosine(vecdb, vecquery)
        qf = fq.feature.split(",")
        lqf = len(qf)
        qf = [float(j) for j in qf[:lqf-1]]
        sim = cosine(qf, testfeature)
        if simcontent>0.8:
            fq.score = 5
        else:
            fqscore= numans+sim+wordscore+conceptscore
            fq.score = fqscore
            if fqscore>maxscore:
                maxscore=fqscore
        fq.save()
    gtscore = maxscore*2/3
    filtered_question = filtered_questions.filter(score__gt=gtscore).order_by('-score')
    return filtered_question

def patternsearch(ques, correctAnswer, choices):
    if correctAnswer:
        fq, answer, testfeature = cluster_rank(ques, correctAnswer)
        correctAnswer = [correctAnswer]
        filtered_questions = rerank(fq, ques, correctAnswer, testfeature)
    else:
        if len(choices) == 1:
            fq, answer, testfeature = cluster_rank(ques, choices[0])
            filtered_questions = rerank(fq, ques, choices, testfeature)
        elif len(choices) == 2:
            tQuestion0, answer0, testfeature = cluster_rank(ques, choices[0])
            tQuestion1, answer1, testfeature = cluster_rank(ques, choices[1])
            fq = tQuestion0|tQuestion1
            filtered_questions = rerank(fq, ques, choices, testfeature)
        elif len(choices) == 3:
            tQuestion0, answer0, testfeature = cluster_rank(ques, choices[0])
            tQuestion1, answer1, testfeature = cluster_rank(ques, choices[1])
            tQuestion2, answer2, testfeature = cluster_rank(ques, choices[2])
            fq = tQuestion0|tQuestion1|tQuestion2
            filtered_questions = rerank(fq, ques, choices, testfeature)
        else:
            tQuestion0, answer0, testfeature = cluster_rank(ques, choices[0])
            tQuestion1, answer1, testfeature = cluster_rank(ques, choices[1])
            tQuestion2, answer2, testfeature = cluster_rank(ques, choices[2])
            tQuestion3, answer3, testfeature = cluster_rank(ques, choices[3])
            fq = tQuestion0|tQuestion1|tQuestion2|tQuestion3
            filtered_questions = rerank(fq, ques, choices, testfeature)
    return filtered_questions

def texttagsearch(ques):
    question = ques.split(' ')
    print 'question: '+ str(question)
    filtered_question2 = Question.objects.all()
    maxscore = 0
    if len(question)>1:
        for fq in filtered_question2:
            contentdb = nltk.word_tokenize(str(fq.content).lower())
            contentvec = set(question)|set(contentdb)
            contentvec = list(contentvec)
            vecquery = []
            vecdb = []
            for i in range(len(contentvec)):
                if contentvec[i] in question:
                    vecquery.append(1)
                else:
                    vecquery.append(0)
                if contentvec[i] in contentdb:
                    vecdb.append(1)
                else:
                    vecdb.append(0)
            simcontent = cosine(vecdb, vecquery)
            if simcontent > maxscore:
                maxscore = simcontent
            fq.score = simcontent
            fq.save()
        gtscore = maxscore*2/3
        filtered_question1 = filtered_question2.filter(score__gt=gtscore).order_by('-score')
    else:
        filtered_question1 = Question.objects.all().filter(reduce(lambda x, y: x | y, [Q(std_answer__iregex='[[:<:]]' + word+ '[[:>:]]') for word in question])).order_by('id')
        if filtered_question1.count() == 0:
            filtered_question1 = Question.objects.all().filter(Q(content__icontains=ques)).order_by('id')
    #Using Haystack and Whoosh
    #print ques
    #questionlist = SearchQuerySet().autocomplete(content=ques)
    #print questionlist.count()
    #return questionlist
    return filtered_question1

def user_search(request):
    "Home view to display practice or trial testing modes"
    selected_mode=1
    all_tags = Tag.objects.all()
    return render(request, 'search.pattern.html', {'all_tags': all_tags,'selected_mode':selected_mode})

def withoutchoice(query):
    question = query.split(' ')
    filtered_question2 = Question.objects.all()
    predictFeature = []
    maxscore = 0
    minpf1 = 1
    maxpf1 = 0
    minpf2 = 1
    maxpf2 =0
    Qp,Qk, Qcont, Qp2 = parsesentencs([query], [''])
    print Qp2
    p, ptrees = QFeature(Qp2[0], Qk[0],1,2)
    for fq in filtered_question2:
        mp = fq.Mp.split('***')
        tmp = fq.Mk.split('***')
        mk = []
        for mi in tmp:
            mj = mi.split(',')
            if mj==['']:
                mj = []
            else:
                mj = [int(i) for i in mi]
            mk.append(mj)
        F, trees = QFeature(mp, mk,1,2)
        pf = pairFeature(F, p, trees, ptrees)
        pf1 = pf[0]
        pf2 = pf[1]
        if pf1<minpf1:
            minpf1 = pf1
        if pf1>maxpf1:
            maxpf1 = pf1
        if pf2<minpf2:
            minpf2 = pf2
        if pf2>maxpf2:
             maxpf2 = pf2
        predictFeature.append(pf)
    #min_max_scaler = preprocessing.MinMaxScaler()
    #predict_minmax = min_max_scaler.transform(predictFeature)
    rg1 = maxpf1-minpf1
    rg2 = maxpf2-minpf2
    if rg1==0:
        rg1 =1
    if rg2 ==0:
        rg2 = 1
    predict_minmax = [[float(x[0]-minpf1)/rg1,float(x[1]-minpf2)/rg2] for x in predictFeature]
    #score =model.predict(predictFeature)

    for fq,sc in zip(filtered_question2,predict_minmax):
        contentdb = nltk.word_tokenize(str(fq.content).lower())
        contentvec = set(question)|set(contentdb)
        contentvec = list(contentvec)
        vecquery = []
        vecdb = []
        for i in range(len(contentvec)):
            if contentvec[i] in question:
                vecquery.append(1)
            else:
                vecquery.append(0)
            if contentvec[i] in contentdb:
                vecdb.append(1)
            else:
                vecdb.append(0)
        simcontent = cosine(vecdb, vecquery)
        if simcontent>0.8:
            score = 1
        else:
            score = 0.25*sc[0]+0.67*sc[1]
        if score > maxscore:
            maxscore = score
        fq.score = score
        fq.save()
    gtscore = maxscore*2/3
    filtered_question = filtered_question2.filter(score__gt=gtscore).order_by('-score')
    return filtered_question
@login_required
def adaptivesearch (request):
    selected_mode=2
    topics = Topic.objects.all().order_by("id")
    # Init
    selected_topic = None
    topic_id = 0
    topic_count = {}
    filtered_questions = Question.objects.all()
    count = None
    tags = request.GET.getlist("tags")
    choiceA = request.GET.getlist("choiceA")
    choiceB = request.GET.getlist("choiceB")
    choiceC = request.GET.getlist("choiceC")
    choiceD = request.GET.getlist("choiceD")
    correctAnswer = request.GET.getlist("correctAnswer")
    tags = str(tags)
    correctAnswer = str(correctAnswer)
    tags=tags.lower()
    tags=tags[3:len(tags)-2]
    ques = str(tags)
    choices = []
    if choiceA:
        choiceA = str(choiceA)
        choiceA=choiceA.lower()
        choiceA=choiceA[3:len(choiceA)-2]
        choiceA = str(choiceA)
        if choiceA:
            choices.append(choiceA)
    if choiceB:
        choiceB = str(choiceB)
        choiceB=choiceB.lower()
        choiceB=choiceB[3:len(choiceB)-2]
        choiceB = str(choiceB)
        if choiceB:
            choices.append(choiceB)
    if choiceC:
        choiceC = str(choiceC)
        choiceC=choiceC.lower()
        choiceC = choiceC.split("'")[1]
        #choiceC=choiceC[3:len(choiceC)-2]
        choiceC = str(choiceC)
        if choiceC:
            choices.append(choiceC)
    if choiceD:
        choiceD = str(choiceD)
        choiceD=choiceD.lower()
        choiceD=choiceD[3:len(choiceD)-2]
        choiceD = str(choiceD)
        if choiceD:
            choices.append(choiceD)
    content = nltk.sent_tokenize(ques)
    correctAnswer=correctAnswer.lower()
    correctAnswer=correctAnswer[3:len(correctAnswer)-2]
    correctAnswer = str(correctAnswer)

    tokens = nltk.word_tokenize(ques)
    length = len(tokens)
    tagged = nltk.pos_tag(tokens)
    key = ' '.join([tup[1] for tup in tagged])

    if tags:
        if '*' in ques:
            if len(choices)>0:
                filtered_questions = patternsearch(ques, correctAnswer, choices)
            else:
                filtered_questions = withoutchoice(ques)
        else:
            filtered_questions = texttagsearch(ques)
        #filtered_questions = Question.objects.all().filter(Q(choiceparse__icontains=key)|Q(content__icontains=tags)).order_by('id')

        count = filtered_questions.count()
        print count
        if request.GET.get("topic") != None:
            topic_id = int(request.GET.get("topic"))
        # Obtain counts of questions per topic
        for topic in topics:
            topicQcount = filtered_questions.filter(topic=topic).count()
            topic_count[topic]=topicQcount

        if topic_id > 0:
            sel = filtered_questions.filter(topic__id=topic_id).order_by('-result')
            selected_topic = Topic.objects.get(id=topic_id)
        else: #all topics
    		sel = filtered_questions
        paginator = Paginator(sel, 10)

        page = request.GET.get('page')

        try:
            questions = paginator.page(page)
        except PageNotAnInteger:
            questions = paginator.page(1)
        except EmptyPage:
            questions = paginator.page(paginator.num_pages)

    else:
        questions = None

        # Remove page number from querystring
    q = request.GET
    z = q.copy()
    try:
        del z['page']
    except KeyError:
        pass
    querystring = '?' + z.urlencode()

    return render(request, 'search.pattern.html', { 'selected_mode':selected_mode,'choices':choices, 'tags':tags, 'key':key, 'questions': questions, 'filtered_questions' : filtered_questions,'querystring': querystring, 'count':count, 'topic_count':topic_count, 'selected_topic':selected_topic, 'topics':topics, 'choiceA':choiceA, 'choiceB':choiceB, 'choiceC':choiceC, 'choiceD':choiceD})

