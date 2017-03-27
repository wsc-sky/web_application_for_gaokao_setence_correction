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
from itemrtweb import forms
from django.db.models import Q
from datetime import datetime, timedelta

from decimal import *

import math, re, random, sys
import nltk
import nltk.tag, nltk.data
from nltk import tag
from nltk import tokenize
from simplify_brown_tag import simplify_brown_tag
from conceptlist import concept
from list import lists
from tfidf import tfidftest

#############################ACCOUNT##############################

def account_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate user w/db
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                # Success, check permissions (user/admin)
                if user.is_staff:
                    # Staff redirected to control panel
                    return redirect('/control/')
                else:
                    # User redirected to practice homepage
                    return redirect('/home/')
            else:
                if user.last_login == user.date_joined:
                    # Not activated
                    return render(request, 'auth.login.html', {'error': 'inactive'})
                else:
                    # User account has been disabled
                    return render_to_response('auth.login.html', {'error': 'disabled'}, context_instance=RequestContext(request))
        else:
            # User account not found or password is incorrect
            return render_to_response('auth.login.html', {'error': 'incorrect'}, context_instance=RequestContext(request))
    else:
        if request.user.is_authenticated():
            if 'next' not in request.GET:
                # Why are you visiting my sign in page again?
                return redirect('/')
            else:
                return render(request, 'auth.login.html', {'error':'permission'})
        else:
            return render(request, 'auth.login.html')

def account_login2(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate user w/db
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                # Success, check permissions (user/admin)
                if user.is_staff:
                    # Staff redirected to control panel
                    return redirect('/control/')
                else:
                    # User redirected to practice homepage
                    return redirect('/home/')
            else:
                if user.last_login == user.date_joined:
                    # Not activated
                    return render(request, 'auth.login2.html', {'error': 'inactive'})
                else:
                    # User account has been disabled
                    return render_to_response('auth.login2.html', {'error': 'disabled'}, context_instance=RequestContext(request))
        else:
            # User account not found or password is incorrect
            return render_to_response('auth.login2.html', {'error': 'incorrect'}, context_instance=RequestContext(request))
    else:
        if request.user.is_authenticated():
            if 'next' not in request.GET:
                # Why are you visiting my sign in page again?
                return redirect('/')
            else:
                return render(request, 'auth.login2.html', {'error':'permission'})
        else:
            return render(request, 'auth.login2.html')
def account_logout(request):
    # Logout for user
    logout(request)

    return render_to_response('auth.logout.html', {}, context_instance=RequestContext(request))

def account_register(request):
    if request.method == 'POST':
        form = forms.RegistrationForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Process account registration
            user = User.objects.create_user(username=form.cleaned_data['email'], email=form.cleaned_data['email'], password=form.cleaned_data['password'])
            user.first_name=form.cleaned_data['first_name']
            user.last_name=form.cleaned_data['last_name']
            user.is_active = False
            user.save()

            # Generate a activation key using existing salt for pwd
            algorithm, iterations, salt, hashed = user.password.split('$', 3)
            activation_key = make_password(user.email, salt, algorithm)
            algorithm, iterations, salt, activation_key = activation_key.split('$', 3)
            activation_key = activation_key[:-1]
            # Alternative char for + and /
            activation_key = activation_key.replace('+','-').replace('/','_')

            title = 'Account Activation'
            content = render_to_string('register.email', {'first_name': user.first_name, 'last_name': user.last_name, 'is_secure': request.is_secure(), 'host': request.get_host(), 'activation_key': activation_key, 'sender': settings.PROJECT_NAME})

            send_mail(title, content, settings.PROJECT_NAME + ' <' + settings.EMAIL_HOST_USER + '>', [user.email])

            return render(request, 'account.register.success.html')
    else:
        # Display new form for user to fill in
        form = forms.RegistrationForm()

    return render(request, 'account.register.form.html', {'form': form})

def account_activate(request):
    # Already activated
    if request.user.is_authenticated():
        return render(request, 'account.activate.success.html', {'error': 'activated'})

    if request.method == 'GET':
        # Get activation details
        activation_key = request.GET.get('key')

        # No activation key, throw to login page
        if activation_key is None:
            return redirect('/accounts/login/')

        # Keep activation key in session awaiting login
        request.session['activation_key'] = activation_key

        form = forms.ActivationForm()
    else:
        # Attempt to activate user using given user, password and key
        form = forms.ActivationForm(request.POST)
        if form.is_valid():
            # Try logging in
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])

            if user is None:
                form.activation_error = 'incorrect'
            else:
                # Already active? error!
                if user.is_active:
                    form.activation_error = 'expired'
                else:
                    # Match activation key
                    algorithm, iterations, salt, hashed = user.password.split('$', 3)
                    activation_key = make_password(user.email, salt, algorithm)
                    algorithm, iterations, salt, activation_key = activation_key.split('$', 3)
                    activation_key = activation_key[:-1]
                    # Alternative char for + and /
                    activation_key = activation_key.replace('+','-').replace('/','_')

                    form.key1 = request.session['activation_key']
                    form.key2 = activation_key

                    # Match keys
                    if activation_key == request.session['activation_key']:
                        # Activated, login and proceed
                        user.is_active = True
                        user.save()
                        login(request, user)

                        return render(request, 'account.activate.success.html')
                    else:
                        # Key expired!
                        form.activation_error = 'expired'

    return render(request, 'account.activate.form.html', {'form': form})

def account_forgot(request):
    if request.method == 'POST':
        form = forms.PasswordForgetForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Retrieve user from db
            try:
                user = User.objects.get(email=form.cleaned_data['email'])
            except User.DoesNotExist:
                return redirect('/accounts/forgot/?error=nouser')

            # Generate a reset key using existing salt for pwd
            algorithm, iterations, salt, hashed = user.password.split('$', 3)
            reset_key = make_password(user.email, salt, algorithm)
            algorithm, iterations, salt, reset_key = reset_key.split('$', 3)
            reset_key = reset_key[:-1]
            # Alternative char for + and /
            reset_key = reset_key.replace('+','-').replace('/','_')

            title = 'Password Reset'
            content = render_to_string('passwordreset.email', {'first_name': user.first_name, 'last_name': user.last_name, 'host': request.get_host(), 'reset_key': reset_key, 'sender': settings.PROJECT_NAME, 'email': user.email})

            send_mail(title, content, settings.PROJECT_NAME + ' <' + settings.EMAIL_HOST_USER + '>', [user.email])

            return render(request, 'account.forgot.success.html')
    else:
        # Display new form for user to fill in
        form = forms.PasswordForgetForm()

    return render(request, 'account.forget.form.html', {'form': form})

def account_reset(request):
    if request.user.is_authenticated():
        pass
    else:
        if request.method == 'GET':
            # TODO: Error messages if key is not valid or email is wrong

            # Reset password for user who has forgotten it
            # Get user from request data
            user_email = request.GET.get('user')

            # Retrieve user from db
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                return redirect('/accounts/forgot/?error=nouser')

            # Get reset key from request data
            reset_key_input = request.GET.get('key')

            # No reset key, throw to login page
            if reset_key_input is None:
                return redirect('/accounts/forgot/?error=nokey')

            # Match reset key
            algorithm, iterations, salt, hashed = user.password.split('$', 3)
            reset_key = make_password(user.email, salt, algorithm)
            algorithm, iterations, salt, reset_key = reset_key.split('$', 3)
            reset_key = reset_key[:-1]
            # Alternative char for + and /
            reset_key = reset_key.replace('+','-').replace('/','_')

            # Match keys
            if reset_key == reset_key_input:
                # Reset keys match, render page for user to reset
                # Store reset email in session
                request.session['reset_email'] = user_email

                form = forms.PasswordResetForm(initial={'email': user_email})
            else:
                # Key expired!
                return redirect('/accounts/forgot/?error=keymismatch')
        elif request.method == 'POST':
            form = forms.PasswordResetForm(request.POST)
            if form.is_valid():
                # Perform real resetting of account
                # Check if emails from form and session matches
                if form.cleaned_data['email'] == request.session['reset_email']:
                    # Get user
                    try:
                        user = User.objects.get(email=request.session['reset_email'])
                    except User.DoesNotExist:
                        return redirect('/accounts/forgot/?error=nouser')

                    # Update password of user in system
                    user.set_password(form.cleaned_data['password'])
                    user.save()

                    # Success, login user and display success page
                    user = authenticate(username=user.username, password=form.cleaned_data['password'])
                    login(request, user)

                    return render(request, 'account.reset.success.html')
                else:
                    return redirect('/accounts/forgot/?error=email')

        return render(request, 'account.reset.form.html', {'form': form})

#############################HOME PAGE##############################
def home(request):
    all_tags = Tag.objects.all()
    "Main page of the site, redirects if logged in"
    # Redirect to respective home portals
    if request.user.is_authenticated():

        # Record usage for stats purpose
        page = "home"
        # Never accessed this page before, or last access was more than 10 mins ago
        if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
            usage = UserUsage(user=request.user, page=page)
            usage.save()
            request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
        # End usage recording

        if request.user.is_staff:
            # Redirect staff to staff portal
            return redirect('/home/')
        else:
            # Redirect user to user portal
            return redirect('/home/')

    # Home page for non authenticated users
    return render(request, 'itemrtweb/test.html', {'all_tags':all_tags})

@login_required
def user_home(request):
    "Home view to display practice or trial testing modes"
    all_tags = Tag.objects.all()
    return render(request, 'itemrtweb/home.html', {'all_tags': all_tags})

@login_required
def about(request):
    "Home view to display practice or trial testing modes"

    return render(request, 'itemrtweb/about.html')

@login_required
def aboutsurvey(request):
    "Home view to display practice or trial testing modes"

    return render(request, 'itemrtweb/about.survey.html')

@login_required
def aboutvideo(request):
    "Home view to display practice or trial testing modes"

    return render(request, 'itemrtweb/about.video.html')

@login_required
def survey(request):
    "Survey form for user to submit feedbacks"

    return render(request, 'itemrtweb/survey.form.html')

@login_required
def feedback(request):
    "Feedback form for user to submit feedbacks"

    if request.method == 'POST':
        form = forms.FeedbackForm(request.POST)
        if form.is_valid():
            # Maybe in the future this can be done in a webform with feedback id generated

            title = 'Feedback Received from ' + request.user.get_full_name()
            content = render_to_string('feedback.email', {'first_name': request.user.first_name, 'last_name': request.user.last_name, 'feedback': form.cleaned_data['feedback']})

            send_mail(title, content, settings.PROJECT_NAME + ' <' + settings.EMAIL_HOST_USER + '>', ['grammarexpress1@gmail.com'])

            return render(request, 'itemrtweb/feedback.success.html')
    else:
        # Display new form for user to fill in
        form = forms.FeedbackForm()

    return render(request, 'itemrtweb/feedback.form.html', {'form': form})

#############################PAPER TEST##############################
@login_required
def papertest(request, test_id=None):
    # Init mode
    selected_mode = 2
    "Boombastic function! Change with care."
    # Record usage for stats purpose
    page = "paper_test"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    if not test_id:
        if request.method == 'POST' and 'test_id' in request.POST and request.POST['test_id']:
            return redirect('/test/paper/'+request.POST['test_id']+'/')
        elif request.method == 'POST' and 'num_qn' in request.POST and request.POST['num_qn'] and 'topics' in request.POST:
            # Check if all param is in
            # Get number of questions and difficulty
            avg = 3
            if request.POST['qn_diff']: avg = int(request.POST['qn_diff'])

            numQns = int(request.POST['num_qn']) ## Increase Capacity to 50.
            if numQns > 20:
                numQns = 20

            testid = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(6))

            #### VERY IMPORTANT TODO:: CHECK FOR UNIQUE ID
            new_test = Test(id=testid, user=request.user, assessment=Assessment.objects.all().get(name='Paper Test'))
            new_test.save()

            numQns = int(numQns)

            topics_selected = request.POST.getlist('topics')

            topics_all = list(topics.values_list('id', flat=True))

            for topic_id in topics_selected:
                topics_all.remove(int(topic_id))
            if avg > 0 :
                question_pool = Question.objects.all().filter(difficulty=int(avg))
            else:
                question_pool = Question.objects.all()
            question_pool = question_pool.exclude(topic__in=topics_all)

            for i in range (0, numQns):
                # Get a random question and add to paper
                question_pool = question_pool.exclude(id__in=new_test.questions.all().values_list('id'))

                if question_pool:
                    question = question_pool[random.randint(0, question_pool.count()-1)]
                    newTestQuestion = TestQuestion(question=question, test=new_test)
                    newTestQuestion.save()

            return redirect('/test/paper/'+str(testid)+'/')
        elif request.method == 'POST':
            error = {}
            if 'num_qn' not in request.POST or not request.POST['num_qn']:
                error['num_qn'] = True
            return render(request, 'itemrtweb/papertest.home.html', {'error': error, 'topics': topics, 'selected_mode':selected_mode})

        return render(request, 'itemrtweb/papertest.home.html', {'topics': topics, 'selected_mode':selected_mode})
    else:
        # test_id is available, render test instead
        test = Test.objects.all().get(id=test_id)


        return render(request, 'itemrtweb/papertest.question.html', {'test': test, 'selected_mode':selected_mode})


@login_required
def papertest_2(request, test_id=None):
    # Init mode
    selected_mode = 2
    "Boombastic function! Change with care."
    # Record usage for stats purpose
    page = "paper_test"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    if not test_id:
        if request.method == 'POST' and 'test_id' in request.POST and request.POST['test_id']:
            return redirect('/test/paper/'+request.POST['test_id']+'/')
        elif request.method == 'POST' and 'num_qn' in request.POST and request.POST['num_qn'] and 'topics' in request.POST:
            # Check if all param is in
            # Get number of questions and difficulty
            avg = 3
            if request.POST['qn_diff']: avg = int(request.POST['qn_diff'])

            numQns = int(request.POST['num_qn']) ## Increase Capacity to 50.
            if numQns > 20:
                numQns = 20

            testid = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(6))

            #### VERY IMPORTANT TODO:: CHECK FOR UNIQUE ID
            new_test = Test(id=testid, user=request.user, assessment=Assessment.objects.all().get(name='Paper Test'))
            new_test.save()

            numQns = int(numQns)

            topics_selected = request.POST.getlist('topics')

            topics_all = list(topics.values_list('id', flat=True))

            for topic_id in topics_selected:
                topics_all.remove(int(topic_id))
            if avg > 0 :
                question_pool = Question.objects.all().filter(difficulty=int(avg))
            else:
                question_pool = Question.objects.all()
            question_pool = question_pool.exclude(topic__in=topics_all)

            for i in range (0, numQns):
                # Get a random question and add to paper
                question_pool = question_pool.exclude(id__in=new_test.questions.all().values_list('id'))

                if question_pool:
                    question = question_pool[random.randint(0, question_pool.count()-1)]
                    newTestQuestion = TestQuestion(question=question, test=new_test)
                    newTestQuestion.save()

            return redirect('/test/paper_2/'+str(testid)+'/')
        elif request.method == 'POST':
            error = {}
            if 'num_qn' not in request.POST or not request.POST['num_qn']:
                error['num_qn'] = True
            return render(request, 'itemrtweb/papertest.home_2.html', {'error': error, 'topics': topics, 'selected_mode':selected_mode})

        return render(request, 'itemrtweb/papertest.home_2.html', {'topics': topics, 'selected_mode':selected_mode})
    else:
        # test_id is available, render test instead
        test = Test.objects.all().get(id=test_id)

        return render(request, 'itemrtweb/papertest.question_2.html', {'test': test, 'selected_mode':selected_mode})





def question_selection(question_pool,numQns,avg,new_test):
    below = (numQns + 2) / 5
    above = (numQns + 2) / 5
    middle = numQns - below - above

    if avg == 1 or avg == 5:
        below = 0
        above = 0
        middle = numQns

    for i in range (0, below):
        # Get a random question and add to paper
        question_pool_below = question_pool.filter(difficulty=int(avg-1))
        question_pool_below = question_pool_below.exclude(id__in=new_test.questions.all().values_list('id'))

        if question_pool_below:
            question = question_pool_below[random.randint(0, question_pool_below.count()-1)]
            newTestQuestion = TestQuestion(question=question, test=new_test)
            newTestQuestion.save()

    for i in range (0, above):
        # Get a random question and add to paper
        question_pool_above = question_pool.filter(difficulty=int(avg+1))
        question_pool_above = question_pool_above.exclude(id__in=new_test.questions.all().values_list('id'))

        if question_pool_above:
            question = question_pool_above[random.randint(0, question_pool_above.count()-1)]
            newTestQuestion = TestQuestion(question=question, test=new_test)
            newTestQuestion.save()

    for i in range (0, middle):
        # Get a random question and add to paper
        question_pool_middle = question_pool.filter(difficulty=int(avg))
        question_pool_middle = question_pool_middle.exclude(id__in=new_test.questions.all().values_list('id'))

        if question_pool_middle:
            question = question_pool_middle[random.randint(0, question_pool_middle.count()-1)]
            newTestQuestion = TestQuestion(question=question, test=new_test)
            newTestQuestion.save()

@login_required
def papertestsubmit(request, test_id):
    test = Test.objects.all().get(id=test_id)
    source_all = 0;   
    if request.method == 'POST':
        # Check each question if it has been attempted
        for question in test.questions.all():
            try:
                # Previously saved response available? OK do nothing for now.
                test_response = TestResponse.objects.filter(test=test).filter(user=request.user).get(question=question)
                pass
            # Otherwise new response, create object
            except ObjectDoesNotExist:
                test_response = TestResponse(test=test, user=request.user, question=question, response='<No Answer Given>', criterion=question.marks, assessment=test.assessment)
                test_response.save()

        # Assign a score for each question
        total_ability = 0

        for question in test.questions.all():
            test_response = TestResponse.objects.filter(test=test).filter(user=request.user).get(question=question)

            response = test_response.response
            response = response.replace(' ', '').replace('\\n', '').replace('\\r', '').replace('\\t', '')
            response_s = response.split(';')
            # Get actual answer in string
            #delete [question.answers.all()[0].content.lower()]
            answer_text = question.choice
            answer_text = answer_text.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
            answer_s = question.choice.split(';')
            correctness = 0

            #source_all = range(0,len(response_s))
            #
            for i in range(0,len(response_s)):
                #if re.match('^'+answer_s[i]+'$', response_s[i])
                if answer_s[i]==response_s[i]:
                    correctness = question.answers.all()[0].correctness
                    source_all=source_all+1
            

            print >> sys.stderr, response + " == " + answer_text + " : " + str(correctness)
            # Update correctness
            test_response.correctness = correctness

            # Update ability
            total_ability = total_ability + correctness
            test_response.ability = total_ability

            test_response.save()

        test.state = True
        test.save()


        # Prevent resubmission of test
        return redirect('/test/paper/submit/' + test_id + '/')

    elif request.method == 'GET':
        ability = TestResponse.objects.all().filter(test=test).order_by('-date')[0]
        filtered = TestResponse.objects.all().filter(test=test).order_by('date')
        correct = {}
        total={}
        for i in range(1,6):
            correct[i] = filtered.filter(correctness=1).filter(question__difficulty=i).count()
            total[i] = filtered.filter(question__difficulty=i).count()
        return render(request, 'itemrtweb/papertest.submit.html', {'test': test, 'final_score': int(test.score),'test_scoure': int(source_all) ,'correct':correct, 'total':total})

@login_required
def papertestutil(request, test_id=None, util_name=None):
    "Util functions for Boombastic function!"

    if test_id:
        test = Test.objects.all().get(id=test_id)
        # Util to return test endtime
        if util_name == 'getendtime':
            
            #time = test.questions.count()*1
            time = 10
            endtime = test.generated+timedelta(minutes=time) # Time Control

            return HttpResponse(endtime.isoformat())
        elif util_name == 'save':
            if 'qn_id' in request.POST and request.POST['qn_id']:
                # Get question (or nothing) from orm
                question = Question.objects.all().get(id=request.POST['qn_id'])

                # Check test not completed, question exists
                if test.state == False and test.questions.filter(id=question.id).exists():
                    # Check that there was a answer sent together with message
                    if 'answer1' in request.POST and request.POST['answer1']:
                        try:
                            # Previously saved response available? Resave if so!
                            test_response = TestResponse.objects.filter(test=test).filter(user=request.user).get(question=question)
                            test_response.response =request.POST['answer1']+';'+request.POST['answer2']+';'+request.POST['answer3']+';'+request.POST['answer4']+';'+request.POST['answer5']+';'+request.POST['answer6']+';'+request.POST['answer7']+';'+request.POST['answer8']+';'+request.POST['answer9']+';'+request.POST['answer10']
                            test_response.save()
                        # Otherwise new response, create object
                        except ObjectDoesNotExist:
                            response_all =request.POST['answer1']+';'+request.POST['answer2']+';'+request.POST['answer3']+';'+request.POST['answer4']+';'+request.POST['answer5']+';'+request.POST['answer6']+';'+request.POST['answer7']+';'+request.POST['answer8']+';'+request.POST['answer9']+';'+request.POST['answer10']
                            test_response = TestResponse(test=test, user=request.user, question=question, response=response_all, criterion=question.marks, assessment=test.assessment)
                            test_response.save()

                        return HttpResponse("Saved")
                    # Otherwise no answer just return nothing happened!

                    if 'answer' in request.POST and request.POST['answer']:
                        try:
                            # Previously saved response available? Resave if so!
                            test_response = TestResponse.objects.filter(test=test).filter(user=request.user).get(question=question)
                            test_response.response = request.POST['answer']
                            test_response.save()
                        # Otherwise new response, create object
                        except ObjectDoesNotExist:
                            test_response = TestResponse(test=test, user=request.user, question=question, response=request.POST['answer'], criterion=question.marks, assessment=test.assessment)
                            test_response.save()

                        return HttpResponse("Saved")
                    # Otherwise no answer just return nothing happened!
                    else:
                        return HttpResponse("Empty")
    raise Http404


