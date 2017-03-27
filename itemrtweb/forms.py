from django import forms
from django.forms.widgets import PasswordInput
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from itemrtdb.models import *

class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField(
        max_length=75,
        validators = [
            RegexValidator(
                regex='$',
                message='NTU Email is Required',
                code='invalid_ntuemail'
            ),
        ]
    )
    password = forms.CharField(
        widget=PasswordInput,
        validators = [MinLengthValidator(8)]
    )
    cfm_password = forms.CharField(widget=PasswordInput)

    def clean_email(self):
        # Perform checking for existing email used by user
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already in use")

        return email

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()

        # Perform checking for password confirmation
        password = cleaned_data.get("password")
        cfm_password = cleaned_data.get("cfm_password")

        if password and cfm_password and password != cfm_password:
            self._errors["cfm_password"] = self.error_class(["Confirm password does not match"])

            del cleaned_data["password"]
            del cleaned_data["cfm_password"]

        return cleaned_data

class PasswordForgetForm(forms.Form):
    email = forms.EmailField(
        max_length=75,
        validators = [
            RegexValidator(
                regex='$',
                message='NTU Email is Required',
                code='invalid_ntuemail'
            ),
        ]
    )

    def clean_email(self):
        # Perform checking for existing email used by user
        email = self.cleaned_data['email']

        if not User.objects.filter(email=email).exists():
            raise ValidationError("No account has been registered with this email")

        return email

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        max_length=75,
        validators = [
            RegexValidator(
                regex='$',
                message='NTU Email is Required',
                code='invalid_ntuemail'
            ),
        ]
    )
    password = forms.CharField(
        widget=PasswordInput,
        validators = [MinLengthValidator(8)]
    )
    cfm_password = forms.CharField(widget=PasswordInput)

    def clean(self):
        cleaned_data = super(PasswordResetForm, self).clean()

        # Perform checking for password confirmation
        password = cleaned_data.get("password")
        cfm_password = cleaned_data.get("cfm_password")

        if password and cfm_password and password != cfm_password:
            self._errors["cfm_password"] = self.error_class(["Confirm password does not match"])

            del cleaned_data["password"]
            del cleaned_data["cfm_password"]

        return cleaned_data

class ActivationForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()

class FeedbackForm(forms.Form):
    feedback = forms.CharField()

class InsertEditQuestionForm(forms.Form):
    topics = Topic.objects.all().order_by('id')
    tags = Tag.objects.all().values_list('name', 'name')

    content     = forms.CharField(max_length=2000)
    choice      = forms.CharField(max_length=200)
    source      = forms.CharField(max_length=2000)
    difficulty  = forms.IntegerField(min_value=1, max_value=5)
    topic       = forms.ModelChoiceField(queryset=topics)
    time        = forms.IntegerField(required=False, min_value=0)
    marks       = forms.DecimalField(required=False, max_digits=3, decimal_places=1, min_value=0.0)
    #answer      = forms.CharField(max_length=1) # This shld be 100 but MCQ for now only
    solution    = forms.CharField(required=False, max_length=2000)
    tags        = forms.MultipleChoiceField(required=False, choices=tags)

class FlagQuestionForm(forms.Form):
    issue = forms.CharField(max_length=2000)

class ForumForm(forms.Form):
    topics      = Topic.objects.all().order_by('id')

    content     = forms.CharField(max_length=200)
    topic       = forms.ModelChoiceField(queryset=topics)

class PostForm(forms.Form):
    content     = forms.CharField(max_length=200)

class NewQuestion(forms.Form):
    content     = forms.CharField(max_length=2000)

class InsertQuestionForm(forms.Form):
    topics = Topic.objects.all().order_by('id')
    tags = Tag.objects.all().values_list('name', 'name')

    content     = forms.CharField(max_length=2000)
    choiceA      = forms.CharField(max_length=50)
    #choiceB     = forms.CharField(max_length=50)
    #choiceC      = forms.CharField(max_length=50)
    #choiceD     = forms.CharField(max_length=50)
    source      = forms.CharField(max_length=2000)
    ##difficulty  = forms.IntegerField(min_value=1, max_value=5)
    ##topic       = forms.ModelChoiceField(queryset=topics)
    ##time        = forms.IntegerField(required=False, min_value=0)
    ##marks       = forms.DecimalField(required=False, max_digits=3, decimal_places=1, min_value=0.0)
    #answer      = forms.CharField(max_length=1) # This shld be 100 but MCQ for now only
    solution    = forms.CharField(required=False, max_length=2000)
    ##tags        = forms.MultipleChoiceField(required=False, choices=tags)


class InsertQuestionForm_2(forms.Form):
    topics = Topic.objects.all().order_by('id')
    tags = Tag.objects.all().values_list('name', 'name')

    content     = forms.CharField(max_length=2000)
    choice1      = forms.CharField(max_length=50)
    choice2     = forms.CharField(max_length=50)
    choice3      = forms.CharField(max_length=50)
    choice4     = forms.CharField(max_length=50)
    choice5      = forms.CharField(max_length=50)
    choice6     = forms.CharField(max_length=50)
    choice7      = forms.CharField(max_length=50)
    choice8     = forms.CharField(max_length=50)
    choice9      = forms.CharField(max_length=50)
    choice10     = forms.CharField(max_length=50)

    source1      = forms.CharField(max_length=200)
    source2      = forms.CharField(max_length=200)
    source3      = forms.CharField(max_length=200)
    source4      = forms.CharField(max_length=200)
    source5      = forms.CharField(max_length=200)
    source6      = forms.CharField(max_length=200)
    source7      = forms.CharField(max_length=200)
    source8      = forms.CharField(max_length=200)
    source9      = forms.CharField(max_length=200)
    source10      = forms.CharField(max_length=200)
    ##difficulty  = forms.IntegerField(min_value=1, max_value=5)
    ##topic       = forms.ModelChoiceField(queryset=topics)
    ##time        = forms.IntegerField(required=False, min_value=0)
    ##marks       = forms.DecimalField(required=False, max_digits=3, decimal_places=1, min_value=0.0)
    #answer      = forms.CharField(max_length=1) # This shld be 100 but MCQ for now only
    solution    = forms.CharField(required=False, max_length=2000)
    ##tags        = forms.MultipleChoiceField(required=False, choices=tags)

class InsertTopicForm(forms.Form):
    name = forms.CharField(max_length=50)

class InsertTagForm(forms.Form):
    topics = Topic.objects.all().order_by('id')
    topic       = forms.ModelChoiceField(queryset=topics)
    name = forms.CharField(max_length=50)
    description   = forms.CharField(max_length=2000)

class InsertConceptForm(forms.Form):
    topics = Topic.objects.all().order_by('id')
    topic       = forms.ModelChoiceField(queryset=topics)
    name = forms.CharField(max_length=50)
    description   = forms.CharField(max_length=2000)

class LearnForm(forms.Form):
    topics = Topic.objects.all().order_by('id')

    topic       = forms.ModelChoiceField(queryset=topics)
    description   = forms.CharField(max_length=20000)