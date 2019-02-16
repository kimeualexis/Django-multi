from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView

from ..decorators import student_required
from ..forms import StudentCourseForm, StudentSignUpForm, TakeTopicForm
from ..models import Topic, Student, TakenTopic, User


class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('students:topic_list')


@method_decorator([login_required, student_required], name='dispatch')
class StudentCourseView(UpdateView):
    model = Student
    form_class = StudentCourseForm
    template_name = 'codecat/students/courses_form.html'
    success_url = reverse_lazy('students:topic_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        messages.success(self.request, 'Topics updated successfully!!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class TopicListView(ListView):
    model = Topic
    ordering = ('name', )
    context_object_name = 'topics'
    template_name = 'codecat/students/topic_list.html'

    def get_queryset(self):
        student = self.request.user.student
        student_courses = student.courses.values_list('pk', flat=True)
        taken_topics = student.topics.values_list('pk', flat=True)
        queryset = Topic.objects.filter(course__in=student_courses) \
            .exclude(pk__in=taken_topics) \
            .annotate(questions_count=Count('questions')) \
            .filter(questions_count__gt=0)
        return queryset


@method_decorator([login_required, student_required], name='dispatch')
class TakenTopicListView(ListView):
    model = TakenTopic
    context_object_name = 'taken_topics'
    template_name = 'codecat/students/taken_topic_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_topics \
            .select_related('topic', 'topic__course') \
            .order_by('topic__name')
        return queryset


@login_required
@student_required
def take_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    student = request.user.student

    if student.topics.filter(pk=pk).exists():
        return render(request, 'students/taken_topic.html')

    total_questions = topic.questions.count()
    unanswered_questions = student.get_unanswered_questions(topic)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeTopicForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=False)
                student_answer.student = student
                student_answer.save()
                if student.get_unanswered_questions(topic).exists():
                    return redirect('students:take_topic', pk)
                else:
                    correct_answers = student.topic_answers.filter(answer__question__topic=topic, answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenTopic.objects.create(student=student, topic=topic, score=score)
                    if score < 50.0:
                        messages.warning(request, 'Better luck next time! Your score for the quiz %s was %s.' % (topic.name, score))
                    else:
                        messages.success(request, 'Congratulations! You completed the quiz %s with success! You scored %s points.' % (topic.name, score))
                    return redirect('students:topic_list')
    else:
        form = TakeTopicForm(question=question)

    return render(request, 'codecat/students/take_topic_form.html', {
        'topic': topic,
        'question': question,
        'form': form,
        'progress': progress
    })