@login_required
def papertestprogress (request):
    #Init
    selected_mode = 2
    correct={}
    total={}
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    for topic in topics:
        response = Response.objects.all().filter(user=request.user).filter(assessment__name__exact='Paper Test').filter(question__topic__exact=topic).order_by('-date')

        total[topic.id] = 0
        correct[topic.id]= 0
        for i in response:
            correct[topic.id]  += int(i.correctness)
        total[topic.id]  = response.count()

    active_engine = Assessment.objects.all().filter(active=True).get(id=5)
    engine = getattr(assessment_engine, active_engine.engine)()

    topic_ability = {}
    for topic in topics:
        ability = engine.get_user_ability(user=request.user, topic=topic)
        if ability is not None:
            topic_ability[topic] = ability
        else:
            topic_ability[topic] = None

    allR = Response.objects.all().filter(user=request.user).filter(assessment__name__exact='Paper Test')
    total["all"]  = allR.count()
    correct["all"] = 0
    for i in allR:
        correct["all"]  += int(i.correctness)
    if total["all"] is not 0:
        topic_ability["all"] = round (float(correct['all'])/float(total['all']) * 100 ,2)
    else:
        topic_ability["all"] = None

    tests = Test.objects.filter(assessment_id=5).filter(user=request.user).order_by('-generated')
    tlist={}
    qlist={}
    plist={}
    wlist={}
    for test in tests:
        test_response = TestResponse.objects.filter(test=test).filter(user=request.user).order_by('-ability')
        if test_response.count() > 0:
            tlist[test.id]=int(test_response[0].ability)
            qlist[test.id]=test_response.count()
            plist[test.id]=round(float(test_response[0].ability) / float( test_response.count()) * 100,2)
        else:
            tlist[test.id]=0
            plist[test.id]=0
            qlist[test.id]=0

        test_question = TestQuestion.objects.filter(test=test)
        test_topic=Topic.objects.none()

        get_topic = None
        related_topic = Topic.objects.none()
        topic_get=[]
        for q in test_question:
            get_topic = Topic.objects.filter(id=q.question.topic.id)
            related_topic = related_topic | get_topic
        for t in related_topic:
            topic_get.append(t.name)
            topic_get2=' '.join(topic_get)
        wlist[test.id]=topic_get2
        # Get list of questions that user has previously commented on
    questions_commented_id = Comment.objects.all().filter(content_type=ContentType.objects.get_for_model(Question)).filter(user=request.user).values_list('object_pk')
    questions_commented = Question.objects.all().filter(pk__in=questions_commented_id)

    return render(request, 'itemrtweb/papertest.progress.html', {'correct':correct,'total':total,'topic_ability':topic_ability,'topics':topics, 'tests': tests, 'tlist':tlist,'qlist':qlist,'plist':plist,'wlist':wlist,'questions_commented':questions_commented, 'selected_mode':selected_mode})

@login_required
def topic (request):
    #Init Mode
    selected_mode = 2
    correct={}
    total={}
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    for topic in topics:
        response = Response.objects.all().filter(user=request.user).filter(question__topic__exact=topic).order_by('-date')

        total[topic.id] = 0
        correct[topic.id]= 0
        for i in response:
            correct[topic.id]  += int(i.correctness)
        total[topic.id]  = response.count()

    dict_total = {}
    dict_correct = {}
    topics = Topic.objects.all().order_by('position')
    for topic in topics:
        response = Response.objects.all().filter(user=request.user).filter(question__topic__exact=topic).order_by('-date')
        topicall = {}
        topiccorrect = {}
        for i in range(1,6):
            response_diff = response.filter(question__difficulty=i)
            topicall[i] = 0
            topiccorrect[i]=0
            for j in response_diff:
                topiccorrect[i]  += int(j.correctness)
            topicall[i] = response_diff.count()
        dict_correct[topic.id]=topiccorrect
        dict_total[topic.id]=topicall

    return render(request, 'itemrtweb/topic.html', {'correct':correct,'total':total, 'topics':topics, 'dict_total':dict_total, 'dict_correct':dict_correct, 'selected_mode':selected_mode})

#############################CAT TEST##############################
@login_required
def trialtest(request):
    #Init System and Mode
    selected_mode = 2
    #"Placeholder for trial test"
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Record usage for stats purpose
    page = "cat_test"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    if 'complete' in request.GET and request.GET['complete']:
        complete = True
        if 'ability' in request.GET and request.GET['ability']:
            ability = request.GET['ability']
    else:
        complete = False
        ability = None

    return render(request, 'itemrtweb/cattest.html', {'topics':topics, 'complete': complete, 'ability': ability, 'selected_mode':selected_mode})

@login_required
def trialtest_generate(request):
    if request.method == 'POST':
        testid = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(6))

        #### VERY IMPORTANT TODO:: CHECK FOR UNIQUE ID
        new_test = Test(id=testid,user=request.user, assessment=Assessment.objects.all().get(name='CAT Test'))
        new_test.save()

        # Clear previous test questions if any
        request.session['trialtest_current_qn'] = None

        # Store topic in session, change this to db storage soon
        request.session['trialtest_topic_id'] = int(request.POST['topic'])

        return redirect('/test/cat/go/'+testid+'/')
    return redirect('/')

@login_required
def trialtest_go(request, test_id):
    #Init System and Mode
    selected_mode = 2
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Get Test object
    test = Test.objects.all().get(id=test_id)

    # Selected topic
    topic_id = request.session['trialtest_topic_id']
    if topic_id > 0:
        topic = Topic.objects.all().get(id=topic_id)
    else:
        topic = None

    # Init session variable for question
    if 'trialtest_current_qn' not in request.session:
        request.session['trialtest_current_qn'] = None

    # Debug data
    debug = {}

    # Error data
    error = {}

    # GET Request or POST w/o session data >> Load Question
    # POST Request >> Answer Question
    if request.method == 'GET' or request.session['trialtest_current_qn'] is None:
        # Generate new question if not resuming
        if request.session['trialtest_current_qn'] == None:
            # Get assessment engine for CAT Test and dynamically load engine
            active_engine = Assessment.objects.all().get(name='CAT Test')
            engine = getattr(assessment_engine, active_engine.engine)()

            # Initialise session storage for assessment engine
            if 'engine_store' not in request.session:
                request.session['engine_store'] = None

            # Request a new question from the assessment engine
            question = engine.get_next_question(user=request.user, test=test, topic=topic, session_store=request.session['engine_store'])

            # Get current ability for debug purposes
            debug['ability'] = engine.get_user_ability(user=request.user, test=test)

            # Test ends if question is None (out of questions), redirect to completion screen
            if not question:
                return render(request, 'itemrtweb/trialtest.html', {'topics':topics, 'complete': True, 'ability': engine.get_user_ability(user=request.user, test=test), 'selected_mode':selected_mode})

            debug['answer'] = question.answers.all()[0].content

            # Update the question to session (for persistance if user refresh page/relogin)
            request.session['trialtest_current_qn'] = question.id

            # Update time starts from here
            request.session['trialtest_time'] = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        else:
            # Reload question from session data if resuming practice or page refresh
            question = Question.objects.all().get(id=request.session['trialtest_current_qn'])

        # Rendering at end of page
    else:
        # Submitting a test question
        if 'qid' in request.POST and request.POST['qid']:
            qnid_post = request.POST['qid']
        else:
            qnid_post = None

        qnid_session = request.session['trialtest_current_qn']

        if qnid_post != qnid_session:
            # Something strange is happening, missing qid from form or mismatch between form and session, TODO: Handle this PROPERLY
            debug['qnid_post'] = qnid_post
            debug['qnid_session'] = qnid_session

        # Reload question from session data
        question = Question.objects.all().get(id=qnid_session)

        # Check if answer was submitted
        if 'ans' in request.POST and request.POST['ans']:
            choice = request.POST['ans']

            # Get assessment engine for CAT Test and dynamically load engine
            active_engine = Assessment.objects.all().get(name='CAT Test')
            engine = getattr(assessment_engine, active_engine.engine)()

            # Initialise session storage for assessment engine
            if 'engine_store' not in request.session:
                request.session['engine_store'] = None

            # Match answer using assessment engine
            result = engine.match_answers(user=request.user, test=test, response=choice, question=question, session_store=request.session['engine_store'])

            # Restore updated engine store
            request.session['engine_store'] = result['session_store']

            # Reset current practice qn to None
            request.session['trialtest_current_qn'] = None

            # Answer is correct if full points is awarded
            if result['correctness'] == 1.0:
                correct = True
            else:
                correct = False

            # Get correct answer
            question.answer = question.answers.all()[0]

            # Terminating condition is true!
            if result['terminate']:
                ability_list = engine.get_user_ability_list(user=request.user, test=test)

                test.state = True
                test.save()

                return redirect('/test/cat/'+ str(test_id) )
                return render(request, 'itemrtweb/cattest.html', {'topics':topics, 'complete': True, 'ability': result['ability'], 'ability_list': ability_list, 'debug': result['debug_t_cond'], 'selected_mode':selected_mode})
            # Otherwise, no need to render a answer page, so we just save answers and then load next qn
#            else:
 #               return redirect(request.path)


            # Format question for web mode
            formatter = formatter_engine.WebQuestionFormatter()
            question = formatter.format(question)
            test = Test.objects.all().get(id=test_id)
            answered = TestResponse.objects.all().filter(test=test).order_by('date')

            # Temp variable to allow ajax through https
            host = request.get_host()
            is_secure = not "localhost" in host

            # Kill debug for non test users
            #if request.user.get_profile().debug is False:
             #   debug = {}

            return render(request, 'itemrtweb/cattest.submit.html', {'question': question, 'topic': topic, 'choice': choice, 'correct': correct, 'debug': debug, 'host': host, 'is_secure': is_secure, 'test':test, 'answered':answered, 'selected_mode':selected_mode})
        else:
            # Option not selected, prompt error
            error['unselected'] = True

    # Format question for web mode
    formatter = formatter_engine.WebQuestionFormatter()
    question = formatter.format(question)
    test = Test.objects.all().get(id=test_id)
    answered = TestResponse.objects.all().filter(test=test).order_by('date')
     # Kill debug for non test users
    ##if request.user.get_profile().debug is False:
      ##  debug = {}

    # Render question page
    return render(request, 'itemrtweb/cattest.question.html', {'question': question, 'topic': topic, 'error': error, 'debug': debug, 'test_id': test.id, 'test':test, 'answered':answered, 'selected_mode':selected_mode})

@login_required
def trialtestutil(request, test_id=None, util_name=None):
    "Util functions for Boombastic function!"

    if test_id:
        test = Test.objects.all().get(id=test_id)
        # Util to return question endtime
        if util_name == 'getendtime':
            # 1 mins from time the question was loaded
            endtime = datetime.strptime(request.session['trialtest_time'], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=1)

            return HttpResponse(endtime.isoformat())
    raise Http404

def trialtesthist(request, test_id):
    #Init System and Mode
    selected_mode = 2
    test = Test.objects.all().get(id=test_id)
    active_engine = Assessment.objects.all().get(name='CAT Test')
    engine = getattr(assessment_engine, active_engine.engine)()
    ability_list = engine.get_user_ability_list(user=request.user, test=test)
    ability = TestResponse.objects.all().filter(test=test).order_by('-date')[0]
    filtered = TestResponse.objects.all().filter(test=test).order_by('date')
    correct = filtered.filter(correctness=1).count()

    return render(request, 'itemrtweb/cattest.history.html', {'test': test,'ability_list': ability_list,'ability':ability,'filtered':filtered,'correct':correct, 'selected_mode':selected_mode })

@login_required
def progress (request):
    #Init mode
    selected_mode = 2
    #CAT TEST
    test_response = None
    test1 = Test.objects.filter(assessment_id=1).filter(user=request.user).order_by('-generated')
    alist={}
    blist={}
    clist={}
    for test in test1:
        test_response = TestResponse.objects.filter(test=test).filter(user=request.user).order_by('-date')
        if test_response.count() > 0:
            alist[test.id]=int(test_response[0].ability)
            blist[test.id]=test_response.count()
            clist[test.id]=test_response[0].criterion
        else:
            alist[test.id] = 0
            blist[test.id] = 0
            clist[test.id] = 0

    #PAPER TEST
    tests = Test.objects.filter(assessment_id=5).filter(user=request.user).order_by('-generated')
    tlist={}
    qlist={}
    plist={}
    wlist={}
    for test in tests:
        test_response = TestResponse.objects.filter(test=test).filter(user=request.user).order_by('-ability')
        if test_response.count() > 0:
            # change this line
            tlist[test.id]= int(test_response[0].ability)
            qlist[test.id]=test_response.count()
            plist[test.id]=round(float(test_response[0].ability) / float( test_response.count()) * 100,2)
        else:
            tlist[test.id]=0
            qlist[test.id]=0
            plist[test.id]=0

        test_question = TestQuestion.objects.filter(test=test)
        test_topic=Topic.objects.none()

        get_topic = None
        related_topic = Topic.objects.none()
        topic_get=[]
        for q in test_question:
            get_topic = Topic.objects.filter(id=q.question.topic.id)
            related_topic = related_topic | get_topic
        for t in related_topic:
            topic_get.append(str(t.name.encode('utf-8')))
        wlist[test.id]=topic_get

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    active_engine = Assessment.objects.all().filter(active=True).get(id=5)
    engine = getattr(assessment_engine, active_engine.engine)()

    topic_ability = {}
    for topic in topics:
        ability = engine.get_user_ability(user=request.user, topic=topic)
        if ability is not None:
            topic_ability[topic] = ability
        else:
            topic_ability[topic] = None

    return render(request, 'itemrtweb/cattest.progress.html', {'tests': tests, 'test_response': test_response,'topic_ability':topic_ability,'topics':topics,
'tlist':tlist,'qlist':qlist,'plist':plist,'alist':alist,'blist':blist,'clist':clist,'test1': test1,'wlist':wlist, 'selected_mode':selected_mode})

@login_required
def question_view(request, id, practiced=False):
    "Lets the user view the question with answers"

    # Question exists?
    question = Question.objects.all().get(id=id)
    if question:
        # Check if user has done question if practiced = true
        if practiced:
            user_practiced = Response.objects.all().filter(user=request.user).filter(question=id)
            if not user_practiced:
                return redirect('/')

        # Load question and render
        # Get correct answer
        question.answer = question.answers.all()[0]

        # Format question for web mode
        formatter = formatter_engine.WebQuestionFormatter()
        question = formatter.format(question)

        # Temp variable to allow ajax through https
        host = request.get_host()
        is_secure = not "localhost" in host

        return render(request, 'itemrtweb/question.view.html', {'question': question, 'topic': question.topic, 'host': host, 'is_secure': is_secure})

    else:
        return redirect('/')

    pass

# additional view to list all possible questions

@user_passes_test(lambda u: u.is_superuser)
def admin(request):
    return render(request, 'itemrtweb/submit.html')

@user_passes_test(lambda u: u.is_superuser)
def system_health_check(request):
    # Check system to ensure only 1 (and not less) assessment per type (practice and test) is active

    # Check system to ensure all assessment engines can be loaded

    pass

@login_required
def debug_changemode(request, mode):
    mode = int(mode)

    if mode == 1:
        # Swap to Random Practice mode
        catengine = Assessment.objects.all().get(name='CAT Practice')
        randomengine = Assessment.objects.all().get(name='Random Practice')

        catengine.active = False
        randomengine.active = True

        catengine.save()
        randomengine.save()
    elif mode == 2:
        # Swap to CAT Practice mode
        catengine = Assessment.objects.all().get(name='CAT Practice')
        randomengine = Assessment.objects.all().get(name='Random Practice')

        catengine.active = True
        randomengine.active = False

        catengine.save()
        randomengine.save()

    return HttpResponseRedirect('/home/')

@login_required
def debug_clearresponses(request):
    # Clears all responses for current user

    request.session['engine_store'] = None

    Response.objects.all().filter(user=request.user).delete()

    return redirect('/practice/')

