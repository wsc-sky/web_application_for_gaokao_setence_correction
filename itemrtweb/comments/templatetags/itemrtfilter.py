from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

import re

register = template.Library()

@register.filter(name='formatquestionforweb')
def format_question_for_web(value):
    value = re.sub(r'\\begin{code}\r\n', '<pre class="prettyprint linenums">', value)
    value = re.sub(r'\\end{code}\r\n', '</pre>', value)

    index_start_pre = value.find('<pre class="prettyprint linenums">')
    index_end_pre = value.find('</pre>')

    front_string = escape(value[:index_start_pre])
    safe_string = escape(value[index_start_pre+34:index_end_pre])
    back_string = escape(value[index_end_pre+6:])

    value = front_string + '<pre class="prettyprint linenums">' + safe_string + '</pre>' + back_string

    return value

@register.filter(name='keyvalue')
def keyvalue(dict, key):
    return dict[key]

@register.filter(name='ast')
def ast(key):
    return key.replace('*','_______')

@register.filter(name='highlight')
def highlight(text, filter):
    pattern = re.compile(r"(?P<filter>%s)" % filter, re.IGNORECASE)
    return mark_safe(re.sub(pattern, r"<b>\g<filter></b>", text))

@register.filter(name='abcd')
def abcd(key):
    choice =  str(key).split(';')
    show = "<b> (A)</b> " + choice[0] + " <b>(B)</b> " + choice[1]+ " <b>(C)</b> " + choice[2]+ " <b>(D)</b> " + choice[3]
    return show

@register.filter(name='cnum')
def cnum(key):
    choice =  str(key).split(';')
    show = "<b>(1)</b> " + choice[0] + "<br> <b>(2)</b> " + choice[1]+ "<br> <b>(3)</b> " + choice[2]+ "<br> <b>(4)</b> " + choice[3]
    return show

@register.filter(name='c1234')
def c1234(key):
    choice =  str(key).split(';')
    show = choice
    return show
