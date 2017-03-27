from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from itemrtweb.views import *
from search.views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', home),
    url(r'^home/$', user_home),
    url(r'^about/$', about),
    url(r'^about/2/$', aboutsurvey),
    url(r'^about/video/$', aboutvideo),

    # Learn
    url(r'^learn/$',learn_home),
    url(r'^learn/(\d+)/$', learn_topic),
    url(r'^concept/(\d+)/$', learn_topicconcept),

    # Browse
    url(r'^browse/diff/(\d+)/$', browsediff),
    url(r'^question/(?P<id>\d+)/view/$', question_view, {'practiced': True}),

    # Paper Practice
    url(r'^practice/paper/$', paperprac),
    url(r'^practice/paper/(?P<test_id>\w+)/$', paperprac),
    url(r'^practice/paper/submit/(?P<test_id>\w+)/$', paperpracsubmit),
    url(r'^practice/paper/(?P<test_id>\w+)/(?P<util_name>\w+)/$', paperpracutil),
    url(r'^question/flag/(?P<question_id>\d+)/$', flag_question),

    # CAT Test
    url(r'^test/cat/$', trialtest),

    url(r'^test/cat/generate/$', trialtest_generate),
    url(r'^test/cat/history/$', progress),
    url(r'^test/cat/go/(?P<test_id>\w+)/$', trialtest_go),
    url(r'^test/cat/(?P<test_id>\w+)/(?P<util_name>\w+)/$', trialtestutil),
    url(r'^test/cat/(?P<test_id>\w+)/$', trialtesthist),

    # Paper Test
    url(r'^test/paper/$', papertest),
    url(r'^test/paper_2/$', papertest_2),

    ##url(r'^test/paper/history/$', papertesthist),
    url(r'^test/paper/proficiency/$', papertestprogress),

    url(r'^test/paper/(?P<test_id>\w+)/$', papertest),
    url(r'^test/paper_2/(?P<test_id>\w+)/$', papertest_2),
    url(r'^test/paper/submit/(?P<test_id>\w+)/$', papertestsubmit),

    url(r'^test/paper/(?P<test_id>\w+)/(?P<util_name>\w+)/$', papertestutil),
    ##url(r'^test/paper/print/$', printpdf),

    # Search for Users
    url(r'^search/pattern/$', adaptivesearch),
    url(r'^search/$', user_search),

    #Feedback
    ##url(r'^feedback/$', feedback),
    ##url(r'^survey/$', 'itemrtweb.views.survey'),
    url(r'^analyse/diff/$', diffcount),
    url(r'^analyse/diff/(\d+)/$', diff),
    url(r'^analyse/parser/$', parser),
    url(r'^analyse/(\d+)/$',analyzer_topic_tag),
    url(r'^analyse/$',analyzer_tag),
    url(r'^analyse/question/$',question),
    url(r'^analyse/topic/$',eng_Admin_RegenTopicdone),

    # Question Management
    url(r'^question/search/(\d+)/$', browsequestion),
    url(r'^prototype/$', prototype),
    url(r'^question/edit/(?P<question_id>\d+)/$', prototype),
    url(r'^question/delete/(?P<question_id>\d+)/$', prototype3),
    url(r'^question/view/(?P<question_id>\d+)/$', preview),
    url(r'^question/$', prototype2),
    url(r'^question/list/topic/(?P<topic_id>\d+)/$', prototype2),
    url(r'^question/list/tags/$', prototype2a),
    #url(r'^question/new/$', insertQ), #step 1
    url(r'^question/insert/$', prototypeauto), #step 2
    url(r'^question/insert2/$', prototypeauto_2), #step 2

    url(r'^question/insert/(?P<question_id>\d+)/$', postauto), #step3

    #Topic Management
    url(r'^control/topic/$', topicview),
    url(r'^control/topic/insert/$', topicinsert),
    url(r'^control/topic/delete/(?P<topic_id>\d+)/$', topicdelete),
    url(r'^control/topic/up/(?P<topic_id>\d+)/$', topicup),
    url(r'^control/topic/down/(?P<topic_id>\d+)/$', topicdown),

    #Tag Management
    url(r'^control/tag/$', tagcontrol),
    url(r'^control/tag/topic/(?P<topic_id>\d+)/$', tagcontrol),
    url(r'^control/tag/list/$', taglist),
    url(r'^control/tag/view/(?P<tag_id>\d+)/$', tagview),
    url(r'^control/tag/delete/(?P<tag_id>\d+)/$', tagdelete),
    url(r'^control/tag/insert/$', taginsert),
    url(r'^control/tag/edit/(?P<tag_id>\d+)/$', tagedit),

    #Concept Tag Management
    url(r'^control/concept/$', conceptcontrol),
    url(r'^control/concept/topic/(?P<topic_id>\d+)/$', conceptcontrol),
    url(r'^control/concept/view/(?P<tag_id>\d+)/$', conceptview),
    url(r'^control/concept/edit/(?P<tag_id>\d+)/$', conceptedit),
    url(r'^control/concept/delete/(?P<tag_id>\d+)/$', conceptdelete),
    url(r'^control/concept/insert/$', conceptinsert),

    ##Learn Control
    url(r'^control/learn/$', learncontrol),
    url(r'^control/learn/topic/(?P<learn_id>\d+)/$', learnview),
    url(r'^control/learn/edit/(?P<learn_id>\d+)/$', learnedit),

    #LEADERBOARD
    url(r'^leaderboard/$', leaderboard),
    url(r'^leaderboard/(?P<topic_id>\d+)/$', leaderboard),
    url(r'^topic/$', topic),
    ##Forum