@user_passes_test(lambda u: u.is_staff)
def control(request):
    "Control Panel Code"
    # Obtain the list of topics
    tests = Test.objects.all()

    testcount = tests.count()

    qf = QuestionFlag.objects.all().count()

    return render_to_response('itemrtweb/control-pageland.html', {'tests': tests, 'testcount': testcount, 'qf':qf}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def control_cattest_settings(request):
    topics = Topic.objects.all().order_by('position')

    return render(request, 'itemrtweb/control-createnewtest.html', {'topics': topics})

@user_passes_test(lambda u: u.is_staff)
def controlnewtest(request):
    "Control Panel Code"
    # Obtain the list of topics
    tests = Test.objects.all()

    return render_to_response('itemrtweb/control-createnewtest.html', {'tests': tests}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def controlnewtest_submit(request):
    "Control Panel Code"
    # Obtain the list of topics
    if request.method == 'POST' and request.POST['newtestNumOfQns']:
        numQns = request.POST['newtestNumOfQns']

        testid = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(6))

        #### VERY IMPORTANT TODO:: CHECK FOR UNIQUE ID
        new_test = Test(id=testid,user=request.user, assessment=Assessment.objects.all().get(name='Generic Test'))
        new_test.save()

        numQns = int(numQns)

        for i in range (0, numQns):
            # Get a random question and add to paper
            question_pool = Question.objects.all().filter(topic=1)
            question_pool = question_pool.exclude(id__in=new_test.questions.all().values_list('id'))

            if question_pool:
                question = question_pool[random.randint(0, question_pool.count()-1)]
                newTestQuestion = TestQuestion(question=question, test=new_test)
                newTestQuestion.save()


    return render_to_response('itemrtweb/control-createnewtest.html', {'testid': testid}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def controlviewpaper(request, testid):
    "Control Panel Code"
    # Obtain the list of topics
    tests = Test.objects.all()

    # Get this test
    thisTest = Test.objects.all().get(id=testid)

    # Home mode
        # Show test responses
        # Open paper for testing
        # Download paper in LaTeX format

    # Question modecontrol_cattest_settingsconcontrol_cattest_settingstrol_cattest_settings
        # Display all questions in test
        # Display dummy modify button
    questions = thisTest.questions.all()

    averagediff = thisTest.questions.all().aggregate(Avg('difficulty')).values()[0]

    # Stats mode
        # Currently not used
        # Paper users, scores, etc

    return render_to_response('itemrtweb/control.html', {'tests': tests, 'testid': testid, 'thistest': thisTest, 'questions': questions, 'avgdiff': averagediff}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def controldownloadpaper(request, testid):
    "Control Panel Code"
    # Obtain the list of topics
    tests = Test.objects.all()

    # Get this test
    thisTest = Test.objects.all().get(id=testid)

    # Home mode
        # Show test responses
        # Open paper for testing
        # Download paper in LaTeX format

    # Question mode
        # Display all questions in test
        # Display dummy modify button
    questions = thisTest.questions.all()

    averagediff = thisTest.questions.all().aggregate(Avg('difficulty')).values()[0]

    # Stats mode
        # Currently not used
        # Paper users, scores, etc

    return render_to_response('itemrtweb/download.tex', {'tests': tests, 'testid': testid, 'thistest': thisTest, 'questions': questions, 'avgdiff': averagediff}, context_instance=RequestContext(request))

@csrf_exempt
def postdata(request):
    if request.method == 'POST':

        # loop through keys and values
        for key, value in request.POST.iteritems():
            pass

        return render_to_response('postdata.html', {'postdata': request.POST}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def prototype(request, question_id=None):
    # Init
    selected_question = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if question_id:
        selected_question = Question.objects.all().get(id=int(question_id))

    if request.method == 'POST':
        form = forms.InsertEditQuestionForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Check if question exists or need to create new
            if selected_question:
                # Edit existing question
                selected_question.content=form.cleaned_data['content']
                selected_question.choice=form.cleaned_data['choice']
                selected_question.source=form.cleaned_data['source']
                selected_question.difficulty=form.cleaned_data['difficulty']
                selected_question.topic=form.cleaned_data['topic']
                selected_question.save()

                #answer = selected_question.answers.all()[0]
                #answer.content = form.cleaned_data['answer']
                #answer.save()

                # Insert solution if exists
                if form.cleaned_data['solution']:
                    # Check if solution exists
                    solution_exists = Solution.objects.all().filter(question=selected_question).count()

                    if solution_exists > 0:
                        # Update solution
                        solution = selected_question.solution
                        solution.content = form.cleaned_data['solution']
                        solution.save()
                    else:
                        # New solution for this question
                        solution = Solution(question=selected_question, content=form.cleaned_data['solution'])
                        solution.save()

                # Tag adding/deleting
                selected_question.tags.clear()
                for tag_name in form.cleaned_data['tags']:
                    # Check tag exists in db, otherwise add
                    # Currently no need since automatically verified
                    tag = Tag.objects.all().get(name=tag_name)

                    qn_tag = QuestionTag(question=selected_question, tag=tag)
                    qn_tag.save()

                return redirect('/question/list/topic/'+ str(selected_question.topic.id) +'/?msg=Question '+ str(selected_question.id) +' edited successfully#question-'+ str(selected_question.id))
            else:
                # Insert new question
                question = Question(content=form.cleaned_data['content'], choice=form.cleaned_data['choice'], source=form.cleaned_data['source'],difficulty=form.cleaned_data['difficulty'], topic=form.cleaned_data['topic'])
                question.save()

                # Insert answer for question
                answer = Answer(question=question, content=form.cleaned_data['answer'])
                answer.save()

                # Insert solution if exists
                if form.cleaned_data['solution']:
                    solution = Solution(question=question, content=form.cleaned_data['solution'])
                    solution.save()

                for tag_name in form.cleaned_data['tags']:
                    # Check tag exists in db, otherwise add
                    # Currently no need since automatically verified
                    tag = Tag.objects.all().get(name=tag_name)

                    qn_tag = QuestionTag(question=question, tag=tag)
                    qn_tag.save()

                # Question inserted successfully!
                return redirect('/question/list/topic/'+ str(question.topic.id) +'/?msg=Question '+ str(question.id) +' added successfully#question-'+ str(question.id))

        # Reply regardless valid
        return render(request, 'itemrtweb/manage.question.form.html', {'form': form, 'topics': topics, 'selected_question': selected_question})
    else:
        # Check if question exists or give blank form
        if selected_question:
            # Load existing question into a form
            form = forms.InsertEditQuestionForm(initial={'content':selected_question.content, 'choice':selected_question.choice, 'source':selected_question.source,'difficulty':selected_question.difficulty, 'topic':selected_question.topic, 'answer':selected_question.answers.all()[0].content, 'tags': selected_question.tags.all().values_list('name', flat=True)})

            solution_exists = Solution.objects.all().filter(question=selected_question).count()

            if solution_exists > 0:
                form.fields["solution"].initial = selected_question.solution.content
        else:
            # Display new form for user to fill in
            form = forms.InsertEditQuestionForm()

    return render(request, 'itemrtweb/manage.question.form.html', {'form': form, 'topics': topics,  'selected_question': selected_question})

@user_passes_test(lambda u: u.is_staff)
def prototype3(request, question_id=None):
    # Init
    selected_question = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if question_id:
        selected_question = Question.objects.all().get(id=int(question_id))

    # Check if question exists otherwise redirect to question list
    if selected_question:
        # Hide question and save. Then give message to user
        selected_question.is_active = False
        selected_question.save()

        return redirect('/question/?msg=Question has been deleted')
    else:
        # Redirect user back to question lists
        return redirect('/question/')

@user_passes_test(lambda u: u.is_staff)
def prototype2(request, topic_id=None):
    # Record usage for stats purpose
    page = "question_management"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Init
    filtered_questions = None
    filtered_tags = None
    selected_topic = None
    count={}

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    for topic in topics:
        topicQcount = Question.objects.all().filter(topic=topic).count()
        count[topic]=topicQcount
    all_tags = Tag.objects.all()

    # int the selected topic
    if topic_id:
        selected_topic = Topic.objects.all().get(id=int(topic_id))

    if topic_id:
        # Retrieve questions for this topic
        filtered_questions = Question.objects.all().filter(topic=topic_id)
        filtered_tags = Tag.objects.filter(topic=topic_id)

        # Filter for difficulty if specified
        if request.GET.__contains__('difficulty'):
            difficulty = request.GET.get('difficulty')

            # Only filter if input is an int!
            try:
                difficulty = int(difficulty)
                filtered_questions = filtered_questions.filter(difficulty=difficulty)
            except exceptions.ValueError:
                pass

    return render(request, 'itemrtweb/manage.question.list.html', {'count':count, 'topics': topics, 'selected_topic': selected_topic, 'questions': filtered_questions, 'all_tags': all_tags,'filtered_tags':filtered_tags})
@user_passes_test(lambda u: u.is_staff)
def prototype2a(request):
    # Init
    filtered_questions = Question.objects.all()

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    all_tags = Tag.objects.all()

    # Filter by tags given from input
    tags = request.GET.getlist("tags")

    count={}
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    for topic in topics:
        topicQcount = Question.objects.all().filter(topic=topic).count()
        count[topic]=topicQcount




    ##print >> sys.stderr, tags

    if tags:
        for tag in tags:
            print >> sys.stderr, tag
            filtered_questions = filtered_questions.filter(tags__name=tag)
    else:
        filtered_questions = None

    return render(request, 'itemrtweb/manage.question.list.html', {'count':count, 'topics': topics, 'questions': filtered_questions, 'tags': tags, 'all_tags': all_tags})

@user_passes_test(lambda u: u.is_staff)
def preview(request, question_id=None):
    # Init
    selected_question = None

    # Objectify the selected question
    if question_id:
        selected_question = Question.objects.all().get(id=int(question_id))
        # Get correct answer
        selected_question.answer = selected_question.answers.all()[0]
        try:
            selected_question.dconcept = QuestionConcept.objects.all().filter(question=question_id).order_by('id').first()
        except QuestionConcept.DoesNotExist:
            selected_question.dconcept = None
        try:
            selected_question.history = Response.objects.all().filter(assessment_id=5).filter(question_id=question_id).filter(user=request.user).order_by('date')
        except QuestionConcept.DoesNotExist:
            selected_question.history = None

    count = selected_question.history.count()
    all_question_attempt = Response.objects.all().filter(assessment_id=5).filter(question_id=question_id).order_by('date').count()
    correct_question_attempt = Response.objects.all().filter(assessment_id=5).filter(question_id=question_id).filter(correctness=1).order_by('date').count()

    # Check if question exists otherwise redirect to question list
    if selected_question:
        return render(request, 'itemrtweb/manage.question.preview.html', {'question': selected_question, 'count':count, 'correct_question_attempt':correct_question_attempt, 'all_question_attempt':all_question_attempt})
    else:
        # 404 if question was not found
        raise Http404

@user_passes_test(lambda u: u.is_staff)
def testquestion(request, question_id=None):

    if question_id is not None:
        # Get question (or nothing) from orm
        question = Question.objects.all().get(id=question_id)

        if 'answer' in request.POST and request.POST['answer']:
            response = request.POST['answer']
            response = response.replace(' ', '').replace('\\n', '').replace('\\r', '').replace('\\t', '')

            # Get actual answer in string
            answer_text = question.choices[question.answers.all()[0].content.lower()]
            answer_text = answer_text.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

            ##print sys.stderr, answer_text

            if re.match('^'+answer_text+'$', response):
                return HttpResponse("Answer is Correct")
            else:
                return HttpResponse("Answer do not Match\nInput: "+ response+ "\nActual: "+ answer_text)
        # Otherwise no answer just return nothing happened!
        else:
            return HttpResponse("Empty Field!")
    raise Http404

@login_required
def flag_question(request, question_id):
    "View to allow users to flag/report a problem with the question"

    if request.method == 'POST':
        form = forms.FlagQuestionForm(request.POST)
        if form.is_valid():
            # Get the question from orm
            question = Question.objects.get(id=question_id)

            # Flag question now!
            flag = QuestionFlag(question=question, user=request.user, issue=form.cleaned_data['issue'])
            flag.save()

            return render(request, 'itemrtweb/question.flag.html', {'form': form, 'submitted': True})
    else:
        # Display new form for user to fill in
        form = forms.FlagQuestionForm()

    return render(request, 'itemrtweb/question.flag.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def flag_display(request):
    flagged_qns = QuestionFlag.objects.all()
    qf = flagged_qns.count()

    return render(request, 'itemrtweb/control.flaggedquestions.html', {'flagged_qns': flagged_qns, 'qf':qf})

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
posidf = loadtxttoarray('gaokaoposidf.txt')
myposlist = loadtxttolist('gaokaomyposlist.txt')
depidf1 = loadtxttoarray('gaokaodepidf1.txt')
mydependencylist1 = loadtxttolist('gaokaomydependencylist1.txt')
depidf2 = loadtxttoarray('gaokaodepidf2.txt')
mydependencylist2 = loadtxttolist('gaokaomydependencylist2.txt')
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
##def user_search(request):
##    "Home view to display practice or trial testing modes"
##    selected_mode=2
##    all_tags = Tag.objects.all()
##    return render(request, 'itemrtweb/user_search.html', {'all_tags': all_tags,'selected_mode':selected_mode})
##@login_required
##def adaptivesearch (request):
##    selected_mode=2
##    topics = Topic.objects.all().order_by("id")
##    # Init
##    selected_topic = None
##    topic_id = 0
##    topic_count = {}
##    filtered_questions = Question.objects.all()
##    count = None
##    tags = request.GET.getlist("tags")
##    choiceA = request.GET.getlist("choiceA")
##    choiceB = request.GET.getlist("choiceB")
##    choiceC = request.GET.getlist("choiceC")
##    choiceD = request.GET.getlist("choiceD")
##    correctAnswer = request.GET.getlist("correctAnswer")
##    tags = str(tags)
##    correctAnswer = str(correctAnswer)
##    tags=tags.lower()
##    tags=tags[3:len(tags)-2]
##    ques = str(tags)
##    choices = []
##    if choiceA:
##        choiceA = str(choiceA)
##        choiceA=choiceA.lower()
##        choiceA=choiceA[3:len(choiceA)-2]
##        choiceA = str(choiceA)
##        if choiceA:
##            choices.append(choiceA)
##    if choiceB:
##        choiceB = str(choiceB)
##        choiceB=choiceB.lower()
##        choiceB=choiceB[3:len(choiceB)-2]
##        choiceB = str(choiceB)
##        if choiceB:
##            choices.append(choiceB)
##    if choiceC:
##        choiceC = str(choiceC)
##        choiceC=choiceC.lower()
##        choiceC = choiceC.split("'")[1]
##        #choiceC=choiceC[3:len(choiceC)-2]
##        choiceC = str(choiceC)
##        if choiceC:
##            choices.append(choiceC)
##    if choiceD:
##        choiceD = str(choiceD)
##        choiceD=choiceD.lower()
##        choiceD=choiceD[3:len(choiceD)-2]
##        choiceD = str(choiceD)
##        if choiceD:
##            choices.append(choiceD)
##    content = nltk.sent_tokenize(ques)
##    correctAnswer=correctAnswer.lower()
##    correctAnswer=correctAnswer[3:len(correctAnswer)-2]
##    correctAnswer = str(correctAnswer)
##
##    tokens = nltk.word_tokenize(ques)
##    length = len(tokens)
##    tagged = nltk.pos_tag(tokens)
##    key = ' '.join([tup[1] for tup in tagged])
##    print ques
##    print tokens
##
##    if tags:
##        if '*' in ques:
##            if len(choices)>0:
##                filtered_questions = patternsearch(ques, correctAnswer, choices)
##            else:
##                filtered_questions = Question.objects.all().filter(Q(choiceparse__icontains=key)|Q(content__icontains=tags)).order_by('id')
##        else:
##            filtered_questions = texttagsearch(ques)
##        #filtered_questions = Question.objects.all().filter(Q(choiceparse__icontains=key)|Q(content__icontains=tags)).order_by('id')
##
##        count = filtered_questions.count()
##        if request.GET.get("topic") != None:
##            topic_id = int(request.GET.get("topic"))
##        # Obtain counts of questions per topic
##        for topic in topics:
##            topicQcount = filtered_questions.filter(topic=topic).count()
##            topic_count[topic]=topicQcount
##
##        if topic_id > 0:
##            sel = filtered_questions.filter(topic__id=topic_id).order_by('-result')
##            selected_topic = Topic.objects.get(id=topic_id)
##        else: #all topics
##    		sel = filtered_questions
##        paginator = Paginator(sel, 10)
##
##        page = request.GET.get('page')
##
##        try:
##            questions = paginator.page(page)
##        except PageNotAnInteger:
##            questions = paginator.page(1)
##        except EmptyPage:
##            questions = paginator.page(paginator.num_pages)
##
##    else:
##        questions = None
##
##        # Remove page number from querystring
##    q = request.GET
##    z = q.copy()
##    try:
##        del z['page']
##    except KeyError:
##        pass
##    querystring = '?' + z.urlencode()
##
##    return render(request, 'itemrtweb/search.pattern.html', { 'selected_mode':selected_mode,'choices':choices, 'tags':tags, 'key':key, 'questions': questions, 'filtered_questions' : filtered_questions,'querystring': querystring, 'count':count, 'topic_count':topic_count, 'selected_topic':selected_topic, 'topics':topics, 'choiceA':choiceA, 'choiceB':choiceB, 'choiceC':choiceC, 'choiceD':choiceD})


@login_required
def learn_home(request):

    "Home view to display topics to choose from for practice"
    # Record usage for stats purpose
    page = "learn"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    #Learn
    learnusage_all = LearnUsage.objects.filter(user=request.user)
    learn_progress = {}
    for topic in topics:
        is_done = learnusage_all.filter(learn__id=topic.id).count()
        learn_progress[topic] = is_done

    return render(request, 'itemrtweb/learn.home.html', {'topics': topics, 'learn_progress': learn_progress})

@login_required
def learn_topic(request, cid):

    # Record usage for stats purpose
    topic = cid
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'learn_usage_'+topic not in request.session or datetime.now() > datetime.strptime(request.session['learn_usage_'+topic], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        learn_topic = Learn.objects.get(topic__id=int(topic))
        usage = LearnUsage(user=request.user, learn=learn_topic)
        usage.save()
        request.session['learn_usage_'+topic] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    active_engine = Assessment.objects.all().filter(active=True).get(type=Assessment.PRACTICE)
    engine = getattr(assessment_engine, active_engine.engine)()

    selected_topic = None

    # int the selected topic
    if cid:
        selected_topic = Topic.objects.all().get(id=cid)

    param = {}
    chapters = list(Learn.objects.all().order_by('id').values())
    param['chapters'] = chapters
    sel = Learn.objects.get(topic__id=int(cid))

    learnusage_all = LearnUsage.objects.filter(user=request.user)
    learn_progress = {}
    for topic in topics:
        is_done = learnusage_all.filter(learn__id=topic.id).count()
        learn_progress[topic] = is_done

    # Render question page
    return render(request, 'itemrtweb/learn.topic.html', {'topics': topics,'cid': cid, 'sel':sel, 'selected_topic':selected_topic, 'learn_progress':learn_progress})

@login_required
def learn_topicconcept(request, cid):

    # Record usage for stats purpose
    topic = cid
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'learn_usage_'+topic not in request.session or datetime.now() > datetime.strptime(request.session['learn_usage_'+topic], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        learn_topic = Learn.objects.get(topic__id=int(topic))
        usage = LearnUsage(user=request.user, learn=learn_topic)
        usage.save()
        request.session['learn_usage_'+topic] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    selected_topic = None

    # int the selected topic
    if cid:
        selected_topic = Topic.objects.all().get(id=cid)
        tag= Tag.objects.filter(topic__id=cid)
        concept= Concept.objects.filter(topic__id=cid)

    param = {}
    chapters = list(Topic.objects.all().order_by('position').values())
    param['chapters'] = chapters
    sel = Tag.objects.filter(topic__id=int(cid))

    learnusage_all = LearnUsage.objects.filter(user=request.user)
    learn_progress = {}
    for topic in topics:
        is_done = learnusage_all.filter(learn__id=topic.id).count()
        learn_progress[topic] = is_done

    # Render question page
    return render(request, 'itemrtweb/concept.topic.html', {'topics': topics,'cid': cid, 'tag':tag, 'concept':concept, 'sel':sel, 'selected_topic':selected_topic, 'learn_progress':learn_progress})


# English Admin

def process_parse(q):
    token = q['content'].split(';')
    ans = q['std_answer'].strip()
    display = []
    item= []
    #for each question part
    for t in token:
        c = t.strip().count("*")
        if c == 2:
            ans = ans.split('...')
            item = t.strip().replace("*", ans[0],1)
            item= item.replace("*", ans[1],1)
        else:
            item = t.strip().replace("*", ans)
        display.append(item)
        item = []
    return display

#process difficulty level
def process_diff(q):

    from nltk.tokenize import RegexpTokenizer

    TOKENIZER = RegexpTokenizer('(?u)\W+|\$[\d\.]+|\S+')
    SPECIAL_CHARS = ['.', ',', '!', '?']

    def get_char_count(words):
        characters = 0
        for word in words:
            characters += len(word.decode("utf-8"))
        return characters

    def get_words(text=''):
        words = []
        words = TOKENIZER.tokenize(text)
        filtered_words = []
        for word in words:
            if word in SPECIAL_CHARS or word == " ":
                pass
            else:
                new_word = word.replace(",","").replace(".","")
                new_word = new_word.replace("!","").replace("?","")
                filtered_words.append(new_word)
        return filtered_words

    def get_sentences(text=''):
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        sentences = tokenizer.tokenize(text)
        return sentences

    specialSyllables_en = """
    ok 2
    tv 2
    cd 2
    steely 2
    file 1
    hole 1
    mile 1
    pale 1
    pile 1
    pole 1
    role 1
    rule 1
    scale 1
    smile 1
    sole 1
    stale 1
    style 1
    tale 1
    vile 1
    while 1
    whole 1
    acre 2
    beauty 2
    being 2
    bureau 2
    business 2
    buyer 2
    carriage 2
    centre 2
    colleague 2
    colonel 2
    compile 2
    create 2
    cruel 2
    diet 2
    evening 2
    female 2
    fibre 2
    fluid 2
    framework 2
    going 2
    guideline 2
    household 2
    hundred 2
    judgement 2
    layer 2
    lifetime 2
    lion 2
    marriage 2
    mayor 2
    metre 2
    missile 2
    module 2
    movement 2
    pavement 2
    player 2
    poem 2
    prayer 2
    profile 2
    ratio 2
    rely 2
    safety 2
    schedule 2
    science 2
    spokesman 2
    squeaky 2
    statement 2
    technique 2
    achievement 3
    announcement 3
    area 3
    arrangement 3
    awareness 3
    barrier 3
    behaviour 3
    businessman 3
    carrier 3
    casual 3
    catalogue 3
    champion 3
    coincide 3
    creation 3
    criticism 3
    dialogue 3
    employee 3
    employer 3
    engagement 3
    equation 3
    excitement 3
    graduate 3
    idea 3
    improvement 3
    influence 3
    involvement 3
    loyalty 3
    management 3
    measurement 3
    mechanism 3
    molecule 3
    musician 3
    organism 3
    parliament 3
    poetry 3
    policeman 3
    reaction 3
    realise 3
    realize 3
    reassure 3
    recipe 3
    reinforce 3
    replacement 3
    requirement 3
    retirement 3
    shareholder 3
    situate 3
    suicide 3
    supplier 3
    theatre 3
    theory 3
    united 3
    video 3
    advertisement 4
    anxiety 4
    capitalism 4
    casualty 4
    championship 4
    constituent 4
    criterion 4
    evaluate 4
    experience 4
    hierarchy 4
    initiate 4
    negotiate 4
    politician 4
    reality 4
    situation 4
    society 4
    differentiate 5
    evaluation 5
    ideology 5
    individual 5
    initiation 5
    negotiation 5
    cheque 1
    quaint 1
    queen 1
    queer 1
    squeeze 1
    tongue 1
    mimes 1
    ms 1
    h'm 1
    brutes 1
    lb 1
    effaces 2
    mr 2
    mrs 2
    moustaches 2
    dr 2
    sr 2
    jr 2
    mangroves 2
    truckle 2
    fringed 2
    messieurs 2
    poleman 2
    sombre 2
    sidespring 2
    gravesend 2
    60 2
    greyish 2
    anyone 3
    amusement 3
    shamefully 3
    sepulchre 3
    hemispheres 3
    veriest 3
    satiated 4
    sailmaker 4
    etc 4
    unostentatious 5
    Propitiatory 6
    """
    fallback_cache = {}

    fallback_subsyl = ["cial", "tia", "cius", "cious", "giu", "ion", "iou",
                       "sia$", ".ely$"]

    fallback_addsyl = ["ia", "riet", "dien", "iu", "io", "ii",
                       "[aeiouym]bl$", "mbl$",
                       "[aeiou]{3}",
                       "^mc", "ism$",
                       "(.)(?!\\1)([^aeiouy])\\ll$",
                       "[^l]lien",
                       "^coad.", "^coag.", "^coal.", "^coax.",
                       "(.)(?!\\1)[gq]ua(.)(?!\\2)[aeiou]",
                       "dnt$"]


    # Compile our regular expressions
    for i in range(len(fallback_subsyl)):
        fallback_subsyl[i] = re.compile(fallback_subsyl[i])
    for i in range(len(fallback_addsyl)):
        fallback_addsyl[i] = re.compile(fallback_addsyl[i])

    def _normalize_word(word):
        return word.strip().lower()

    # Read our syllable override file and stash that info in the cache
    for line in specialSyllables_en.splitlines():
        line = line.strip()
        if line:
            toks = line.split()
            assert len(toks) == 2
            fallback_cache[_normalize_word(toks[0])] = int(toks[1])

    def count(word):
        word = _normalize_word(word)
        if not word:
            return 0

        # Check for a cached syllable count
        count = fallback_cache.get(word, -1)
        if count > 0:
            return count

        # Remove final silent 'e'
        if word[-2:] == "le":
            word = word+"s" #-le

        elif word[-2:] == "ed":
            word = word[:-2] #problematic -ed

        elif word[-1] == "e":
            word = word[:-1]


        # Count vowel groups
        count = 0
        prev_was_vowel = 0
        for c in word:
            is_vowel = c in ("a", "e", "i", "o", "u", "y")
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Add & subtract syllables
        for r in fallback_addsyl:
            if r.search(word):
                count += 1
        for r in fallback_subsyl:
            if r.search(word):
                count -= 1

        #for words with silent e +1 e.g. me, she, he, the
        if count == 0:
            count = 1

        # Cache the syllable count
        fallback_cache[word] = count

        return count

    def count_syllables(words):
        syllableCount = 0
        for word in words:
            syllableCount += count(word)
        return syllableCount

    def count_complex_words(text=''):
        words = get_words(text)
        sentences = get_sentences(text)
        complex_words = 0
        found = False
        cur_word = []

        for word in words:
            cur_word.append(word)
            if count_syllables(cur_word)>= 3:

                #Checking proper nouns. If a word starts with a capital letter
                #and is NOT at the beginning of a sentence we don't add it
                #as a complex word.
                if not(word[0].isupper()):
                    complex_words += 1
                else:
                    for sentence in sentences:
                        if str(sentence).startswith(word):
                            found = True
                            break
                    if found:
                        complex_words += 1
                        found = False

            cur_word.remove(word)
        return complex_words


    class Readability:
        analyzedVars = {}

        def __init__(self, text):
            self.analyze_text(text)

        def analyze_text(self, text):
            words = get_words(text)
            char_count = get_char_count(words)
            word_count = len(words)
            sentence_count = len(get_sentences(text))
            syllable_count = count_syllables(words)
            complexwords_count = count_complex_words(text)
            avg_words_p_sentence = word_count/sentence_count

            self.analyzedVars = {
                'words': words,
                'char_cnt': float(char_count),
                'word_cnt': float(word_count),
                'sentence_cnt': float(sentence_count),
                'syllable_cnt': float(syllable_count),
                'complex_word_cnt': float(complexwords_count),
                'avg_words_p_sentence': float(avg_words_p_sentence)
            }

##        def FleschReadingEase(self):
##            score = 0.0
##            score = 206.835 - (1.015 * (self.analyzedVars['avg_words_p_sentence'])) - (84.6 * (self.analyzedVars['syllable_cnt']/ self.analyzedVars['word_cnt']))
##            return round(score, 4)
        def FleschKincaidGradeLevel(self):
            score = 0.39 * (self.analyzedVars['avg_words_p_sentence']) + 11.8 * (self.analyzedVars['syllable_cnt']/ self.analyzedVars['word_cnt']) - 15.59
            return round(score, 4)

    param = {}
    q = q[0]
    text = q
    rd = Readability(str(text))
    grade = rd.FleschKincaidGradeLevel()

    sent = tokenize.word_tokenize(text)
    sentence = tag.pos_tag(sent)
    grammar1 = r"""
    NP: {<.*>*}             # start by chunking everything
        }<[\.VI].*>+{       # chink any verbs, prepositions or periods
        <.*>}{<DT>          # separate on determiners
    PP: {<IN><NP>}          # PP = preposition + noun phrase
    VP: {<VB.*><NP|PP>*}    # VP = verb words + NPs and PPs
    """
    grammar2 = r"""
      NP: {<DT|JJ|NN.*>+}          # Chunk sequences of DT, JJ, NN
      PP: {<IN><NP>}               # Chunk prepositions followed by NP
      VP: {<VB.*><NP|PP|CLAUSE>+$} # Chunk verbs and their arguments
      CLAUSE: {<NP><VP>}           # Chunk NP, VP
      """
    grammar3 = r"""
    NP:                   # NP stage
      {<DT>?<JJ>*<NN>}    # chunk determiners, adjectives and nouns
      {<NNP>+}            # chunk proper nouns
    """
    cp1 = nltk.RegexpParser(grammar1)
    cp2 = nltk.RegexpParser(grammar2)
    cp3 = nltk.RegexpParser(grammar3)
    result1 = cp1.parse(sentence)
    result2 = cp2.parse(sentence)
    result3 = cp3.parse(sentence)
    ht1 =  result1.height()
    ht2 =  result2.height()
    ht3 =  result3.height()
    grade = grade + ht1 + ht2 + ht3
    if grade <= 14:
        diff_lvl=1
    elif grade <= 16:
        diff_lvl=2
    elif grade <= 18:
        diff_lvl=3
    elif grade <= 20:
        diff_lvl=4
    else:
        diff_lvl=5
    return diff_lvl

#regenerate keywords
@user_passes_test(lambda u: u.is_staff)
def eng_Admin_RegenKeyword(request):
    param = {}
    topics = Topic.objects.all()

    #delete old keywords relationships
    oldkeywordtags = QuestionTag.objects.all()
    oldkeywordtags.delete()

    for topic in topics:
        keywords = Tag.objects.filter(topic=topic)

        for keyword in keywords:
            keywordfound = Question.objects.filter(topic=topic).filter(Q(std_answer__iregex='[[:<:]]' + keyword.name + '[[:>:]]'))  #search for keyword in standard answer only
            for kf in keywordfound:
                #create new tag relationship
                newtag = QuestionTag(question=kf, tag=keyword)
                newtag.save()

    return render(request, 'itemrtweb/eng_admin_taglist.html', {} )
    ##return render_to_response('itemrtweb/eng_admin_taglist.html', param, RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def eng_Admin_RegenDiff(request):
    c = 0
    param = {}
    sel = Question.objects.all().order_by('id').values()
    for q in sel:
        q_id = q['id']
        q_content = q['content']
        q_item = Question.objects.get(id=q_id)
        a = process_parse(q)
        b = process_diff(a)

        q_item.difficulty = b
        q_item.save()

    return render(request, 'itemrtweb/eng_admin_diff.html', {} )
    ##return render_to_response('itemrtweb/eng_admin_diff.html', param, RequestContext(request))
def eng_Admin_RegenConcept(request):
    param = {}
    topics = Topic.objects.all()

    #delete old keywords relationships
    oldconcepts = QuestionConcept.objects.all()
    oldconcepts.delete()

    for topic in topics:
        concepts = Concept.objects.filter(topic=topic)

        for concept in concepts:
            tags = concept.words.all()
            if len(tags)>1:
                conceptfound = Question.objects.filter(topic=topic).filter(reduce(lambda x, y: x | y, [Q(std_answer__iregex='[[:<:]]' + tag.name + '[[:>:]]') for tag in tags]))
            else:
                for tag in tags:
                    conceptfound = Question.objects.filter(topic=topic).filter(Q(std_answer__iregex='[[:<:]]' + tag.name + '[[:>:]]'))
            if (concept.id == 20 or concept.id ==60):
                print conceptfound
            if len(tags)>0:
                for kf in conceptfound:
                    #create new tag relationship
                    newconcept = QuestionConcept(question=kf, concept=concept)
                    newconcept.save()
    return render(request, 'itemrtweb/eng_admin_conceptlist.html', {} )

@user_passes_test(lambda u: u.is_staff)
def eng_Admin_RegenParse(request):
    c = 0
    param = {}
    sel = Question.objects.all().order_by('id').values()
    for q in sel:
        q_id = q['id']
        q_content = q['content']
        q_ans = q['choice']

        q_item = Question.objects.get(id=q_id)
        ques = str(q_content.lower())
        ans = str(q_ans.lower())
        tokens = nltk.word_tokenize(ques)
        tokenans = nltk.word_tokenize(ans)

        length = len(tokens)
        pos = -1
        for i in range(0,length-1):
            if tokens[i] == "*":
                pos = i
        tokens.pop(pos)
        for x in reversed(tokenans): tokens.insert(pos,x)

        default_tagger = nltk.data.load(nltk.tag._POS_TAGGER)
        model = {'more':'ADV','yesterday':'ADV','the':'DD','a':'DD','an':'DD','so':'CC','yet':'CC', 'apart':'CC','nevertheless':'CC','lest':'CC',
                'unless':'CC','despite':'CC','although':'CC','besides':'CC','since':'CC','than':'CC','until':'CC','except':'CC','though':'CC',
                'many':'DT','much':'DT','most':'DT','few':'DT','fewer':'DT','other':'DT','little':'DT','none':'DT','less':'DT','everyone':'DT','anything':'DT',
                'out':'IN','up':'IN','down':'IN','off':'IN','whose':'WH','how':'WH','mine':'PRP','ourselves':'PRP','themselves':'PRP','is':'SVA','are':'SVA','was':'SVA','were':'SVA','am':'SVA','has':'SVA','have':'SVA','had':'SVA','does':'SVA'}
        tagger = nltk.tag.UnigramTagger(model=model, backoff=default_tagger)
        tagged = tagger.tag(tokens) ##nltk.pos_tag(tokens)
        simplified = [(word, simplify_brown_tag(tag)) for word, tag in tagged] ##added in

        puretagged = nltk.pos_tag(tokens)
        key = ' '.join([tup[1] for tup in puretagged]) ##replaced tagged with simplified
        parse = ''
        for x in range (len(tokenans)):
            parse += simplified[pos+x][1] + ' ' ##replaced tagged with simplified

        min = pos-3
        max = pos + 3
        if min < 0 : min = 0
        if max > len(tokens): max = len(tokens)
        parsechoice = ''
        for x in range(min,max):
            parsechoice += puretagged[x][1] + ' '

        q_item.wholeparse = key
        q_item.parse = parse
        q_item.choiceparse = parsechoice
        q_item.save()

    return render(request, 'itemrtweb/eng_admin_parse.html', {} )
    ##return render_to_response('itemrtweb/eng_admin_parse.html', param, RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def eng_Admin_RegenTopic(request):
    param = {}
    sel = Question.objects.all().order_by('id').values()
    topic = -1
    for q in sel:

        q_id = q['id']
        q_content = q['content']
        q_wholeparse = q['wholeparse']
        q_parse = q['parse']
        q_item = Question.objects.get(id=q_id)
        ques = str(q_content)
        whole = str(q_wholeparse)
        parse = str(q_parse)

        # Filter from higher prob to lower prob
        if parse[0:2] == "WH":topic = 10
        elif parse[0:5] == "MOD ":topic = 7
        elif parse[0:3] == "Q ": topic = 5
        elif parse[0:4] == "DD Q":topic = 5
        elif ques.find("?") != -1:
            if whole.find("RB PRP .")!= -1: topic=11
            elif whole.find("VBZ PRP")!= -1: topic = 11
            elif whole.find("VBP PRP")!= -1: topic = 11
        elif parse[0:5] == "SVA ": topic = 3
        elif parse[0:5] == "PRO ": topic = 2
        elif parse[0:3] == "P ": topic = 8
        elif parse[0:2] == "DD":topic = 1
        elif parse[0:5] == "CNJ ":topic = 9
        elif parse[0:5] == "ADV ":topic = 6
        elif parse.find("P N P")!= -1: topic = 9
        elif parse.find("ADJ")!= -1: topic = 5
        elif parse.find("MOD")!= -1: topic = 7
        elif parse.find(" P ")!= -1: topic = 8
        else: topic=4
        q_item.new_topic = topic
        q_item.save()

    ##return render_to_response('itemrtweb/eng_admin_topic.html', param, RequestContext(request))
    return render(request, 'itemrtweb/eng_admin_topic.html', {} )

@user_passes_test(lambda u: u.is_staff)
def eng_Admin_RegenTopicdone(request):
    param = {}
    sel_question = Question.objects.all()
    topics = Topic.objects.all().order_by("id")
    alist = {}
    tlist = {}
    tplist={}
    flist= {}
    fplist={}
    for topic in topics:
        alist[topic.id] = Question.objects.filter(topic=topic).count()
        tlist[topic.id] = Question.objects.filter(topic=topic).filter(new_topic=topic.id).count()
        if alist[topic.id] > 0:
            tplist[topic.id] = round((float(tlist[topic.id])/float(alist[topic.id])),4)*100
            flist[topic.id] = alist[topic.id]-tlist[topic.id]
            fplist[topic.id] = round((float(flist[topic.id])/float(alist[topic.id])),4)*100
        else:
            tplist[topic.id]=0
            flist[topic.id] = alist[topic.id]-tlist[topic.id]
            fplist[topic.id]=0
    alist["all"]=Question.objects.all().count()
    a= 0
    for topic in topics:
        a += Question.objects.filter(topic=topic).filter(new_topic=topic.id).count()
    tlist["all"]=a
    tplist["all"] = round((float(tlist["all"])/float(alist["all"])),4)*100
    flist["all"] = alist["all"]-tlist["all"]
    fplist["all"] = round((float(flist["all"])/float(alist["all"])),4)*100

    return render(request, 'itemrtweb/eng_admin_topic_done.html', {'topics':topics,'alist':alist,'tlist':tlist,'flist':flist,'tplist':tplist,'fplist':fplist})


@login_required
def browsediff(request, diff=None):
    # Init
    filtered_questions = Question.objects.all()

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

     # Obtain counts of questions per diff
    topic_count = {}
    for topic in topics:
        topicQcount = Question.objects.filter(topic=topic).count()
        topic_count[topic]=topicQcount

    selected_topic = None

    if diff:
        # Retrieve questions for this topic
        filtered_questions = Question.objects.all().filter(difficulty=diff)
        selected_topic = Topic.objects.all().get()

        count = filtered_questions.count()

        ##selected_topic = Topic.objects.all().get(id=topic_id)

        paginator = Paginator(filtered_questions, 10)

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

    return render(request, 'itemrtweb/browse.html', {'topics': topics, 'questions': questions, 'filtered_questions' : filtered_questions,'querystring': querystring, 'selected_topic':selected_topic, 'topic_count':topic_count, 'count':count})
'''
@login_required ##@user_passes_test(lambda u: u.is_staff)
def insertQ(request, question_id=None):
    # Init
    selected_question = None
    all_question = Question.objects.all()
    countQ=0
    qid=[]
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    if request.method == 'POST':
        form = forms.NewQuestion(request.POST) # Bind to user submitted form

        if form.is_valid():
            # INITIALISE - Get from POST
            content=form.cleaned_data['content']
            newqns = str(content)
            # Check if question exists
            s2 = str(content.lower())

            for qns in all_question:
                s1 = str(qns.content.lower())
                if s1 == s2:
                    qid.append(qns)

            # Let User see these qns
            if len(qid)>0:
                countQ = len(qid)
                return render(request, 'itemrtweb/manage.question.new.html', {'form': form,  'selected_question': qid, 'countQ':countQ})

            else:
                return prototypeauto(request, newqns)
                #form = forms.InsertQuestionForm()
                #continue insert qns
                #return render(request, 'itemrtweb/manage.question.insert.html', {'form': form,'content': newqns})

##        # Reply regardless valid
##        return render(request, 'itemrtweb/manage.question.new.html', {'form': form, 'selected_question': selected_question})
    else:
        # Display new form for user to fill in
        form = forms.NewQuestion()

    return render(request, 'itemrtweb/manage.question.new.html', {'form': form, 'selected_question': selected_question, 'countQ':countQ})
'''
@login_required ##@user_passes_test(lambda u: u.is_staff)
def prototypeauto(request, question_id=None):
    # Init
    selected_question = None
    all_question = Question.objects.all()
    countQ=0
    qid=[]
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('id')

    if request.method == 'POST':
        #form = forms.NewQuestion(request.POST) # Bind to user submitted form

        form = forms.InsertQuestionForm(request.POST) # Bind to user submitted form


        if form.is_valid():
            content=form.cleaned_data['content']         
            newqns = str(content)
            # Check if question exists
            s2 = str(content.lower())

            for qns in all_question:
                s1 = str(qns.content.lower())
                if s1 == s2:
                    qid.append(qns)

            # Let User see these qns
            if len(qid)>0:
                countQ = len(qid)
                return render(request, 'itemrtweb/manage.question.new.html', {'form': form,  'selected_question': qid, 'countQ':countQ})
            else:

            # INITIALISE - Get from POST

                content=form.cleaned_data['content']
                '''
                choiceA=form.cleaned_data['choiceA']
                choiceB=form.cleaned_data['choiceB']
                choiceC=form.cleaned_data['choiceC']
                choiceD=form.cleaned_data['choiceD']
                #choiceF=form.cleaned_data['choiceF']

     

                # STD_ANSWER
                choice = choiceA +";"+choiceB +";"+choiceC +";"+choiceD
                choiceAll = choice.split(';')
                ans_a= choiceAll[0]
                ans_b = choiceAll[1]
                ans_c = choiceAll[2]
                ans_d = choiceAll[3]
                std_ans =''
                if answer == "A": std_ans =ans_a
                elif answer == "B": std_ans = ans_b
                elif answer == "C": std_ans = ans_c
                elif answer == "D": std_ans = ans_d
    '''

                choice = form.cleaned_data['choiceA']
                source=form.cleaned_data['source']
                #answer = 'A'
                #std_ans = 'A'
                #ans = 'B'
                # PARSER
                ques = str(content.lower())
                ans = str(choice.lower())
                tokens = nltk.word_tokenize(ques)
                tokenans = nltk.word_tokenize(ans)

                length = len(tokens)
                pos = -1
                for i in range(0,length-1):
                    if tokens[i] == "*":
                        pos = i
                tokens.pop(pos)
                for x in reversed(tokenans): tokens.insert(pos,x)

                default_tagger = nltk.data.load('taggers/maxent_treebank_pos_tagger/english.pickle')

                model = {'more':'ADV','yesterday':'ADV','the':'DD','a':'DD','an':'DD','so':'CC','yet':'CC', 'apart':'CC','nevertheless':'CC','lest':'CC',
                'unless':'CC','despite':'CC','although':'CC','besides':'CC','since':'CC','than':'CC','until':'CC','except':'CC','though':'CC',
                'many':'DT','much':'DT','most':'DT','few':'DT','fewer':'DT','other':'DT','little':'DT','none':'DT','less':'DT','everyone':'DT','anything':'DT',
                'out':'IN','up':'IN','down':'IN','off':'IN','whose':'WH','how':'WH','mine':'PRP','ourselves':'PRP','themselves':'PRP','is':'SVA','are':'SVA','was':'SVA','were':'SVA','am':'SVA','has':'SVA','have':'SVA','had':'SVA','does':'SVA'}
                tagger = nltk.tag.UnigramTagger(model=model, backoff=default_tagger)

                tagged = tagger.tag(tokens) ##nltk.pos_tag(tokens)
                simplified = [(word, simplify_brown_tag(tag)) for word, tag in tagged] ##added in
                puretagged = nltk.pos_tag(tokens)
                key = ' '.join([tup[1] for tup in puretagged]) ##replaced tagged with simplified
                parse = ''
                for x in range (len(tokenans)):
                    parse += simplified[pos+x][1] + ' ' ##replaced tagged with simplified

                min = pos-3
                max = pos + 3
                if min < 0 : min = 0
                if max > len(tokens): max = len(tokens)
                parsechoice = ''
                for x in range(min,max):
                    parsechoice += puretagged[x][1] + ' '

                # Topic
                ques = str(content)
                whole = str(key)
                parse = str(parse)
                topic= 11
                # Filter from higher prob to lower prob
                if parse[0:2] == "WH":topic = 10
                elif parse[0:5] == "MOD ":topic = 7
                elif parse[0:3] == "Q ": topic = 5
                elif parse[0:4] == "DD Q":topic = 5
                elif ques.find("?") != -1:
                    if whole.find("RB PRP .")!= -1: topic=11
                    elif whole.find("VBZ PRP")!= -1: topic = 11
                elif parse[0:5] == "SVA ": topic = 3
                elif parse[0:5] == "PRO ": topic = 2
                elif parse[0:3] == "P ": topic = 8
                elif parse[0:2] == "DD":topic = 1
                elif parse[0:5] == "CNJ ":topic = 9
                elif parse[0:5] == "ADV ":topic = 6
                elif parse.find("ADJ")!= -1: topic = 5
                elif parse.find("MOD")!= -1: topic = 7
                elif parse.find(" P ")!= -1: topic = 8
                else: topic=4

                # Insert new question
                question = Question(
                content=form.cleaned_data['content'],
                topic = Topic.objects.get(id=topic),
                choice= choice,
                source=form.cleaned_data['source'],
                #std_answer = std_ans,
                wholeparse = key,
                choiceparse = parsechoice,
                parse = parse,
                new_topic = topic,
                difficulty=0)
                question.save()

                # Insert answer for question
                answer = Answer(question=question, content=form.cleaned_data['choiceA'])
                answer.save()

                # Insert solution if exists
                if form.cleaned_data['solution']:
                    solution = Solution(question=question, content=form.cleaned_data['solution'])
                    solution.save()

                # Question inserted successfully!
                return redirect('/question/insert/'+ str(question.id))

        # Reply regardless valid
        return render(request, 'itemrtweb/manage.question.insert.html', {'form': form, 'topics': topics , 'selected_question': selected_question,})
    else:
        # Obtain the list of topics
        #topics = Topic.objects.all().order_by('id')
        form = forms.InsertQuestionForm()
#'form': form,
    return render(request, 'itemrtweb/manage.question.insert.html', { 'form': form,'topics': topics , 'selected_question': selected_question,})

@login_required ##@user_passes_test(lambda u: u.is_staff)
def prototypeauto_2(request, question_id=None):
    # Init
    selected_question = None
    all_question = Question.objects.all()
    countQ=0
    qid=[]
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('id')

    if request.method == 'POST':
        #form = forms.NewQuestion(request.POST) # Bind to user submitted form

        form = forms.InsertQuestionForm_2(request.POST) # Bind to user submitted form


        if form.is_valid():
            content=form.cleaned_data['content']         
            newqns = str(content)
            # Check if question exists
            s2 = str(content.lower())

            for qns in all_question:
                s1 = str(qns.content.lower())
                if s1 == s2:
                    qid.append(qns)

            # Let User see these qns
            if len(qid)>0:
                countQ = len(qid)
                return render(request, 'itemrtweb/manage.question.new.html', {'form': form,  'selected_question': qid, 'countQ':countQ})
            else:

            # INITIALISE - Get from POST

                content=form.cleaned_data['content']
              
                choice1=form.cleaned_data['choice1']
                choice2=form.cleaned_data['choice2']
                choice3=form.cleaned_data['choice3']
                choice4=form.cleaned_data['choice4']
                choice5=form.cleaned_data['choice5']
                choice6=form.cleaned_data['choice6']
                choice7=form.cleaned_data['choice7']
                choice8=form.cleaned_data['choice8']
                choice9=form.cleaned_data['choice9']
                choice10=form.cleaned_data['choice10']
     

                # STD_ANSWER
                choice = choice1 +";"+choice2 +";"+choice3 +";"+choice4+";"+choice5 +";"+choice6 +";"+choice7+";"+choice8 +";"+choice9 +";"+choice10
                '''
                choiceAll = choice.split(';')
                ans_a= choiceAll[0]
                ans_b = choiceAll[1]
                ans_c = choiceAll[2]
                ans_d = choiceAll[3]
                std_ans =''
                if answer == "A": std_ans =ans_a
                elif answer == "B": std_ans = ans_b
                elif answer == "C": std_ans = ans_c
                elif answer == "D": std_ans = ans_d
  '''
                source1 = form.cleaned_data['source1']
                source2 = form.cleaned_data['source2']
                source3 = form.cleaned_data['source3']
                source4 = form.cleaned_data['source4']
                source5 = form.cleaned_data['source5']
                source6 = form.cleaned_data['source6']
                source7 = form.cleaned_data['source7']
                source8 = form.cleaned_data['source8']
                source9 = form.cleaned_data['source9']
                source10 = form.cleaned_data['source10']

               # choice = form.cleaned_data['choiceA']
                source = source1 +";"+source2 +";"+choice3 +";"+source4+";"+source5 +";"+source6 +";"+source7+";"+source8 +";"+source9 +";"+source10
                #source=form.cleaned_data['source']
                #answer = 'A'
                std_ans = 'A'
                ans = 'B'
                # PARSER
                ques = str(content.lower())
                #=ans = str(std_ans.lower())
                tokens = nltk.word_tokenize(ques)
                tokenans = nltk.word_tokenize(ans)

                length = len(tokens)
                pos = -1
                for i in range(0,length-1):
                    if tokens[i] == "*":
                        pos = i
                tokens.pop(pos)
                for x in reversed(tokenans): tokens.insert(pos,x)

                default_tagger = nltk.data.load('taggers/maxent_treebank_pos_tagger/english.pickle')

                model = {'more':'ADV','yesterday':'ADV','the':'DD','a':'DD','an':'DD','so':'CC','yet':'CC', 'apart':'CC','nevertheless':'CC','lest':'CC',
                'unless':'CC','despite':'CC','although':'CC','besides':'CC','since':'CC','than':'CC','until':'CC','except':'CC','though':'CC',
                'many':'DT','much':'DT','most':'DT','few':'DT','fewer':'DT','other':'DT','little':'DT','none':'DT','less':'DT','everyone':'DT','anything':'DT',
                'out':'IN','up':'IN','down':'IN','off':'IN','whose':'WH','how':'WH','mine':'PRP','ourselves':'PRP','themselves':'PRP','is':'SVA','are':'SVA','was':'SVA','were':'SVA','am':'SVA','has':'SVA','have':'SVA','had':'SVA','does':'SVA'}
                tagger = nltk.tag.UnigramTagger(model=model, backoff=default_tagger)

                tagged = tagger.tag(tokens) ##nltk.pos_tag(tokens)
                simplified = [(word, simplify_brown_tag(tag)) for word, tag in tagged] ##added in
                puretagged = nltk.pos_tag(tokens)
                key = ' '.join([tup[1] for tup in puretagged]) ##replaced tagged with simplified
                parse = ''
                for x in range (len(tokenans)):
                    parse += simplified[pos+x][1] + ' ' ##replaced tagged with simplified

                min = pos-3
                max = pos + 3
                if min < 0 : min = 0
                if max > len(tokens): max = len(tokens)
                parsechoice = ''
                for x in range(min,max):
                    parsechoice += puretagged[x][1] + ' '

                # Topic
                ques = str(content)
                whole = str(key)
                parse = str(parse)
                topic= 11
                # Filter from higher prob to lower prob
                if parse[0:2] == "WH":topic = 10
                elif parse[0:5] == "MOD ":topic = 7
                elif parse[0:3] == "Q ": topic = 5
                elif parse[0:4] == "DD Q":topic = 5
                elif ques.find("?") != -1:
                    if whole.find("RB PRP .")!= -1: topic=11
                    elif whole.find("VBZ PRP")!= -1: topic = 11
                elif parse[0:5] == "SVA ": topic = 3
                elif parse[0:5] == "PRO ": topic = 2
                elif parse[0:3] == "P ": topic = 8
                elif parse[0:2] == "DD":topic = 1
                elif parse[0:5] == "CNJ ":topic = 9
                elif parse[0:5] == "ADV ":topic = 6
                elif parse.find("ADJ")!= -1: topic = 5
                elif parse.find("MOD")!= -1: topic = 7
                elif parse.find(" P ")!= -1: topic = 8
                else: topic=4

                #topic = 11
                # Insert new question
                question = Question(
                content=form.cleaned_data['content'],
                topic = Topic.objects.get(position=13),
                choice= choice,
                source=source,
                #std_answer = std_ans,
                wholeparse = key,
                choiceparse = parsechoice,
                parse = parse,
                new_topic = topic,
                difficulty=0)
                question.save()

                # Insert answer for question
                answer = Answer(question=question, content=form.cleaned_data['choice1'])
                answer.save()

                # Insert solution if exists
                if form.cleaned_data['solution']:
                    solution = Solution(question=question, content=form.cleaned_data['solution'])
                    solution.save()

                # Question inserted successfully!
                return redirect('/question/insert/'+ str(question.id))

        # Reply regardless valid
        return render(request, 'itemrtweb/manage.question.insert2.html', {'form': form, 'topics': topics , 'selected_question': selected_question,})
    else:
        # Obtain the list of topics
        #topics = Topic.objects.all().order_by('id')
        form = forms.InsertQuestionForm_2()
#'form': form,
    return render(request, 'itemrtweb/manage.question.insert2.html', { 'form': form,'topics': topics , 'selected_question': selected_question,})




@login_required ##@user_passes_test(lambda u: u.is_staff)
def postauto(request, question_id=None):
    # Init
    selected_question = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if question_id:
        selected_question = Question.objects.all().get(id=int(question_id))
        # Check if question exists or give blank form
    if selected_question:
        # Load existing question into a form
        form = forms.InsertEditQuestionForm(initial={'content':selected_question.content, 'choice':selected_question.choice, 'source':selected_question.source,'difficulty':selected_question.difficulty, 'topic':selected_question.topic, 'answer':selected_question.answers.all()[0].content, 'tags': selected_question.tags.all().values_list('name', flat=True), })
        #form = forms.InsertEditQuestionForm(request.POST) # Bind to user submitted form
        ##INITIALISE
        qid = question_id
        content = selected_question.content
        choice=selected_question.choice
        #answer = selected_question.answers.all()[0].content
        source=selected_question.source
        topic=selected_question.topic
        tags = selected_question.tags.all().values_list('name', flat=True)
        topicid = selected_question.topic.id
        std_ans =selected_question.std_answer
        key = selected_question.wholeparse
        parse = selected_question.parse


        ##DIFFICULTY
        sel = Question.objects.filter(id=int(question_id)).values()
        for q in sel:
            q_id = q['id']
            q_content = q['content']
            q_item = Question.objects.get(id=q_id)
            a = process_parse(q)
            b = process_diff(a)
            difficulty = b

        selected_question.difficulty = difficulty
        selected_question.save()

        #delete old keywords relationships
        oldkeywordtags = QuestionTag.objects.filter(question__id=question_id)
        oldkeywordtags.delete()

        keywords = Tag.objects.filter(topic=topic) ##type='K'

        for keyword in keywords:
            #keywordfound = Question.objects.filter(id=int(question_id)).filter(Q(content__iregex='[[:<:]]' + keyword.name + '[[:>:]]')|Q(choice__iregex='[[:<:]]' + keyword.name + '[[:>:]]'))  #search for keyword
            keywordfound = Question.objects.filter(id=int(question_id)).filter(Q(std_answer__iregex='[[:<:]]' + keyword.name + '[[:>:]]'))  #search for keyword

            for kf in keywordfound:
                #create new tag relationship
                newtag = QuestionTag(question=kf, tag=keyword)
                newtag.save()

        keyconcepts = Concept.objects.filter(topic=topic)
        for keyconcept in keyconcepts:
            conwords = keyconcept.words.all()
            if conwords:
                if len(conwords)>1:
                    conceptfound = Question.objects.filter(id=int(question_id)).filter(reduce(lambda x, y: x | y, [Q(std_answer__iregex='[[:<:]]' + conword.name + '[[:>:]]') for conword in conwords]))
                else:
                    for conword in conwords:
                        conceptfound = Question.objects.filter(id=int(question_id)).filter(Q(std_answer__iregex='[[:<:]]' + conword.name + '[[:>:]]'))
                for kf in conceptfound:
                    #create new tag relationship
                    newconcept = QuestionConcept(question=kf, concept=keyconcept)
                    newconcept.save()
        # Solution
        solution_exists = Solution.objects.all().filter(question=selected_question).count()

        if solution_exists > 0:
            form.fields["solution"].initial = selected_question.solution.content

        ##return redirect('/prototype2/list/topic/'+ str(selected_question.topic.id) +'/?msg=Question '+ str(selected_question.id) +' edited successfully#question-'+ str(selected_question.id))
    else:
        # Display new form for user to fill in
        form = forms.InsertQuestionForm()

    return render(request, 'itemrtweb/manage.question.update.html', {'form': form,'qid':qid, 'content':content,'choice':choice,'topic':topic,'topicid':topicid,'tags':tags,'source':source,'topics': topics,  'selected_question': selected_question, 'std_ans':std_ans, 'key':key, 'parse':parse, 'difficulty':difficulty, 'concepts':keyconcepts})
##@login_required
##def forum(request):
##    # Init
##    filtered_threads = Thread.objects.all()
##
##    # Obtain the list of topics
##    topics = Topic.objects.all().order_by('position')
##
##    # Obtain counts of questions per topic
##    topic_count = {}
##    for topic in topics:
##        topicQcount = Thread.objects.filter(topic=topic).count()
##        topic_count[topic]=topicQcount
##
##    return render(request, 'itemrtweb/forum.home.html', {'topics': topics, 'topic_count':topic_count})
##
##@login_required
##def forumtopic(request, topic_id=None):
##    # Init
##    filtered_threads = Thread.objects.all()
##
##    # Obtain the list of topics
##    topics = Topic.objects.all().order_by('position')
##
##     # Obtain counts of questions per topic
##    topic_count = {}
##    for topic in topics:
##        topicQcount = Thread.objects.filter(topic=topic).count()
##        topic_count[topic]=topicQcount
##
##    selected_topic = None
##
##    if topic_id:
##        # Retrieve questions for this topic
##        filtered_threads = Thread.objects.all().filter(topic=topic_id).order_by('-latest')
##
##        count = filtered_threads.count()
##
##        selected_topic = Topic.objects.all().get(id=topic_id)
##
##        paginator = Paginator(filtered_threads, 20)
##
##        page = request.GET.get('page')
##
##        try:
##            questions = paginator.page(page)
##        except PageNotAnInteger:
##            questions = paginator.page(1)
##        except EmptyPage:
##            questions = paginator.page(paginator.num_pages)
####    else:
####        questions = None
##    # Remove page number from querystring
##    q = request.GET
##    z = q.copy()
##    try:
##        del z['page']
##    except KeyError:
##        pass
##    querystring = '?' + z.urlencode()
##
##    return render(request, 'itemrtweb/forum.html', {'topics': topics, 'questions': questions, 'filtered_threads' : filtered_threads,'querystring': querystring, 'selected_topic':selected_topic, 'topic_count':topic_count, 'count':count})
##
##@login_required
##def forumthread(request, topic_id=None, thread_id=None):
##    # Init
##    filtered_threads = Thread.objects.all()
##
##    # Obtain the list of topics
##    topics = Topic.objects.all().order_by('position')
##
##     # Obtain counts of questions per topic
##    topic_count = {}
##    for topic in topics:
##        topicQcount = Thread.objects.filter(topic=topic).count()
##        topic_count[topic]=topicQcount
##
##    selected_topic = None
##
##    if request.method == 'POST':
##        form = forms.PostForm(request.POST)
##        if form.is_valid():
##            # Get the thread
##            thread = Thread.objects.get(id=thread_id)
##
##            # Get Post
##            post = Post(datetime=datetime.now(), thread=thread, user=request.user, content=form.cleaned_data['content'])
##            post.save()
##
##            thread.latest = datetime.now()
##            thread.save()
##
##            # Question inserted successfully!
##            return redirect('/forum/'+ str(thread.topic.id)+'/'+str(thread_id))
##    else:
##        # Display new form for user to fill in
##        form = forms.PostForm()
##
##    if thread_id:
##        # Retrieve questions for this topic
##        selected_topic = Topic.objects.all().get(id=topic_id)
##        selected_thread = Thread.objects.all().get(id=thread_id)
##        selected_post = Post.objects.all().filter(thread_id=thread_id).order_by('datetime')
##        count = selected_post.count()
##        selected_thread.view += 1
##        selected_thread.reply = count
##        selected_thread.save()
##
##    return render(request, 'itemrtweb/forum.thread.html', {'form':form,'topics': topics, 'selected_topic':selected_topic, 'selected_thread':selected_thread, 'selected_post':selected_post, 'topic_count':topic_count, 'count':count})
##
##@login_required
##def foruminsert(request):
##
##    # Obtain the list of topics
##    topics = Topic.objects.all().order_by('position')
##    if request.method == 'POST':
##        form = forms.ForumForm(request.POST) # Bind to user submitted form
##        if form.is_valid():
##            # Insert new question
##            thread = Thread(content=form.cleaned_data['content'], topic=form.cleaned_data['topic'], user=request.user, datetime=datetime.now(),latest=datetime.now())
##            thread.save()
##            # Question inserted successfully!
##            return redirect('/forum/'+ str(thread.topic.id))
##    else:
##        form = forms.ForumForm()
##
##    return render(request, 'itemrtweb/forum.insert.html', {'form': form, 'topics': topics})

@login_required
def browsequestion(request, question_id=None):
    # Init
    selected_question = None

    # Objectify the selected question
    if question_id:
        selected_question = Question.objects.all().get(id=int(question_id))
        # Get correct answer
        selected_question.answer = selected_question.answers.all()[0]

    token = selected_question.content.split(';')
    choice = selected_question.choice.split(';')
    ans = str(selected_question.std_answer.strip())
    display = []
    item= []
    #for each question part
    for t in token:
        c = t.strip().count("*")
        if c == 2:
            ans = ans.split('...')
            item = t.strip().replace("*", ans[0],1)
            item= item.replace("*", ans[1],1)
        else:
            item = t.strip().replace("*", ans)
        display.append(item)
        item = []
    q_display = display[0]
    tags = str(q_display.strip())
    str1 = " ".join(str(x) for x in choice)

    import numpy as np
    from math import sqrt, log
    from itertools import chain, product
    from collections import defaultdict

    def cosine_sim(u,v):
        return np.dot(u,v) / (sqrt(np.dot(u,u)) * sqrt(np.dot(v,v)))

    def corpus2vectors(corpus):
        def vectorize(sentence, vocab):
            return [sentence.split().count(i) for i in vocab]
        vectorized_corpus = []
        vocab = sorted(set(chain(*[i.lower().split() for i in corpus])))
        for i in corpus:
            vectorized_corpus.append((i, vectorize(i, vocab)))
        return vectorized_corpus, vocab

    filtered_questions = Question.objects.all().filter(topic__id=selected_question.topic.id).order_by('id')

    count = filtered_questions.count()
    sents=[]
    for sel in filtered_questions:
        token = sel.content.split(';')
        ctoken = sel.choice.split(';')
        ans = str(sel.std_answer.strip())
        display = []
        item= []
        #for each question part
        for t in token:
            c = t.strip().count("*")
            if c == 2:
                ans = ans.split('...')
                item = t.strip().replace("*", ans[0],1)
                item= item.replace("*", ans[1],1)
            else:
                item = t.strip().replace("*", ans)
            display.append(item)
            item = []
        q_display = display[0]
        sents = str(q_display.strip())
        str2 = " ".join(str(x) for x in ctoken)

        all_sents = [tags] + [sents]
        corpus, vocab = corpus2vectors(all_sents)
        results = []
        for search, senty in product(corpus, corpus):
            results.append( cosine_sim(search[1], senty[1]))

        all_c = [str1.lower()] + [str2.lower()]
        ccorpus, cvocab = corpus2vectors(all_c)
        cresults = []
        for search, senty in product(ccorpus, ccorpus):
            cresults.append( cosine_sim(search[1], senty[1]))

        sel.result=results[1] * 0.2 + cresults[1] * 0.8
        sel.save()

    filtered_questions = filtered_questions.order_by("-result")[1:6]

    allquestions = Question.objects.all().exclude(topic__id=selected_question.topic.id).order_by("id")

    count = allquestions.count()
    sents=[]
    for sel in allquestions:
        token = sel.content.split(';')
        ans = str(sel.std_answer.strip())
        display = []
        item= []
        #for each question part
        for t in token:
            c = t.strip().count("*")
            if c == 2:
                ans = ans.split('...')
                item = t.strip().replace("*", ans[0],1)
                item= item.replace("*", ans[1],1)
            else:
                item = t.strip().replace("*", ans)
            display.append(item)
            item = []
        q_display = display[0]
        sents = str(q_display.strip())

        all_sents = [tags] + [sents]
        corpus, vocab = corpus2vectors(all_sents)
        results = []
        for search, senty in product(corpus, corpus):
            results.append( cosine_sim(search[1], senty[1]))
        sel.result=results[1]
        sel.save()

    allquestions = allquestions.order_by("-result")[:5]

    # Check if question exists otherwise redirect to question list
    if selected_question:
        return render(request, 'itemrtweb/search.question.html', {'question': selected_question, 'related':filtered_questions, 'allrelated':allquestions})
    else:
        # 404 if question was not found
        raise Http404

#Topic Tag Section
def analyzer_topic_tag(request,topic_id):
    ##topic_id=5
    selected_topic=None
    #list of topics for dropdownlist
    topics = Topic.objects.all().order_by('position').values()
    # int the selected topic
    selected_topic = topics.get(id=topic_id)
    onetags = Tag.objects.all()
    #tag cloud settings
    f_max = 36  #font size maximum
    #font size is determined by:
    #IF the current frequency is not minimum, then its integer is int(math.ceil((f_max*(t_i - t_min))/(t_max - t_min)))
    #ELSE the minimum font size is 10
    size = lambda f_max, t_max, t_min, t_i: t_i > t_min and 10 + int(
        math.ceil((f_max * (t_i - t_min)) / (t_max - t_min))) or 10
    #finding the t_min and t_max
    t_min = 999999  #min frequency initialized as 999999 at first
    t_max = 0  #max frequency initialized as 0 at first

    #calibrating the min max font
    for tagitem in onetags:
        tagdef = QuestionTag.objects.filter(tag_id=tagitem.id).filter(question__topic__id=topic_id).count()
        if tagdef < t_min:t_min = tagdef
        if tagdef > t_max:t_max = tagdef


    #packing the tag cloud
    onecloud = []
    for tagitem in onetags:
        pcount = QuestionTag.objects.filter(tag_id=tagitem.id).filter(question__topic__id=topic_id).count()
        if pcount>0:
            onecloud.append({'id': tagitem.id,
                             'tag': tagitem.name,
                             'count': pcount,
                             'size': size(f_max, t_max, t_min, pcount)})

    return render(request, 'itemrtweb/analyzer_topic_tag.html', {'onecloud':onecloud,'topics':topics,'selected_topic':selected_topic})

def analyzer_tag(request):
    selected_topic=None
    #list of topics for dropdownlist
    topics = Topic.objects.all().order_by('position').values()
    onetags = Tag.objects.all()
    #tag cloud settings
    f_max = 36  #font size maximum
    #font size is determined by:
    #IF the current frequency is not minimum, then its integer is int(math.ceil((f_max*(t_i - t_min))/(t_max - t_min)))
    #ELSE the minimum font size is 10
    size = lambda f_max, t_max, t_min, t_i: t_i > t_min and 10 + int(
        math.ceil((f_max * (t_i - t_min)) / (t_max - t_min))) or 10
    #finding the t_min and t_max
    t_min = 999999  #min frequency initialized as 999999 at first
    t_max = 0  #max frequency initialized as 0 at first

    #calibrating the min max font
    for tagitem in onetags:
        tagdef = QuestionTag.objects.filter(tag_id=tagitem.id).count()
        if tagdef < t_min:t_min = tagdef
        if tagdef > t_max:t_max = tagdef


    #packing the tag cloud
    onecloud = []
    for tagitem in onetags:
        pcount = QuestionTag.objects.filter(tag_id=tagitem.id).count()
        if pcount>0:
            onecloud.append({'id': tagitem.id,
                             'tag': tagitem.name,
                             'count': pcount,
                             'size': size(f_max, t_max, t_min, pcount)})

    return render(request, 'itemrtweb/analyzer_topic_tag.html', {'onecloud':onecloud,'topics':topics})

def gentest(request, test_id=None):

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    numQns = 9
    question_pool = Question.objects.all().order_by('difficulty')
    testquestion = Question.objects.none()
    for i in range (1,12):
        question_pool = Question.objects.all().filter(topic__id=i)
        a = random.randint(0, question_pool.count()-1)
        question = Question.objects.filter(id=a)
        testquestion = testquestion | question
    question_pool = Question.objects.all().order_by('difficulty')
    for i in range (0, numQns):
        a = random.randint(0, question_pool.count()-1)
        question = Question.objects.filter(id=a)
        testquestion = testquestion | question
    final = testquestion.order_by('topic')
    return render(request, 'itemrtweb/gentest.html', {'testquestions': final})

@login_required
def paperprac(request, test_id=None):
    #Init
    selected_mode = 3
    "Boombastic function! Change with care."
    # Record usage for stats purpose
    page = "paper_prac"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    if not test_id:
        if request.method == 'POST' and 'test_id' in request.POST and request.POST['test_id']:
            return redirect('/practice/paper/'+request.POST['test_id']+'/')
        elif request.method == 'POST' and 'num_qn' in request.POST and request.POST['num_qn']: ##and 'topics' in request.POST:
            # Check if all param is in
            # Get number of questions and difficulty
            avg = 0
            if request.POST['qn_diff']: avg = int(request.POST['qn_diff'])

            numQns = int(request.POST['num_qn'])
            if numQns > 20:
                numQns = 20

            testid = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(6))

            #### VERY IMPORTANT TODO:: CHECK FOR UNIQUE ID
            new_test = Test(id=testid, user=request.user, assessment=Assessment.objects.all().get(name='Paper Quiz'))
            new_test.save()

            numQns = int(numQns)

            topics_selected = int(request.POST['topic']) ##request.POST.getlist('topics')

            ##topics_all = list(topics.values_list('id', flat=True))

            ##for topic_id in topics_selected:
            ##    topics_all.remove(int(topic_id))
            if avg > 0 :
                question_pool = Question.objects.all().filter(difficulty=int(avg))
            else:
                question_pool = Question.objects.all()
            question_pool = question_pool.filter(topic__id=topics_selected) ##exclude(topic__in=topics_all)

            for i in range (0, numQns):
                # Get a random question and add to paper
                question_pool = question_pool.exclude(id__in=new_test.questions.all().values_list('id'))

                if question_pool:
                    question = question_pool[random.randint(0, question_pool.count()-1)]
                    newTestQuestion = TestQuestion(question=question, test=new_test)
                    newTestQuestion.save()

            return redirect('/practice/paper/'+str(testid)+'/')
        elif request.method == 'POST':
            error = {}
            if 'num_qn' not in request.POST or not request.POST['num_qn']:
                error['num_qn'] = True
            return render(request, 'itemrtweb/paperprac.home.html', {'error': error, 'topics': topics})

        return render(request, 'itemrtweb/paperprac.home.html', {'topics': topics, 'selected_mode':selected_mode})
    else:
        # test_id is available, render test instead
        test = Test.objects.all().get(id=test_id)

        return render(request, 'itemrtweb/paperprac.question.html', {'test': test, 'selected_mode':selected_mode})

@login_required
def paperpracsubmit(request, test_id):
    test = Test.objects.all().get(id=test_id)

    if request.method == 'POST':
        # Check each question if it has been attempted
        for question in test.questions.all():
            try:
                # Previously saved response available? OK do nothing for now.
                test_response = TestResponse.objects.filter(test=test).filter(user=request.user).get(question=question)
                pass
            # Otherwise new response, create object
            except ObjectDoesNotExist:
                test_response = TestResponse(test=test, user=request.user, question=question, response='<No Answer Given>', criterion=question.marks, assessment=test.assessment)
                test_response.save()

        # Assign a score for each question
        total_ability = 0

        for question in test.questions.all():
            test_response = TestResponse.objects.filter(test=test).filter(user=request.user).get(question=question)

            response = test_response.response
            response = response.replace(' ', '').replace('\\n', '').replace('\\r', '').replace('\\t', '')

            # Get actual answer in string
            answer_text = question.choices[question.answers.all()[0].content.lower()]
            answer_text = answer_text.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

            correctness = 0
            if re.match('^'+answer_text+'$', response):
                correctness = question.answers.all()[0].correctness

            print >> sys.stderr, response + " == " + answer_text + " : " + str(correctness)

            # Update correctness
            test_response.correctness = correctness

            # Update ability
            total_ability = total_ability + correctness
            test_response.ability = total_ability

            test_response.save()

        test.state = True
        test.save()

        # Prevent resubmission of test
        return redirect('/practice/paper/submit/' + test_id + '/')

    elif request.method == 'GET':
        return render(request, 'itemrtweb/paperprac.submit.html', {'test': test, 'final_score': int(test.score)})

@login_required
def paperpracutil(request, test_id=None, util_name=None):
    "Util functions for Boombastic function!"

    if test_id:
        test = Test.objects.all().get(id=test_id)
        # Util to return test endtime
        if util_name == 'getendtime':
            time = test.questions.count()*1
            endtime = test.generated+timedelta(minutes=time) # Time Control

            return HttpResponse(endtime.isoformat())
        elif util_name == 'save':
            if 'qn_id' in request.POST and request.POST['qn_id']:
                # Get question (or nothing) from orm
                question = Question.objects.all().get(id=request.POST['qn_id'])

                # Check test not completed, question exists
                if test.state == False and test.questions.filter(id=question.id).exists():
                    # Check that there was a answer sent together with message
                    if 'answer' in request.POST and request.POST['answer']:
                        try:
                            # Previously saved response available? Resave if so!
                            test_response = TestResponse.objects.filter(test=test).filter(user=request.user).get(question=question)
                            test_response.response = request.POST['answer']
                            test_response.save()
                        # Otherwise new response, create object
                        except ObjectDoesNotExist:
                            test_response = TestResponse(test=test, user=request.user, question=question, response=request.POST['answer'], criterion=question.marks, assessment=test.assessment)
                            test_response.save()

                        return HttpResponse("Saved")
                    # Otherwise no answer just return nothing happened!
                    else:
                        return HttpResponse("Empty")
    raise Http404

@login_required
def papertesthist(request):
    tests = Test.objects.filter(assessment_id=5).filter(user=request.user).order_by('-generated')
    tlist={}
    qlist={}
    plist={}
    wlist={}
    for test in tests:
        test_response = TestResponse.objects.filter(test=test).filter(user=request.user).order_by('-ability')
        if test_response.count() > 0:
            tlist[test.id]=int(test_response[0].ability)
            qlist[test.id]=test_response.count()
            plist[test.id]=round(float(test_response[0].ability) / float( test_response.count()) * 100,2)
        else:
            tlist[test.id]=0
            plist[test.id]=0
            qlist[test.id]=0

        test_question = TestQuestion.objects.filter(test=test)
        test_topic=Topic.objects.none()

        get_topic = None
        related_topic = Topic.objects.none()
        topic_get=[]
        for q in test_question:
            get_topic = Topic.objects.filter(id=q.question.topic.id)
            related_topic = related_topic | get_topic
        for t in related_topic:
            topic_get.append(str(t.name))
        wlist[test.id]=topic_get
        # Get list of questions that user has previously commented on
    questions_commented_id = Comment.objects.all().filter(content_type=ContentType.objects.get_for_model(Question)).filter(user=request.user).values_list('object_pk')
    questions_commented = Question.objects.all().filter(pk__in=questions_commented_id)

    return render(request, 'itemrtweb/papertest.history.html', {'tests': tests, 'tlist':tlist,'qlist':qlist,'plist':plist,'wlist':wlist,'questions_commented':questions_commented})



@login_required
def diff(request,qid=None):
    c = 0
    param = {}

    from nltk.tokenize import RegexpTokenizer

    TOKENIZER = RegexpTokenizer('(?u)\W+|\$[\d\.]+|\S+')
    SPECIAL_CHARS = ['.', ',', '!', '?']

    def get_char_count(words):
        characters = 0
        for word in words:
            characters += len(word.decode("utf-8"))
        return characters

    def get_words(text=''):
        words = []
        words = TOKENIZER.tokenize(text)
        filtered_words = []
        for word in words:
            if word in SPECIAL_CHARS or word == " ":
                pass
            else:
                new_word = word.replace(",","").replace(".","")
                new_word = new_word.replace("!","").replace("?","")
                filtered_words.append(new_word)
        return filtered_words

    def get_sentences(text=''):
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        sentences = tokenizer.tokenize(text)
        return sentences

    specialSyllables_en = """
    ok 2
    tv 2
    cd 2
    steely 2
    file 1
    hole 1
    mile 1
    pale 1
    pile 1
    pole 1
    role 1
    rule 1
    scale 1
    smile 1
    sole 1
    stale 1
    style 1
    tale 1
    vile 1
    while 1
    whole 1
    acre 2
    beauty 2
    being 2
    bureau 2
    business 2
    buyer 2
    carriage 2
    centre 2
    colleague 2
    colonel 2
    compile 2
    create 2
    cruel 2
    diet 2
    evening 2
    female 2
    fibre 2
    fluid 2
    framework 2
    going 2
    guideline 2
    household 2
    hundred 2
    judgement 2
    layer 2
    lifetime 2
    lion 2
    marriage 2
    mayor 2
    metre 2
    missile 2
    module 2
    movement 2
    pavement 2
    player 2
    poem 2
    prayer 2
    profile 2
    ratio 2
    rely 2
    safety 2
    schedule 2
    science 2
    spokesman 2
    squeaky 2
    statement 2
    technique 2
    achievement 3
    announcement 3
    area 3
    arrangement 3
    awareness 3
    barrier 3
    behaviour 3
    businessman 3
    carrier 3
    casual 3
    catalogue 3
    champion 3
    coincide 3
    creation 3
    criticism 3
    dialogue 3
    employee 3
    employer 3
    engagement 3
    equation 3
    excitement 3
    graduate 3
    idea 3
    improvement 3
    influence 3
    involvement 3
    loyalty 3
    management 3
    measurement 3
    mechanism 3
    molecule 3
    musician 3
    organism 3
    parliament 3
    poetry 3
    policeman 3
    reaction 3
    realise 3
    realize 3
    reassure 3
    recipe 3
    reinforce 3
    replacement 3
    requirement 3
    retirement 3
    shareholder 3
    situate 3
    suicide 3
    supplier 3
    theatre 3
    theory 3
    united 3
    video 3
    advertisement 4
    anxiety 4
    capitalism 4
    casualty 4
    championship 4
    constituent 4
    criterion 4
    evaluate 4
    experience 4
    hierarchy 4
    initiate 4
    negotiate 4
    politician 4
    reality 4
    situation 4
    society 4
    differentiate 5
    evaluation 5
    ideology 5
    individual 5
    initiation 5
    negotiation 5
    cheque 1
    quaint 1
    queen 1
    queer 1
    squeeze 1
    tongue 1
    mimes 1
    ms 1
    h'm 1
    brutes 1
    lb 1
    effaces 2
    mr 2
    mrs 2
    moustaches 2
    dr 2
    sr 2
    jr 2
    mangroves 2
    truckle 2
    fringed 2
    messieurs 2
    poleman 2
    sombre 2
    sidespring 2
    gravesend 2
    60 2
    greyish 2
    anyone 3
    amusement 3
    shamefully 3
    sepulchre 3
    hemispheres 3
    veriest 3
    satiated 4
    sailmaker 4
    etc 4
    unostentatious 5
    Propitiatory 6
    """
    fallback_cache = {}

    fallback_subsyl = ["cial", "tia", "cius", "cious", "giu", "ion", "iou",
                       "sia$", ".ely$"]

    fallback_addsyl = ["ia", "riet", "dien", "iu", "io", "ii",
                       "[aeiouym]bl$", "mbl$",
                       "[aeiou]{3}",
                       "^mc", "ism$",
                       "(.)(?!\\1)([^aeiouy])\\ll$",
                       "[^l]lien",
                       "^coad.", "^coag.", "^coal.", "^coax.",
                       "(.)(?!\\1)[gq]ua(.)(?!\\2)[aeiou]",
                       "dnt$"]


    # Compile our regular expressions
    for i in range(len(fallback_subsyl)):
        fallback_subsyl[i] = re.compile(fallback_subsyl[i])
    for i in range(len(fallback_addsyl)):
        fallback_addsyl[i] = re.compile(fallback_addsyl[i])

    def _normalize_word(word):
        return word.strip().lower()

    # Read our syllable override file and stash that info in the cache
    for line in specialSyllables_en.splitlines():
        line = line.strip()
        if line:
            toks = line.split()
            assert len(toks) == 2
            fallback_cache[_normalize_word(toks[0])] = int(toks[1])

    def count(word):
        word = _normalize_word(word)
        if not word:
            return 0

        # Check for a cached syllable count
        count = fallback_cache.get(word, -1)
        if count > 0:
            return count

        # Remove final silent 'e'
        if word[-2:] == "le":
            word = word+"s" #-le

        elif word[-2:] == "ed":
            word = word[:-2] #problematic -ed

        elif word[-1] == "e":
            word = word[:-1]


        # Count vowel groups
        count = 0
        prev_was_vowel = 0
        for c in word:
            is_vowel = c in ("a", "e", "i", "o", "u", "y")
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Add & subtract syllables
        for r in fallback_addsyl:
            if r.search(word):
                count += 1
        for r in fallback_subsyl:
            if r.search(word):
                count -= 1

        #for words with silent e +1 e.g. me, she, he, the
        if count == 0:
            count = 1

        # Cache the syllable count
        fallback_cache[word] = count

        return count

    def count_syllables(words):
        syllableCount = 0
        for word in words:
            syllableCount += count(word)
        return syllableCount

    def count_complex_words(text=''):
        words = get_words(text)
        sentences = get_sentences(text)
        complex_words = 0
        found = False
        cur_word = []

        for word in words:
            cur_word.append(word)
            if count_syllables(cur_word)>= 3:

                #Checking proper nouns. If a word starts with a capital letter
                #and is NOT at the beginning of a sentence we don't add it
                #as a complex word.
                if not(word[0].isupper()):
                    complex_words += 1
                else:
                    for sentence in sentences:
                        if str(sentence).startswith(word):
                            found = True
                            break
                    if found:
                        complex_words += 1
                        found = False

            cur_word.remove(word)
        return complex_words


    class Readability:
        analyzedVars = {}

        def __init__(self, text):
            self.analyze_text(text)

        def analyze_text(self, text):
            words = get_words(text)
            char_count = get_char_count(words)
            word_count = len(words)
            sentence_count = len(get_sentences(text))
            syllable_count = count_syllables(words)
            complexwords_count = count_complex_words(text)
            avg_words_p_sentence = word_count/sentence_count

            self.analyzedVars = {
                'words': words,
                'char_cnt': float(char_count),
                'word_cnt': float(word_count),
                'sentence_cnt': float(sentence_count),
                'syllable_cnt': float(syllable_count),
                'complex_word_cnt': float(complexwords_count),
                'avg_words_p_sentence': float(avg_words_p_sentence)
            }

##        def FleschReadingEase(self):
##            score = 0.0
##            score = 206.835 - (1.015 * (self.analyzedVars['avg_words_p_sentence'])) - (84.6 * (self.analyzedVars['syllable_cnt']/ self.analyzedVars['word_cnt']))
##            return round(score, 4)
        def FleschKincaidGradeLevel(self):
            score = 0.39 * (self.analyzedVars['avg_words_p_sentence']) + 11.8 * (self.analyzedVars['syllable_cnt']/ self.analyzedVars['word_cnt']) - 15.59
            return round(score, 4)

    param = {}
    if qid:
        sel = Question.objects.get(id=qid)
    content = sel.content
    item = Question.objects.get(id=qid)
    token = sel.content.split(';')
    ans = sel.std_answer.strip()
    display = []
    item= []
    #for each question part
    for t in token:
        c = t.strip().count("*")
        if c == 2:
            ans = ans.split('...')
            item = t.strip().replace("*", ans[0],1)
            item= item.replace("*", ans[1],1)
        else:
            item = t.strip().replace("*", ans)
        display.append(item)
        item = []
    q_display = display[0]
    text = q_display
    words = get_words(text)
    qdict = []
    cdict = []
    for word in words:
        qdict.append(count(word))
        cdict.append(len(word.decode("utf-8")))
    char_count = get_char_count(words)
    word_count = len(words)
    sentence_count = len(get_sentences(text))
    syllable_count = count_syllables(words)
    complexwords_count = float(count_complex_words(text))
    avg_words_p_sentence = float(word_count)/float(sentence_count)
    score = 0.39 * (avg_words_p_sentence) + 11.8 * (float(syllable_count)/ float(word_count)) - 15.59
    grade = round(score, 4)

    sent = tokenize.word_tokenize(text)
    sentence = tag.pos_tag(sent)
    grammar1 = r"""
    NP: {<.*>*}             # start by chunking everything
        }<[\.VI].*>+{       # chink any verbs, prepositions or periods
        <.*>}{<DT>          # separate on determiners
    PP: {<IN><NP>}          # PP = preposition + noun phrase
    VP: {<VB.*><NP|PP>*}    # VP = verb words + NPs and PPs
    """
    grammar2 = r"""
      NP: {<DT|JJ|NN.*>+}          # Chunk sequences of DT, JJ, NN
      PP: {<IN><NP>}               # Chunk prepositions followed by NP
      VP: {<VB.*><NP|PP|CLAUSE>+$} # Chunk verbs and their arguments
      CLAUSE: {<NP><VP>}           # Chunk NP, VP
      """
    grammar3 = r"""
    NP:                   # NP stage
      {<DT>?<JJ>*<NN>}    # chunk determiners, adjectives and nouns
      {<NNP>+}            # chunk proper nouns
    """
    cp1 = nltk.RegexpParser(grammar1)
    cp2 = nltk.RegexpParser(grammar2)
    cp3 = nltk.RegexpParser(grammar3)
    result1 = cp1.parse(sentence)
    result2 = cp2.parse(sentence)
    result3 = cp3.parse(sentence)
    ht1 =  result1.height()
    ht2 =  result2.height()
    ht3 =  result3.height()
    gradet = grade + ht1 + ht2 + ht3
    if gradet <= 14:
        diff_lvl=1
    elif gradet <= 16:
        diff_lvl=2
    elif gradet <= 18:
        diff_lvl=3
    elif gradet <= 20:
        diff_lvl=4
    else:
        diff_lvl=5

    return render(request, 'itemrtweb/diff.html', {'qid': qid, 'content':content,  'ans': ans, 'text':text, 'words':words, 'char_count': char_count,
                    'word_count':word_count, 'sentence_count':sentence_count,'syllable_count':syllable_count,'avg':avg_words_p_sentence,
                    'score':score,'diff': diff_lvl, 'grade': grade, 'gradet':gradet, 'item':sel, 'qdict':qdict, 'cdict':cdict,
                    'result1':result1,'ht1':ht1,'result2':result2,'ht2':ht2,'result3':result3,'ht3':ht3})

@login_required
def diffcount(request):
    topics = Topic.objects.all().order_by('position')
    list1={}
    list2={}
    list3={}
    list4={}
    list5={}
    listall={}

    for topic in topics:
        sel1 = Question.objects.all().filter(topic=topic).filter(difficulty=1).count()
        list1[topic.name]=sel1
        sel2 = Question.objects.all().filter(topic=topic).filter(difficulty=2).count()
        list2[topic.name]=sel2
        sel3 = Question.objects.all().filter(topic=topic).filter(difficulty=3).count()
        list3[topic.name]=sel3
        sel4 = Question.objects.all().filter(topic=topic).filter(difficulty=4).count()
        list4[topic.name]=sel4
        sel5 = Question.objects.all().filter(topic=topic).filter(difficulty=5).count()
        list5[topic.name]=sel5
        selall = Question.objects.all().filter(topic=topic).count()
        listall[topic.name]=selall

    diff1 = Question.objects.all().filter(difficulty=1).count()
    list1['all']=diff1
    diff2 = Question.objects.all().filter(difficulty=2).count()
    list2['all']=diff2
    diff3 = Question.objects.all().filter(difficulty=3).count()
    list3['all']=diff3
    diff4 = Question.objects.all().filter(difficulty=4).count()
    list4['all']=diff4
    diff5 = Question.objects.all().filter(difficulty=5).count()
    list5['all']=diff5
    diffall = Question.objects.all().count()
    listall['all']=diffall

    return render(request, 'itemrtweb/diffcount.html', {'topics': topics,'list1':list1,'list2':list2,'list3':list3,'list4':list4,'list5':list5,'listall':listall})

@login_required
def parser(request,qid=None):
    c = 0
    param = {}

    from nltk.tokenize import RegexpTokenizer

    TOKENIZER = RegexpTokenizer('(?u)\W+|\$[\d\.]+|\S+')
    SPECIAL_CHARS = ['.', ',', '!', '?']

    def get_char_count(words):
        characters = 0
        for word in words:
            characters += len(word.decode("utf-8"))
        return characters

    def get_words(text=''):
        words = []
        words = TOKENIZER.tokenize(text)
        filtered_words = []
        for word in words:
            if word in SPECIAL_CHARS or word == " ":
                pass
            else:
                new_word = word.replace(",","").replace(".","")
                new_word = new_word.replace("!","").replace("?","")
                filtered_words.append(new_word)
        return filtered_words

    def get_sentences(text=''):
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        sentences = tokenizer.tokenize(text)
        return sentences

    specialSyllables_en = """
    ok 2
    tv 2
    cd 2
    steely 2
    file 1
    hole 1
    mile 1
    pale 1
    pile 1
    pole 1
    role 1
    rule 1
    scale 1
    smile 1
    sole 1
    stale 1
    style 1
    tale 1
    vile 1
    while 1
    whole 1
    acre 2
    beauty 2
    being 2
    bureau 2
    business 2
    buyer 2
    carriage 2
    centre 2
    colleague 2
    colonel 2
    compile 2
    create 2
    cruel 2
    diet 2
    evening 2
    female 2
    fibre 2
    fluid 2
    framework 2
    going 2
    guideline 2
    household 2
    hundred 2
    judgement 2
    layer 2
    lifetime 2
    lion 2
    marriage 2
    mayor 2
    metre 2
    missile 2
    module 2
    movement 2
    pavement 2
    player 2
    poem 2
    prayer 2
    profile 2
    ratio 2
    rely 2
    safety 2
    schedule 2
    science 2
    spokesman 2
    squeaky 2
    statement 2
    technique 2
    achievement 3
    announcement 3
    area 3
    arrangement 3
    awareness 3
    barrier 3
    behaviour 3
    businessman 3
    carrier 3
    casual 3
    catalogue 3
    champion 3
    coincide 3
    creation 3
    criticism 3
    dialogue 3
    employee 3
    employer 3
    engagement 3
    equation 3
    excitement 3
    graduate 3
    idea 3
    improvement 3
    influence 3
    involvement 3
    loyalty 3
    management 3
    measurement 3
    mechanism 3
    molecule 3
    musician 3
    organism 3
    parliament 3
    poetry 3
    policeman 3
    reaction 3
    realise 3
    realize 3
    reassure 3
    recipe 3
    reinforce 3
    replacement 3
    requirement 3
    retirement 3
    shareholder 3
    situate 3
    suicide 3
    supplier 3
    theatre 3
    theory 3
    united 3
    video 3
    advertisement 4
    anxiety 4
    capitalism 4
    casualty 4
    championship 4
    constituent 4
    criterion 4
    evaluate 4
    experience 4
    hierarchy 4
    initiate 4
    negotiate 4
    politician 4
    reality 4
    situation 4
    society 4
    differentiate 5
    evaluation 5
    ideology 5
    individual 5
    initiation 5
    negotiation 5
    cheque 1
    quaint 1
    queen 1
    queer 1
    squeeze 1
    tongue 1
    mimes 1
    ms 1
    h'm 1
    brutes 1
    lb 1
    effaces 2
    mr 2
    mrs 2
    moustaches 2
    dr 2
    sr 2
    jr 2
    mangroves 2
    truckle 2
    fringed 2
    messieurs 2
    poleman 2
    sombre 2
    sidespring 2
    gravesend 2
    60 2
    greyish 2
    anyone 3
    amusement 3
    shamefully 3
    sepulchre 3
    hemispheres 3
    veriest 3
    satiated 4
    sailmaker 4
    etc 4
    unostentatious 5
    Propitiatory 6
    """
    fallback_cache = {}

    fallback_subsyl = ["cial", "tia", "cius", "cious", "giu", "ion", "iou",
                       "sia$", ".ely$"]

    fallback_addsyl = ["ia", "riet", "dien", "iu", "io", "ii",
                       "[aeiouym]bl$", "mbl$",
                       "[aeiou]{3}",
                       "^mc", "ism$",
                       "(.)(?!\\1)([^aeiouy])\\ll$",
                       "[^l]lien",
                       "^coad.", "^coag.", "^coal.", "^coax.",
                       "(.)(?!\\1)[gq]ua(.)(?!\\2)[aeiou]",
                       "dnt$"]


    # Compile our regular expressions
    for i in range(len(fallback_subsyl)):
        fallback_subsyl[i] = re.compile(fallback_subsyl[i])
    for i in range(len(fallback_addsyl)):
        fallback_addsyl[i] = re.compile(fallback_addsyl[i])

    def _normalize_word(word):
        return word.strip().lower()

    # Read our syllable override file and stash that info in the cache
    for line in specialSyllables_en.splitlines():
        line = line.strip()
        if line:
            toks = line.split()
            assert len(toks) == 2
            fallback_cache[_normalize_word(toks[0])] = int(toks[1])

    def count(word):
        word = _normalize_word(word)
        if not word:
            return 0

        # Check for a cached syllable count
        count = fallback_cache.get(word, -1)
        if count > 0:
            return count

        # Remove final silent 'e'
        if word[-2:] == "le":
            word = word+"s" #-le

        elif word[-2:] == "ed":
            word = word[:-2] #problematic -ed

        elif word[-1] == "e":
            word = word[:-1]


        # Count vowel groups
        count = 0
        prev_was_vowel = 0
        for c in word:
            is_vowel = c in ("a", "e", "i", "o", "u", "y")
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Add & subtract syllables
        for r in fallback_addsyl:
            if r.search(word):
                count += 1
        for r in fallback_subsyl:
            if r.search(word):
                count -= 1

        #for words with silent e +1 e.g. me, she, he, the
        if count == 0:
            count = 1

        # Cache the syllable count
        fallback_cache[word] = count

        return count

    def count_syllables(words):
        syllableCount = 0
        for word in words:
            syllableCount += count(word)
        return syllableCount

    def count_complex_words(text=''):
        words = get_words(text)
        sentences = get_sentences(text)
        complex_words = 0
        found = False
        cur_word = []

        for word in words:
            cur_word.append(word)
            if count_syllables(cur_word)>= 3:

                #Checking proper nouns. If a word starts with a capital letter
                #and is NOT at the beginning of a sentence we don't add it
                #as a complex word.
                if not(word[0].isupper()):
                    complex_words += 1
                else:
                    for sentence in sentences:
                        if str(sentence).startswith(word):
                            found = True
                            break
                    if found:
                        complex_words += 1
                        found = False

            cur_word.remove(word)
        return complex_words


    class Readability:
        analyzedVars = {}

        def __init__(self, text):
            self.analyze_text(text)

        def analyze_text(self, text):
            words = get_words(text)
            char_count = get_char_count(words)
            word_count = len(words)
            sentence_count = len(get_sentences(text))
            syllable_count = count_syllables(words)
            complexwords_count = count_complex_words(text)
            avg_words_p_sentence = word_count/sentence_count

            self.analyzedVars = {
                'words': words,
                'char_cnt': float(char_count),
                'word_cnt': float(word_count),
                'sentence_cnt': float(sentence_count),
                'syllable_cnt': float(syllable_count),
                'complex_word_cnt': float(complexwords_count),
                'avg_words_p_sentence': float(avg_words_p_sentence)
            }

##        def FleschReadingEase(self):
##            score = 0.0
##            score = 206.835 - (1.015 * (self.analyzedVars['avg_words_p_sentence'])) - (84.6 * (self.analyzedVars['syllable_cnt']/ self.analyzedVars['word_cnt']))
##            return round(score, 4)
        def FleschKincaidGradeLevel(self):
            score = 0.39 * (self.analyzedVars['avg_words_p_sentence']) + 11.8 * (self.analyzedVars['syllable_cnt']/ self.analyzedVars['word_cnt']) - 15.59
            return round(score, 4)

    param = {}
    text={}
    ht1 = {}
    ht2 = {}
    ht3= {}
    words={}
    char_count={}
    word_count = {}
    sentence_count={}
    syllable_count={}
    complexwords_count={}
    avg_words_p_sentence={}
    grade={}
    diff={}
    selall = Question.objects.all()
    for sel in selall:
        content = sel.content
        token = sel.content.split(';')
        ans = sel.std_answer.strip()
        display = []
        item= []
        #for each question part
        for t in token:
            c = t.strip().count("*")
            if c == 2:
                ans = ans.split('...')
                item = t.strip().replace("*", ans[0],1)
                item= item.replace("*", ans[1],1)
            else:
                item = t.strip().replace("*", ans)
            display.append(item)
            item = []
        q_display = display[0]
        w = get_words(q_display)
        text[sel.id] = q_display
        words[sel.id] = get_words(q_display)
##        qdict = []
##        cdict = []
##        for word in words:
##            qdict.append(count(word))
##            cdict.append(len(word.decode("utf-8")))
        char_count[sel.id] = get_char_count(w)
        word_count[sel.id] = len(w)
        w_count = len(w)
        sentence_count[sel.id] = len(get_sentences(q_display))
        s_count= len(get_sentences(q_display))
        sy_count = count_syllables(w)
        syllable_count[sel.id] = count_syllables(w)
        complexwords_count[sel.id] = float(count_complex_words(q_display))
        avg_words_p_sentence = float(w_count)/float(s_count)
        score = 0.39 * (avg_words_p_sentence) + 11.8 * (float(sy_count)/ float(w_count)) - 15.59
        grade[sel.id] = round(score, 4)
        g = round(score, 4)
        if g <= 3:
            diff_lvl=1
        elif g <= 5:
            diff_lvl=2
        elif g <= 7:
            diff_lvl=3
        elif g <= 9:
            diff_lvl=4
        else:
            diff_lvl=5
        diff[sel.id] = diff_lvl
        sent = tokenize.word_tokenize(q_display)
        sentence = tag.pos_tag(sent)
        grammar1 = r"""
        NP: {<.*>*}             # start by chunking everything
            }<[\.VI].*>+{       # chink any verbs, prepositions or periods
            <.*>}{<DT>          # separate on determiners
        PP: {<IN><NP>}          # PP = preposition + noun phrase
        VP: {<VB.*><NP|PP>*}    # VP = verb words + NPs and PPs
        """
        grammar2 = r"""
          NP: {<DT|JJ|NN.*>+}          # Chunk sequences of DT, JJ, NN
          PP: {<IN><NP>}               # Chunk prepositions followed by NP
          VP: {<VB.*><NP|PP|CLAUSE>+$} # Chunk verbs and their arguments
          CLAUSE: {<NP><VP>}           # Chunk NP, VP
          """
        grammar3 = r"""
        NP:                   # NP stage
          {<DT>?<JJ>*<NN>}    # chunk determiners, adjectives and nouns
          {<NNP>+}            # chunk proper nouns
        """
        cp1 = nltk.RegexpParser(grammar1)
        cp2 = nltk.RegexpParser(grammar2)
        cp3 = nltk.RegexpParser(grammar3)
        result1 = cp1.parse(sentence)
        result2 = cp2.parse(sentence)
        result3 = cp3.parse(sentence)
        ht1[sel.id] =  result1.height()
        ht2[sel.id] =  result2.height()
        ht3[sel.id] =  result3.height()

    return render(request, 'itemrtweb/parser.html', {'qid': qid, 'content':content,  'ans': ans, 'text':text, 'char_count': char_count,
                    'word_count':word_count, 'sentence_count':sentence_count,'syllable_count':syllable_count,'complexwords_count':complexwords_count,'avg':avg_words_p_sentence,
                    'score':score,'diff': diff, 'grade': grade, 'item':sel,'result1':result1,'ht1':ht1,'result2':result2,'ht2':ht2,'result3':result3,'ht3':ht3,'selall':selall})

@login_required
def question(request,qid=None):
    from nltk.tokenize import RegexpTokenizer

    TOKENIZER = RegexpTokenizer('(?u)\W+|\$[\d\.]+|\S+')
    SPECIAL_CHARS = ['.', ',', '!', '?']

    def get_words(text=''):
        words = []
        words = TOKENIZER.tokenize(text)
        filtered_words = []
        for word in words:
            if word in SPECIAL_CHARS or word == " ":
                pass
            else:
                new_word = word.replace(",","").replace(".","")
                new_word = new_word.replace("!","").replace("?","")
                filtered_words.append(new_word)
        return filtered_words

    param = {}
    text={}
    sentence={}
    selall = Question.objects.all()
    for sel in selall:
        content = sel.content
        token = sel.content.split(';')
        ans = sel.std_answer.strip()
        display = []
        item= []
        #for each question part
        for t in token:
            c = t.strip().count("*")
            if c == 2:
                ans = ans.split('...')
                item = t.strip().replace("*", ans[0],1)
                item= item.replace("*", ans[1],1)
            else:
                item = t.strip().replace("*", ans)
            display.append(item)
            item = []
        q_display = display[0]
        w = get_words(q_display)
        text[sel.id] = q_display
        sent = tokenize.word_tokenize(q_display)
        puretagged = tag.pos_tag(sent)
        sentence[sel.id] = ' '.join([tup[1] for tup in puretagged])

    return render(request, 'itemrtweb/question.html', {'qid': qid, 'content':content, 'selall':selall, 'text':text, 'sentence':sentence})

@user_passes_test(lambda u: u.is_staff)
def learncontrol(request, topic_id=None):
    # Record usage for stats purpose
    page = "learn_management"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Init
    filtered_questions = None
    selected_topic = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # int the selected topic
    if topic_id:
        selected_topic = Topic.objects.all().get(id=int(topic_id))

    if topic_id:
        # Retrieve questions for this topic
        filtered_questions = Learn.objects.all().filter(topic=topic_id)

    return render(request, 'itemrtweb/manage.learn.home.html', {'topics': topics, 'selected_topic': selected_topic, 'questions': filtered_questions})

@user_passes_test(lambda u: u.is_staff)
def learnedit(request, learn_id=None):
    # Init
    selected_learn = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if learn_id:
        selected_learn = Learn.objects.all().get(id=int(learn_id))

    if request.method == 'POST':
        form = forms.LearnForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Check if question exists or need to create new

            # INITIALISE - Get from POST
            # Insert new tag
            learn = Learn(
            id = learn_id,
            topic = form.cleaned_data['topic'],
            description=form.cleaned_data['description'])
            learn.save()

            # Question inserted successfully!
            return redirect('/control/learn/topic/'+ str(learn.id))

        # Reply regardless valid
        return render(request, 'itemrtweb/manage.learn.insert.html', {'form': form, 'topics': topics, 'selected_learn': selected_learn})
    else:
        # Check if question exists or give blank form
        if selected_learn:
            # Load existing question into a form
            form = forms.LearnForm(initial={'topic':selected_learn.topic,  'description':selected_learn.description})

        else:
            # Display new form for user to fill in
            form = forms.LearnForm()

    return render(request, 'itemrtweb/manage.learn.insert.html', {'form': form, 'topics': topics, 'selected_learn': selected_learn})

@user_passes_test(lambda u: u.is_staff)
def learnview(request, learn_id=None):
    # Init
    filtered_questions = None
    selected_learn = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # int the selected topic
    if learn_id:
        selected_learn = Topic.objects.all().get(id=int(learn_id))

    if learn_id:
        # Retrieve questions for this topic
        filtered_questions = Learn.objects.all().filter(topic=learn_id)

    return render(request, 'itemrtweb/manage.learn.home.html', {'topics': topics, 'selected_learn': selected_learn, 'questions': filtered_questions})


##from reportlab.pdfgen import canvas
##from django.http import HttpResponse
##
##def printpdf(request):
##    # Create the HttpResponse object with the appropriate PDF headers.
##    response = HttpResponse(content_type='application/pdf')
##    response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'
##
##    # Create the PDF object, using the response object as its "file."
##    p = canvas.Canvas(response)
##
##    # Draw things on the PDF. Here's where the PDF generation happens.
##    # See the ReportLab documentation for the full list of functionality.
##    p.drawString(100, 100, "Hello world.")
##
##    # Close the PDF object cleanly, and we're done.
##    p.showPage()
##    p.save()
##    return response

##@user_passes_test(lambda u: u.is_staff)
##def tagcontrol(request, topic_id=None):
##    # Record usage for stats purpose
##    page = "tag_management"
##    # Never accessed this page before, or last access was more than 10 mins ago
##    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
##        usage = UserUsage(user=request.user, page=page)
##        usage.save()
##        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
##    # End usage recording
##
##    count = {}
##    topics = Topic.objects.all()
##    for topic in topics:
##        count[topic.id]= Tag.objects.filter(topic=topic).count()
##
##    # Init
##    filtered_questions = None
##    selected_topic = None
##
##    # Obtain the list of topics
##    topics = Topic.objects.all().order_by('position')
##    all_tags = Tag.objects.all()
##
##    # int the selected topic
##    if topic_id:
##        selected_topic = Topic.objects.all().get(id=int(topic_id))
##
##    if topic_id:
##        # Retrieve questions for this topic
##        filtered_questions = Tag.objects.all().filter(topic=topic_id)
##
##    return render(request, 'itemrtweb/manage.tag.home.html', {'topics': topics, 'selected_topic': selected_topic, 'questions': filtered_questions, 'all_tags': all_tags, 'count':count})
##
##@user_passes_test(lambda u: u.is_staff)
##def taglist(request):
##    # Obtain the list of topics
##    topics = Topic.objects.all().order_by('position')
##    all_tags = Tag.objects.all()
##
##    count = {}
##    topics = Topic.objects.all()
##    for topic in topics:
##        count[topic.id]= Tag.objects.filter(topic=topic).count()
##
##    filtered_tag= None
##    tags = None
##
##    # Filter by tags given from input
##    if request.GET.get("tags") != None:
##        tags = request.GET.getlist("tags")
##        for tag in tags:
##                filtered_tag = Tag.objects.get(name=tag)
##
##
##    return render(request, 'itemrtweb/manage.tag.list.html', {'topics': topics,'filtered_tag':filtered_tag, 'all_tags':all_tags, 'count':count})
##
##@user_passes_test(lambda u: u.is_staff)
##def tagview(request, tag_id=None):
##    # Init
##    filtered_questions = None
##    selected_tag = None
##    count = 0
##
##    # int the selected topic
##    if tag_id:
##        selected_tag = Tag.objects.get(id=tag_id)
##        name = str(selected_tag.name).strip()
##        filtered_questions = QuestionTag.objects.all().filter(tag=tag_id)
##        count = filtered_questions.count()
##
##    return render(request, 'itemrtweb/manage.tag.view.html', {'tag': selected_tag, 'questions': filtered_questions, 'count':count})
##
##@user_passes_test(lambda u: u.is_staff)
##def tagdelete(request, tag_id=None):
##    # Init
##    selected_tag = None
##
##    # Objectify the selected question
##    if tag_id:
##        selected_tag = Tag.objects.all().get(id=int(tag_id))
##
##    # Check if question exists otherwise redirect to question list
##    if selected_tag:
##        question_tags = QuestionTag.objects.filter(tag__id=(tag_id))
##        for tagged in question_tags:
##            tagged.delete()
##        selected_tag.delete()
##
##        return redirect('/control/tag/?msg=Tag has been deleted')
##    else:
##        # Redirect user back to question lists
##        return redirect('/control/tag/')
##
##@user_passes_test(lambda u: u.is_staff)
##def taginsert(request, tag_id=None):
##    # Init
##    selected_tag = None
##
##    # Obtain the list of topics
##    topics = Topic.objects.all().order_by('position')
##
##    # Objectify the selected question
##    if tag_id:
##        selected_tag = Tag.objects.all().get(id=int(question_id))
##
##    if request.method == 'POST':
##        form = forms.InsertTagForm(request.POST) # Bind to user submitted form
##        if form.is_valid():
##            # Check if question exists or need to create new
##
##            # INITIALISE - Get from POST
##            # Insert new tag
##            tag = Tag(
##            topic = form.cleaned_data['topic'],
##            name = form.cleaned_data['name'],
##            description=form.cleaned_data['description'])
##            tag.save()
##
##            keyword = tag
##            keywordfound = Question.objects.filter(topic=keyword.topic).filter(Q(content__iregex='[[:<:]]' + keyword.name + '[[:>:]]')|Q(choice__iregex='[[:<:]]' + keyword.name + '[[:>:]]'))  #search for keyword
##            for kf in keywordfound:
##                #create new tag relationship
##                newtag = QuestionTag(question=kf, tag=keyword)
##                newtag.save()
##
##            # Question inserted successfully!
##            return redirect('/control/tag/view/'+ str(tag.id))
##
##        # Reply regardless valid
##        return render(request, 'itemrtweb/manage.question.insert.html', {'form': form, 'topics': topics, 'selected_tag': selected_tag})
##    else:
##        # Check if question exists or give blank form
##        if selected_tag:
##            # Load existing question into a form
##            form = forms.InsertTagForm(initial={'topic':selected_tag.topic, 'name':selected_tag.name, 'description':selected_tag.description})
##
##        else:
##            # Display new form for user to fill in
##            form = forms.InsertTagForm()
##
##    return render(request, 'itemrtweb/manage.tag.insert.html', {'form': form, 'topics': topics,  'selected_tag': selected_tag})
##
##@user_passes_test(lambda u: u.is_staff)
##def tagedit(request, tag_id=None):
##    # Init
##    selected_tag = None
##
##    # Obtain the list of topics
##    topics = Topic.objects.all().order_by('position')
##
##    # Objectify the selected question
##    if tag_id:
##        selected_tag = Tag.objects.all().get(id=int(question_id))
##
##    if request.method == 'POST':
##        form = forms.InsertTagForm(request.POST) # Bind to user submitted form
##        if form.is_valid():
##            # Check if question exists or need to create new
##
##            # INITIALISE - Get from POST
##            # Insert new tag
##            tag = Tag(
##            topic = form.cleaned_data['topic'],
##            name = form.cleaned_data['name'],
##            description=form.cleaned_data['description'])
##            tag.save()
##
##            keyword = tag
##            keywordfound = Question.objects.filter(topic=keyword.topic).filter(Q(content__iregex='[[:<:]]' + keyword.name + '[[:>:]]')|Q(choice__iregex='[[:<:]]' + keyword.name + '[[:>:]]'))  #search for keyword
##            for kf in keywordfound:
##                #create new tag relationship
##                newtag = QuestionTag(question=kf, tag=keyword)
##                newtag.save()
##
##            # Question inserted successfully!
##            return redirect('/control/tag/view/'+ str(tag.id))
##
##        # Reply regardless valid
##        return render(request, 'itemrtweb/manage.tag.insert.html', {'form': form, 'topics': topics, 'selected_tag': selected_tag})
##    else:
##        # Check if question exists or give blank form
##        if selected_tag:
##            # Load existing question into a form
##            form = forms.InsertTagForm(initial={'topic':selected_tag.topic, 'name':selected_tag.name, 'description':selected_tag.description})
##
##        else:
##            # Display new form for user to fill in
##            form = forms.InsertTagForm()
##
##    return render(request, 'itemrtweb/manage.tag.insert.html', {'form': form, 'topics': topics,  'selected_tag': selected_tag, 'count':count})
##

@user_passes_test(lambda u: u.is_staff)
def tagcontrol(request, topic_id=None):
    # Record usage for stats purpose
    page = "tag_management"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    count = {}

    topics = Topic.objects.all()
    for topic in topics:
        count[topic.id] = Tag.objects.filter(topic=topic).count()
    # Init
    filtered_tags = None
    selected_topic = None
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    all_tags = Tag.objects.all()
    # int the selected topic
    if topic_id:
        selected_topic = Topic.objects.all().get(id=int(topic_id))
        filtered_tags = Tag.objects.all().filter(topic=topic_id)
    return render(request, 'itemrtweb/manage.tag.home.html', {'topics': topics, 'selected_topic': selected_topic, 'filtered_tags': filtered_tags, 'all_tags': all_tags, 'count':count})

@user_passes_test(lambda u: u.is_staff)
def taglist(request):
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    all_tags = Tag.objects.all()

    count = {}
    topics = Topic.objects.all()
    for topic in topics:
        count[topic.id]= Tag.objects.filter(topic=topic).count()

    filtered_tag= None
    tags = None

    # Filter by tags given from input
    if request.GET.get("tags") != None:
        tags = request.GET.getlist("tags")
        for tag in tags:
                filtered_tag = Tag.objects.get(name=tag)
                ##filtered_questions = QuestionTag.objects.all().filter(tag=filtered_tag.id)
                ##filtered_tag.count = filtered_questions.count()

    return render(request, 'itemrtweb/manage.tag.list.html', {'topics': topics,'filtered_tag':filtered_tag, 'all_tags':all_tags, 'count':count})

@user_passes_test(lambda u: u.is_staff)
def conceptcontrol(request, topic_id=None):
    # Record usage for stats purpose
    page = "concept_management"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    count = {}

    topics = Topic.objects.all()
    for topic in topics:
        count[topic.id]= Concept.objects.filter(topic=topic).count()
    # Init
    selected_topic = None
    filtered_concept = None
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    all_concept = Concept.objects.all()
    # int the selected topic
    if topic_id:
        selected_topic = Topic.objects.all().get(id=int(topic_id))
        filtered_concept = Concept.objects.all().filter(topic=topic_id)
    return render(request, 'itemrtweb/manage.concept.home.html', {'topics': topics, 'selected_topic': selected_topic,  'filtered_concept':filtered_concept, 'all_concept': all_concept, 'count':count})

@user_passes_test(lambda u: u.is_staff)
def conceptview(request, tag_id=None):
    # Init
    filtered_questions = None
    selected_tag = None
    selected_concept = None
    count = 0

    # int the selected topic
    if tag_id:
        selected_concept = Concept.objects.get(id=tag_id)
        selected_tag = selected_concept.words.all()
        filtered_questions = QuestionConcept.objects.all().filter(concept=tag_id)
        count = filtered_questions.count()

    return render(request, 'itemrtweb/manage.concept.view.html', {'concept': selected_concept, 'tag': selected_tag, 'questions': filtered_questions, 'count':count})

@user_passes_test(lambda u: u.is_staff)
def tagview(request, tag_id=None):
    # Init
    filtered_questions = None
    selected_tag = None
    count = 0

    # int the selected topic
    if tag_id:
        selected_tag = Tag.objects.get(id=tag_id)
        name = str(selected_tag.name).strip()
        filtered_questions = QuestionTag.objects.all().filter(tag=tag_id)
        count = filtered_questions.count()

    return render(request, 'itemrtweb/manage.tag.view.html', {'tag': selected_tag, 'questions': filtered_questions, 'count':count})

@user_passes_test(lambda u: u.is_staff)
def tagdelete(request, tag_id=None):
    # Init
    selected_tag = None

    # Objectify the selected question
    if tag_id:
        selected_tag = Tag.objects.all().get(id=int(tag_id))

    # Check if question exists otherwise redirect to question list
    if selected_tag:
        question_tags = QuestionTag.objects.filter(tag__id=(tag_id))
        for tagged in question_tags:
            tagged.delete()
        selected_tag.delete()

        return redirect('/control/tag/?msg=Tag has been deleted')
    else:
        # Redirect user back to question lists
        return redirect('/control/tag/')

@user_passes_test(lambda u: u.is_staff)
def conceptdelete(request, tag_id=None):
    # Init
    selected_tag = None

    # Objectify the selected question
    if tag_id:
        selected_tag = Concept.objects.all().get(id=int(tag_id))

    # Check if question exists otherwise redirect to question list
    if selected_tag:
        question_tags = QuestionConcept.objects.filter(concept__id=(tag_id))
        for tagged in question_tags:
            tagged.delete()
        selected_tag.delete()

        return redirect('/control/concept/?msg=Tag has been deleted')
    else:
        # Redirect user back to question lists
        return redirect('/control/concept/')

@user_passes_test(lambda u: u.is_staff)
def taginsert(request, tag_id=None):
    # Init
    selected_tag = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if tag_id:
        selected_tag = Tag.objects.all().get(id=int(question_id))

    if request.method == 'POST':
        form = forms.InsertTagForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Check if question exists or need to create new

            # INITIALISE - Get from POST
            # Insert new tag
            tag = Tag(
            topic = form.cleaned_data['topic'],
            name = form.cleaned_data['name'],
            description=form.cleaned_data['description'])
            tag.save()

            keyword = tag
            keywordfound = Question.objects.filter(topic=keyword.topic).filter(Q(content__iregex='[[:<:]]' + keyword.name + '[[:>:]]')|Q(choice__iregex='[[:<:]]' + keyword.name + '[[:>:]]'))  #search for keyword
            for kf in keywordfound:
                #create new tag relationship
                newtag = QuestionTag(question=kf, tag=keyword)
                newtag.save()

            # Question inserted successfully!
            return redirect('/control/tag/view/'+ str(tag.id))

        # Reply regardless valid
        return render(request, 'itemrtweb/manage.tag.insert.html', {'form': form, 'topics': topics, 'selected_tag': selected_tag})
    else:
        # Check if question exists or give blank form
        if selected_tag:
            # Load existing question into a form
            form = forms.InsertTagForm(initial={'topic':selected_tag.topic, 'name':selected_tag.name, 'description':selected_tag.description})

        else:
            # Display new form for user to fill in
            form = forms.InsertTagForm()

    return render(request, 'manage.tag.insert.html', {'form': form, 'topics': topics,  'selected_tag': selected_tag})

@user_passes_test(lambda u: u.is_staff)
def conceptinsert(request, tag_id=None):
    # Init
    selected_tag = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if tag_id:
        selected_tag = Tag.objects.all().get(id=int(question_id))

    if request.method == 'POST':
        form = forms.InsertConceptForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Check if question exists or need to create new

            # INITIALISE - Get from POST
            # Insert new concept tag
            tag = Concept(
            topic = form.cleaned_data['topic'],
            name = form.cleaned_data['name'],
            description=form.cleaned_data['description'])
            tag.save()

            concept = tag
            tags = concept.words.all()
            if len(tags)>1:
                conceptfound = Question.objects.filter(topic=topic).filter(reduce(lambda x, y: x | y, [Q(std_answer__iregex='[[:<:]]' + tag.name + '[[:>:]]') for tag in tags]))
            else:
                for tag in tags:
                    conceptfound = Question.objects.filter(topic=topic).filter(Q(std_answer__iregex='[[:<:]]' + tag.name + '[[:>:]]'))
            if (concept.id == 20 or concept.id ==60):
                print conceptfound
            if len(tags)>0:
                for kf in conceptfound:
                    #create new tag relationship
                    newconcept = QuestionConcept(question=kf, concept=concept)
                    newconcept.save()

            # Question inserted successfully!
            return redirect('/control/concept/view/'+ str(tag.id))

        # Reply regardless valid
        return render(request, 'itemrtweb/manage.concept.insert.html', {'form': form, 'topics': topics, 'selected_tag': selected_tag})
    else:
        # Check if question exists or give blank form
        if selected_tag:
            # Load existing question into a form
            form = forms.InsertConceptForm(initial={'topic':selected_tag.topic, 'name':selected_tag.name, 'description':selected_tag.description})

        else:
            # Display new form for user to fill in
            form = forms.InsertConceptForm()

    return render(request, 'itemrtweb/manage.concept.insert.html', {'form': form, 'topics': topics,  'selected_tag': selected_tag})

@user_passes_test(lambda u: u.is_staff)
def tagedit(request, tag_id=None):
    # Init
    selected_tag = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if tag_id:
        selected_tag = Tag.objects.all().get(id=tag_id)

    if request.method == 'POST':
        form = forms.InsertTagForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Check if question exists or need to create new

            # INITIALISE - Get from POST
            # Insert new tag
            tag = Tag(
            id = tag_id,
            topic = form.cleaned_data['topic'],
            name = form.cleaned_data['name'],
            description=form.cleaned_data['description'])
            tag.save()

            keyword = tag
            keywordfound = Question.objects.filter(topic=keyword.topic).filter(Q(std_answer__iregex='[[:<:]]' + keyword.name + '[[:>:]]'))  #search for keyword
            for kf in keywordfound:
                #create new tag relationship
                newtag = QuestionTag(question=kf, tag=keyword)
                newtag.save()
            return redirect('/control/tag/topic/'+ str(tag.topic_id))

        # Reply regardless valid
        return render(request, 'itemrtweb/manage.tag.edit.html', {'form': form, 'topics': topics, 'selected_tag': selected_tag})
    else:
        # Check if question exists or give blank form
        if selected_tag:
            # Load existing question into a form
            form = forms.InsertTagForm(initial={'topic':selected_tag.topic, 'name':selected_tag.name, 'description':selected_tag.description})

        else:
            # Display new form for user to fill in
            form = forms.InsertTagForm()

    return render(request, 'itemrtweb/manage.tag.edit.html', {'form': form, 'topics': topics,  'selected_tag': selected_tag})

@user_passes_test(lambda u: u.is_staff)
def conceptedit(request, tag_id=None):
    # Init
    selected_tag = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if tag_id:
        selected_tag = Concept.objects.all().get(id=tag_id)

    if request.method == 'POST':
        form = forms.InsertTagForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Check if question exists or need to create new

            # INITIALISE - Get from POST
            # Insert new tag
            tag = Concept(
            id = tag_id,
            topic = form.cleaned_data['topic'],
            name = form.cleaned_data['name'],
            description=form.cleaned_data['description'])
            tag.save()

            conceptfound = None
            tags = selected_tag.words.all()
            if len(tags)>1:
                conceptfound = Question.objects.filter(topic=selected_tag.topic).filter(reduce(lambda x, y: x | y, [Q(std_answer__iregex='[[:<:]]' + t.name + '[[:>:]]') for t in tags]))
            elif len(tags)==1:
                for t in tags:
                    conceptfound = Question.objects.filter(topic=selected_tag.topic).filter(Q(std_answer__iregex='[[:<:]]' + t.name + '[[:>:]]'))
            if conceptfound:
                for kf in conceptfound:
                    #create new tag relationship
                    newconcept = QuestionConcept(question=kf, concept=selected_tag)
                    newconcept.save()
            return redirect('/control/concept/topic/'+ str(tag.topic_id))
        # Reply regardless valid
        return render(request, 'itemrtweb/manage.concept.edit.html', {'form': form, 'topics': topics, 'selected_tag': selected_tag})
    else:
        # Check if question exists or give blank form
        if selected_tag:
            # Load existing question into a form
            form = forms.InsertTagForm(initial={'topic':selected_tag.topic, 'name':selected_tag.name, 'description':selected_tag.description})

        else:
            # Display new form for user to fill in
            form = forms.InsertTagForm()

    return render(request, 'itemrtweb/manage.concept.edit.html', {'form': form, 'topics': topics,  'selected_tag': selected_tag})

@user_passes_test(lambda u: u.is_staff)
def topicview(request, topic_id=None):
    # Init
    selected_topic = None

    # Obtain the list of topics
    topics = Topic.objects.all().filter(is_active=True).order_by('position')
    count = topics.count()

    return render(request, 'itemrtweb/manage.topic.html', {'topics': topics, 'count':count})

@user_passes_test(lambda u: u.is_staff)
def topicup(request, topic_id=None):
    # Init
    selected_topic = None
    selected_topic_B = None

     # Objectify the selected question
    if topic_id:
        selected_topic = Topic.objects.all().get(position=int(topic_id))
        selected_topic_B = Topic.objects.all().get(position=int(topic_id)-1)
        pos = int(topic_id)

    # Check if question exists otherwise redirect to question list
    if selected_topic:
        # Hide question and save. Then give message to user
        selected_topic.position = pos-1
        selected_topic_B.position = pos
        selected_topic.save()
        selected_topic_B.save()

        return redirect('/control/topic/')

@user_passes_test(lambda u: u.is_staff)
def topicdown(request, topic_id=None):
    # Init
    selected_topic = None
    selected_topic_B = None

     # Objectify the selected question
    if topic_id:
        selected_topic = Topic.objects.all().get(position=int(topic_id))
        selected_topic_B = Topic.objects.all().get(position=int(topic_id)+1)
        pos = int(topic_id)

    # Check if question exists otherwise redirect to question list
    if selected_topic:
        # Hide question and save. Then give message to user
        selected_topic.position = pos+1
        selected_topic_B.position = pos
        selected_topic.save()
        selected_topic_B.save()

        return redirect('/control/topic/')
@user_passes_test(lambda u: u.is_staff)
def topicdelete(request, topic_id=None):
    # Init
    selected_topic = None

    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')

    # Objectify the selected question
    if topic_id:
        selected_topic = Topic.objects.all().get(id=int(topic_id))

    # Check if question exists otherwise redirect to question list
    if selected_topic:
        # Hide question and save. Then give message to user
        selected_topic.is_active = False
        selected_topic.position=99
        selected_topic.save()

        return redirect('/control/topic/?msg=Topic has been deleted')
    else:
        # Redirect user back to question lists
        return redirect('/control/topic/')

@user_passes_test(lambda u: u.is_staff)
def topicinsert(request, topic_id=None):
    # Init
    selected_topic = None

    # Obtain the list of topics
    topics = Topic.objects.all().filter(is_active='True').order_by('position')
    count = topics.count()

    if request.method == 'POST':
        form = forms.InsertTopicForm(request.POST) # Bind to user submitted form
        if form.is_valid():

            topic = Topic(
            name = form.cleaned_data['name'],
            position=count+1)
            topic.save()

            # Question inserted successfully!
            return redirect('/control/topic/')
        return redirect('/control/topic/')

def leaderboard(request, topic_id=None):
    #Init Mode
    selected_mode = 2
    # Record usage for stats purpose
    page = "leaderboard"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Init
    selected_topic = None
    all_user = User.objects.all()
    selected_user = request.user
    # Obtain the list of topics
    topics = Topic.objects.all().order_by('position')
    rank = {}

    # int the selected topic
    if topic_id:
        selected_topic = Topic.objects.all().get(id=int(topic_id))
        for user in all_user:
            user.all = 0
            user.score = 0
            user.catscore = 0
            user.paperscore = 0
            user.all = Response.objects.filter(user=user).filter(question__topic__id = topic_id).count()
            user.cat = Response.objects.filter(user=user).filter(question__topic__id = topic_id).filter(assessment__id=1).count()
            user.paper = Response.objects.filter(user=user).filter(question__topic__id = topic_id).filter(assessment__id=5).count()
            if user.all > 0:
                user.score = Decimal (Response.objects.filter(user=user).filter(correctness=1).filter(question__topic__id = topic_id).count()) * 100 / Decimal (Response.objects.filter(user=user).filter(question__topic__id = topic_id).count() )
            if user.cat > 0:
                user.catscore = Decimal (Response.objects.filter(user=user).filter(correctness=1).filter(question__topic__id = topic_id).filter(assessment__id=1).count()) * 100 / Decimal (Response.objects.filter(user=user).filter(question__topic__id = topic_id).filter(assessment__id=1).count() )
            if user.paper> 0:
                user.paperscore = Decimal (Response.objects.filter(user=user).filter(correctness=1).filter(question__topic__id = topic_id).filter(assessment__id=5).count()) * 100 / Decimal (Response.objects.filter(user=user).filter(question__topic__id = topic_id).filter(assessment__id=5).count() )
    else:
        for user in all_user:
            user.all = 0
            user.score = 0
            user.catscore = 0
            user.paperscore = 0
            user.all = Response.objects.filter(user=user).count()
            user.cat = Response.objects.filter(user=user).filter(assessment__id=1).count()
            user.paper = Response.objects.filter(user=user).filter(assessment__id=5).count()
            if user.all > 0:
                user.score = Decimal (Response.objects.filter(user=user).filter(correctness=1).count()) * 100 / Decimal (Response.objects.filter(user=user).count() )
            if user.cat > 0:
                user.catscore = Decimal (Response.objects.filter(user=user).filter(correctness=1).filter(assessment__id=1).count()) * 100 / Decimal (Response.objects.filter(user=user).filter(assessment__id=1).count() )
            if user.paper> 0:
                user.paperscore = Decimal (Response.objects.filter(user=user).filter(correctness=1).filter(assessment__id=5).count()) * 100 / Decimal (Response.objects.filter(user=user).filter(assessment__id=5).count() )



    return render(request, 'itemrtweb/leaderboard.html', {'topics': topics, 'all_user': all_user, 'selected_topic':selected_topic, 'selected_user':selected_user, 'selected_mode':selected_mode})
