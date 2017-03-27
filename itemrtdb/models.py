from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.timesince import timesince

class Topic(models.Model):
    "Topic model for topics that question can assosicate with"
    name        = models.CharField(max_length=30)
    position    = models.SmallIntegerField(blank=True, null=True)
    is_active   = models.BooleanField(default=True) # Deleted will be false
    #weight      = models.SmallIntegerField(default=1)
    #description = models.CharField(max_length=200)

    class Meta:
        ordering = ['position']

    def __unicode__(self):
        return self.name

class Type(models.Model):
    "Type model for different types of questions"
    name        = models.CharField(max_length=50)
    description = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class Meta(models.Model):
    "Meta model to keep the list of meta tags used"
    metatag     = models.CharField(max_length=30, primary_key=True)

    def __unicode__(self):
        return self.metatag

# Manager for Questions showing only the active questions
class ActiveQuestionManager(models.Manager):
    def get_query_set(self):
        return super(ActiveQuestionManager, self).get_queryset().filter(is_active=True)

class Question(models.Model):
    content     = models.TextField(max_length=2000)
    choice      = models.TextField(max_length=200)
    source      = models.TextField(max_length=2000)
    difficulty  = models.IntegerField()
    topic       = models.ForeignKey(Topic)
    time        = models.IntegerField(default=0) # In seconds
    marks       = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    type        = models.ForeignKey(Type, default=1)
    meta        = models.ManyToManyField(Meta, through='QuestionMeta')
    is_active   = models.BooleanField(default=True) # Deleted will be false
    tags        = models.ManyToManyField('Tag', through='QuestionTag')
    std_answer  = models.TextField(max_length=200)
    wholeparse  = models.TextField(max_length=200)
    parse       = models.TextField(max_length=200)
    choiceparse = models.TextField(max_length=200)
    new_topic   = models.IntegerField(default=-1)
    result      = models.DecimalField(max_digits=10, decimal_places=9)
    feature     = models.TextField(max_length=20000)
    concept    = models.ManyToManyField('Concept', through='QuestionConcept')
    score      = models.DecimalField(max_digits=10, decimal_places=9)
    Mp      = models.TextField(max_length=20000)
    Mk      = models.TextField(max_length=20000)
    def _get_question(self):
        "Get text of the question (without choices)"
        index = self.content.find('A.')
        return self.content

    def _get_choices(self):
# change this line:
        choiceAll = self.choice
        '''
        ans_a= choiceAll[0]
        ans_b = choiceAll[1]
        ans_c = choiceAll[2]
        ans_d = choiceAll[3]

        ans_dict = {}

        if ans_a:
            ans_dict['a'] = ans_a
        if ans_b:
            ans_dict['b'] = ans_b
        if ans_c:
            ans_dict['c'] = ans_c
        if ans_d:
            ans_dict['d'] = ans_d
'''
        return choiceAll

    # Additional property based attributes
    text        = property(_get_question)
    choices     = property(_get_choices)

    # Reimplement default objects manager to filter off questions not active
    objects_all = models.Manager()
    objects     = ActiveQuestionManager()

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return "Question " + str(self.id)



class Question_c(models.Model):
    content     = models.TextField(max_length=2000)
    choice      = models.TextField(max_length=200)
    analysis    = models.TextField(max_length=200)
    source      = models.TextField(max_length=200)
    difficulty  = models.IntegerField()
    topic       = models.ForeignKey(Topic)
    marks       = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
 #   meta        = models.ManyToManyField(Meta, through='QuestionMeta')

    def _get_question(self):
        "Get text of the question_c (without choices)"
        index = self.content.find('A.')
        return self.content
'''
    def _get_choices(self):
        choiceAll = self.choice.split(';')
        ans_a= choiceAll[0]
        ans_b = choiceAll[1]
        ans_c = choiceAll[2]
        ans_d = choiceAll[3]

        ans_dict = {}

        if ans_a:
            ans_dict['a'] = ans_a
        if ans_b:
            ans_dict['b'] = ans_b
        if ans_c:
            ans_dict['c'] = ans_c
        if ans_d:
            ans_dict['d'] = ans_d

        return ans_dict

    # Additional property based attributes
    text        = property(_get_question)
    choices     = property(_get_choices)

    # Reimplement default objects manager to filter off questions not active
    objects_all = models.Manager()
    objects     = ActiveQuestionManager()
'''





# New in version 20140214
class Tag(models.Model):
    name        = models.CharField(max_length=30)
    description = models.TextField(max_length=2000)
    topic       = models.ForeignKey(Topic)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return str(self.name)

# New in version 20140214
class QuestionTag(models.Model):
    question    = models.ForeignKey(Question)
    tag         = models.ForeignKey(Tag)

# New in version 20131023
class Solution(models.Model):
    "Solution model for question solutions if any"
    question    = models.OneToOneField(Question, primary_key=True, related_name='solution')
    content     = models.TextField(max_length=2000)
    rating      = models.IntegerField(blank=True, null=True)

# New in version 20131023
class Answer(models.Model):
    "Answer model to represent possible answer(s) for question"
    question    = models.ForeignKey(Question, related_name='answers')
    content     = models.TextField(max_length=100)
    correctness = models.DecimalField(max_digits=3, decimal_places=2, default=1) # Ans can be still correct but not 100% correct