##    url(r'^forum/$', forum),
##    url(r'^forum/insert/$', foruminsert),
##    url(r'^forum/(\d+)/$', forumtopic),
##    url(r'^forum/(\d+)/(\d+)/$', forumthread),

    # Login, Logout and accounts
    url(r'^accounts/login/$', account_login),
    url(r'^accounts/logout/$', account_logout),
    url(r'^accounts/register/$', account_register),
    url(r'^accounts/activate/$', account_activate),
    url(r'^accounts/forgot/$', account_forgot),
    url(r'^accounts/reset/$', account_reset),
    url(r'^accounts/profile/$', RedirectView.as_view(url='/home/')),

    # Debug functions
    url(r'^debug/mode/(\d+)/$', debug_changemode),
    url(r'^debug/clearresponse/$', debug_clearresponses),

    # Control Panel
    url(r'^control/$', control),
    url(r'^control/cattest/settings/$', control_cattest_settings),
    url(r'^control/download/(\w+)/$', controldownloadpaper),
    url(r'^control/flaggedqn/$', flag_display),

	url(r'^eng_admin_regenkeyword/$',eng_Admin_RegenKeyword),
    url(r'^eng_admin_regendiff/$',eng_Admin_RegenDiff),
    url(r'^eng_admin_regenparse/$',eng_Admin_RegenParse),
    url(r'^eng_admin_regentopic/$',eng_Admin_RegenTopic),
    url(r'^eng_admin_regenconcept/$',eng_Admin_RegenConcept),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^comments/', include('django.contrib.comments.urls')),

    url(r'^postdata/$', postdata),

    # Temp
    url(r'^prototype/test/question/(?P<question_id>\d+)/$', 'itemrtweb.views.testquestion'),

    # Prod static files
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    url(r'^gentest/$', gentest),
    url(r'^gentest/(?P<test_id>\w+)/$', gentest),

    # Examples:
    # url(r'^$', 'itemrtproject.views.home', name='home'),
    # url(r'^itemrtproject/', include('itemrtproject.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # NOT IN USE
    url(r'^control/newtest/$', 'itemrtweb.views.controlnewtest'),
    url(r'^control/newtest/submit/$', 'itemrtweb.views.controlnewtest_submit'),
    url(r'^control/view/(\w+)/$', controlviewpaper),

)

# Append staticfiles into urlpatterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
