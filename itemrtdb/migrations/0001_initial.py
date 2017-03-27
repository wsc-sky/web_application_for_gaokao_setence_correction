# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(max_length=100)),
                ('correctness', models.DecimalField(default=1, max_digits=3, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('type', models.CharField(max_length=1, choices=[(b'P', b'Practice'), (b'T', b'Test'), (b'Q', b'Quiz')])),
                ('active', models.BooleanField()),
                ('engine', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField(max_length=2000)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConceptWord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('concept', models.ForeignKey(to='itemrtdb.Concept')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Learn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(max_length=10000)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LearnUsage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('learn', models.ForeignKey(to='itemrtdb.Learn')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-datetime'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Meta',
            fields=[
                ('metatag', models.CharField(max_length=30, serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(max_length=200)),
                ('datetime', models.DateTimeField()),
            ],
            options={
                'ordering': ['-datetime'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(max_length=2000)),
                ('choice', models.TextField(max_length=200)),
                ('source', models.TextField(max_length=2000)),
                ('difficulty', models.IntegerField()),
                ('time', models.IntegerField(default=0)),
                ('marks', models.DecimalField(default=1.0, max_digits=3, decimal_places=1)),
                ('is_active', models.BooleanField(default=True)),
                ('std_answer', models.TextField(max_length=200)),
                ('wholeparse', models.TextField(max_length=200)),
                ('parse', models.TextField(max_length=200)),
                ('choiceparse', models.TextField(max_length=200)),
                ('new_topic', models.IntegerField(default=-1)),
                ('result', models.DecimalField(max_digits=10, decimal_places=9)),
                ('feature', models.TextField(max_length=20000)),
                ('score', models.DecimalField(max_digits=10, decimal_places=9)),
                ('Mp', models.TextField(max_length=20000)),
                ('Mk', models.TextField(max_length=20000)),
            ],
            options={
                'ordering': ['id'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question_c',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(max_length=2000)),
                ('choice', models.TextField(max_length=200)),
                ('analysis', models.TextField(max_length=200)),
                ('source', models.TextField(max_length=200)),
                ('difficulty', models.IntegerField()),
                ('marks', models.DecimalField(default=1.0, max_digits=3, decimal_places=1)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionConcept',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('concept', models.ForeignKey(to='itemrtdb.Concept')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('issue', models.TextField(max_length=2000)),
                ('reported', models.DateTimeField(auto_now=True)),
                ('resolved', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.CharField(max_length=50)),
                ('meta', models.ForeignKey(to='itemrtdb.Meta')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response', models.TextField(max_length=100)),
                ('date', models.DateTimeField(auto_now=True)),
                ('duration', models.IntegerField(null=True, blank=True)),
                ('correctness', models.DecimalField(null=True, max_digits=3, decimal_places=2)),
                ('criterion', models.DecimalField(max_digits=3, decimal_places=1)),
                ('ability', models.DecimalField(null=True, max_digits=5, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Solution',
            fields=[
                ('question', models.OneToOneField(related_name='solution', primary_key=True, serialize=False, to='itemrtdb.Question')),
                ('content', models.TextField(max_length=2000)),
                ('rating', models.IntegerField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField(max_length=2000)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.CharField(max_length=7, serialize=False, primary_key=True)),
                ('generated', models.DateTimeField(auto_now=True)),
                ('state', models.BooleanField(default=False, choices=[(False, b'Draft'), (True, b'Active')])),
                ('assessment', models.ForeignKey(to='itemrtdb.Assessment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.ForeignKey(to='itemrtdb.Question')),
                ('test', models.ForeignKey(to='itemrtdb.Test')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestResponse',
            fields=[
                ('response_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='itemrtdb.Response')),
                ('test', models.ForeignKey(related_name='responses', to='itemrtdb.Test')),
            ],
            options={
            },
            bases=('itemrtdb.response',),
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(max_length=200)),
                ('view', models.IntegerField(default=0)),
                ('reply', models.IntegerField(default=0)),
                ('datetime', models.DateTimeField()),
                ('latest', models.DateTimeField()),
            ],
            options={
                'ordering': ['-datetime'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('position', models.SmallIntegerField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['position'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('debug', models.BooleanField()),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserUsage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('page', models.CharField(max_length=50)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-datetime'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='thread',
            name='topic',
            field=models.ForeignKey(to='itemrtdb.Topic'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='thread',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='test',
            name='questions',
            field=models.ManyToManyField(to='itemrtdb.Question', through='itemrtdb.TestQuestion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='test',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='topic',
            field=models.ForeignKey(to='itemrtdb.Topic'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='response',
            name='assessment',
            field=models.ForeignKey(to='itemrtdb.Assessment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='response',
            name='question',
            field=models.ForeignKey(to='itemrtdb.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='response',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questiontag',
            name='question',
            field=models.ForeignKey(to='itemrtdb.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questiontag',
            name='tag',
            field=models.ForeignKey(to='itemrtdb.Tag'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questionmeta',
            name='question',
            field=models.ForeignKey(to='itemrtdb.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questionflag',
            name='question',
            field=models.ForeignKey(to='itemrtdb.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questionflag',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questionconcept',
            name='question',
            field=models.ForeignKey(to='itemrtdb.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question_c',
            name='topic',
            field=models.ForeignKey(to='itemrtdb.Topic'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='concept',
            field=models.ManyToManyField(to='itemrtdb.Concept', through='itemrtdb.QuestionConcept'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='meta',
            field=models.ManyToManyField(to='itemrtdb.Meta', through='itemrtdb.QuestionMeta'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='tags',
            field=models.ManyToManyField(to='itemrtdb.Tag', through='itemrtdb.QuestionTag'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='topic',
            field=models.ForeignKey(to='itemrtdb.Topic'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='type',
            field=models.ForeignKey(default=1, to='itemrtdb.Type'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(to='itemrtdb.Thread'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='learn',
            name='topic',
            field=models.ForeignKey(to='itemrtdb.Topic'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='conceptword',
            name='word',
            field=models.ForeignKey(to='itemrtdb.Tag'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='concept',
            name='topic',
            field=models.ForeignKey(to='itemrtdb.Topic'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='concept',
            name='words',
            field=models.ManyToManyField(to='itemrtdb.Tag', through='itemrtdb.ConceptWord'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(related_name='answers', to='itemrtdb.Question'),
            preserve_default=True,
        ),
    ]
