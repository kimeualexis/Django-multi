from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.html import escape, mark_safe


# Create your models here.
class User(AbstractUser):
	is_student = models.BooleanField(default=False)
	is_instructor = models.BooleanField(default=False)


class Course(models.Model):
	name = models.CharField(max_length=30)
	color = models.CharField(max_length=7, default='#007bff')

	def __str__(self):
		return self.name

	def get_html_badge(self):
		name = escape(self.name)
		color = escape(self.color)
		html = '<span class="badge badge-primary" style="background-color: %s">%s</span>' % (color, name)
		return mark_safe(html)


class Topic(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics', null=True)
	name = models.CharField(max_length=255)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')

	def __str__(self):
		return self.name


class Question(models.Model):
	topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
	text = models.TextField()

	def __str__(self):
		return self.text


class Answer(models.Model):
	question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
	text = models.TextField()
	is_correct = models.BooleanField('Correct answer', default=False)

	def __str__(self):
		return self.text


class Student(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
	topics = models.ManyToManyField(Topic, through='TakenTopic')
	courses = models.ManyToManyField(Course, related_name='registered_students')

	def get_unanswered_questions(self, topic):
		answered_questions = self.topic_answers \
			.filter(answer__question__topic=topic) \
			.values_list('answer__question__pk', flat=True)
		questions = topic.questions.exclude(pk__in=answered_questions).order_by('text')
		return questions

	def __str__(self):
		return self.user.username


class TakenTopic(models.Model):
	student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='taken_topics')
	topic = models.ForeignKey(Topic,  on_delete=models.CASCADE, related_name='taken_topics')
	score = models.FloatField()
	date = models.DateTimeField(default=timezone.now)


class StudentAnswer(models.Model):
	student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='topic_answers')
	answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='+')