# New in version 20131023
class Assessment(models.Model):
    "Assessment model to represent different assessment engines"

    PRACTICE = 'P'
    TEST = 'T'
    QUIZ = 'Q'
    ASSESSMENT_MODE_CHOICES = (
        (PRACTICE, 'Practice'),
        (TEST, 'Test'),
        (QUIZ, 'Quiz'),
    )

    name        = models.CharField(max_length=30)
    type        = models.CharField(max_length=1, choices=ASSESSMENT_MODE_CHOICES)
    active      = models.BooleanField()
    engine      = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name

# New in version 20131023
class Response(models.Model):
    "Response model to store user responses"
    user        = models.ForeignKey(User)
    question    = models.ForeignKey(Question)
    response    = models.TextField(max_length=100)
    date        = models.DateTimeField(auto_now=True)
    duration    = models.IntegerField(blank=True, null=True) # In seconds
    correctness = models.DecimalField(max_digits=3, decimal_places=2, null=True) # Percent correct in dec (0-1)
    criterion   = models.DecimalField(max_digits=3, decimal_places=1) # Max marks for random practice/test, diff for CAT
    ability     = models.DecimalField(max_digits=5, decimal_places=2, null=True) # Current ability score for practices
    assessment  = models.ForeignKey(Assessment)

# New in version 20131208
class Test(models.Model):
    "Test model for storage of each test paper generated"
    STATE_CHOICES = (
        (False, 'Draft'),
        (True, 'Active'),
    )

    id          = models.CharField(max_length=7, primary_key=True) #Unique 7 char alphanumeric ID
    user        = models.ForeignKey(User)
    generated   = models.DateTimeField(auto_now=True)
    questions   = models.ManyToManyField(Question, through='TestQuestion')
    assessment  = models.ForeignKey(Assessment)
    state       = models.BooleanField(choices=STATE_CHOICES, default=False)
    #gaokao_score = models.TextField(max_length=100)

    def _get_score(self):
        "Gets the score of the completed test"
        question = self.questions.all().reverse()[0] # Get last question

        # Should we filter for users?
        test_response = TestResponse.objects.filter(test=self).filter(question=question)[0]

        return test_response.ability

    score     = property(_get_score)

# New in version 20131208
class TestResponse(Response):
    "TestResponse model for storage of test responses, this links back to the test itself"
    test        = models.ForeignKey(Test, related_name='responses')

    def __unicode__(self):
        return 'TestResponse ' + str(self.id)

# Many to Many intermediary models

# New in version 20131023
class QuestionMeta(models.Model):
    "QuestionMeta model is an intermediary model between Question and Meta models"
    question    = models.ForeignKey(Question)
    meta        = models.ForeignKey(Meta)
    content     = models.CharField(max_length=50)

# New in version 20131208
class TestQuestion(models.Model):
    "TestQuestion model is an intermediary model between Test qnd Question models"
    question    = models.ForeignKey(Question)
    test        = models.ForeignKey(Test)

# New in version 20140205
class UserProfile(models.Model):
    user        = models.OneToOneField(User)

    debug       = models.BooleanField()

    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    post_save.connect(create_user_profile, sender=User)

# New in version 20140215
class UserUsage(models.Model):
    user        = models.ForeignKey(User)
    datetime    = models.DateTimeField(auto_now=True)
    page        = models.CharField(max_length=50)

    class Meta:
        ordering = ['-datetime']

    def __unicode__(self):
        return self.user.get_full_name() + ' last accessed ' + self.page + ' ' + timesince(self.datetime) + ' ago'

# New in version 20140221
class QuestionFlag(models.Model):
    question    = models.ForeignKey(Question)
    user        = models.ForeignKey(User)
    issue       = models.TextField(max_length=2000)
    reported    = models.DateTimeField(auto_now=True)
    resolved    = models.BooleanField(default=False)

#Learn
class Learn(models.Model):
    topic = models.ForeignKey(Topic)
    description = models.TextField(max_length=10000)

# New in version 20140215
class LearnUsage(models.Model):
    user        = models.ForeignKey(User)
    datetime    = models.DateTimeField(auto_now=True)
    learn        = models.ForeignKey(Learn)

    class Meta:
        ordering = ['-datetime']

    def __unicode__(self):
        return self.user.get_full_name() + ' last accessed ' + self.topic + ' ' + timesince(self.datetime) + ' ago'

class Thread(models.Model):
    content     = models.TextField(max_length=200)
    topic       = models.ForeignKey(Topic)
    view        = models.IntegerField(default=0)
    reply       = models.IntegerField(default=0)
    user        = models.ForeignKey(User)
    datetime    = models.DateTimeField(auto_now=False)
    latest      = models.DateTimeField(auto_now=False)

    class Meta:
        ordering = ['-datetime']

    def __unicode__(self):
        return "Thread " + str(self.id)

class Post(models.Model):
    thread      = models.ForeignKey(Thread)
    content     = models.TextField(max_length=200)
    user        = models.ForeignKey(User)
    datetime    = models.DateTimeField(auto_now=False)

    class Meta:
        ordering = ['-datetime']

    def __unicode__(self):
        return self.user.get_full_name() + ' posted a reply for ' + self.question + ' ' + timesince(self.datetime) + ' ago'

class Concept(models.Model):
    name        = models.CharField(max_length=30)
    description = models.TextField(max_length=2000)
    topic       = models.ForeignKey(Topic)
    words        = models.ManyToManyField('Tag', through='ConceptWord')
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return str(self.name)

class QuestionConcept(models.Model):
    question    = models.ForeignKey(Question)
    concept      = models.ForeignKey(Concept)

class ConceptWord(models.Model):
    concept    = models.ForeignKey(Concept)
    word         = models.ForeignKey(Tag)