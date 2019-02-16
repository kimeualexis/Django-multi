from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from ..decorators import instructor_required
from ..forms import BaseAnswerInlineFormSet, QuestionForm, InstructorSignUpForm
from ..models import Answer, Question, Topic, User


class InstructorSignUpView(CreateView):
    model = User
    form_class = InstructorSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'instructor'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('instructors:topic_change_list')


@method_decorator([login_required, instructor_required], name='dispatch')
class TopicListView(ListView):
    model = Topic
    ordering = ('name', )
    context_object_name = 'topics'
    template_name = 'codecat/instructors/topic_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.topics \
            .select_related('course') \
            .annotate(questions_count=Count('questions', distinct=True)) \
            .annotate(taken_count=Count('taken_topics', distinct=True))
        return queryset


@method_decorator([login_required, instructor_required], name='dispatch')
class TopicCreateView(CreateView):
    model = Topic
    fields = ('name', 'course', )
    template_name = 'codecat/instructors/topic_add_form.html'

    def form_valid(self, form):
        topic = form.save(commit=False)
        topic.user = self.request.user
        topic.save()
        messages.success(self.request, 'The topic was created successfully! Go ahead and add some questions now.')
        return redirect('instructors:topic_change', topic.pk)


@method_decorator([login_required, instructor_required], name='dispatch')
class TopicUpdateView(UpdateView):
    model = Topic
    fields = ('name', 'course', )
    context_object_name = 'topic'
    template_name = 'codecat/instructors/topic_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['questions'] = self.get_object().questions.annotate(answers_count=Count('answers'))
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing quizzes that belongs
        to the logged in user.
        '''
        return self.request.user.topics.all()

    def get_success_url(self):
        return reverse('instructors:topic_change', kwargs={'pk': self.object.pk})


@method_decorator([login_required, instructor_required], name='dispatch')
class TopicDeleteView(DeleteView):
    model = Topic
    context_object_name = 'topic'
    template_name = 'codecat/instructors/topic_delete_confirm.html'
    success_url = reverse_lazy('instructors:topic_change_list')

    def delete(self, request, *args, **kwargs):
        topic = self.get_object()
        messages.success(request, 'The topic %s was deleted with success!' % topic.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.topics.all()


@method_decorator([login_required, instructor_required], name='dispatch')
class TopicResultsView(DetailView):
    model = Topic
    context_object_name = 'topic'
    template_name = 'codecat/instructors/topic_results.html'

    def get_context_data(self, **kwargs):
        topic = self.get_object()
        taken_topics = topic.taken_topics.select_related('student__user').order_by('-date')
        total_taken_topics = taken_topics.count()
        topic_score = topic.taken_topics.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_topics': taken_topics,
            'total_taken_topics': total_taken_topics,
            'topic_score': topic_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.topics.all()


@login_required
@instructor_required
def question_add(request, pk):
    # By filtering the quiz by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # quiz will be able to add questions to it.
    topic = get_object_or_404(Topic, pk=pk, user=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.topic = topic
            question.save()
            messages.success(request, 'You may now add answers/options to the question.')
            return redirect('instructors:question_change', topic.pk, question.pk)
    else:
        form = QuestionForm()

    return render(request, 'codecat/instructors/question_add_form.html', {'topic': topic, 'form': form})


@login_required
@instructor_required
def question_change(request, topic_pk, question_pk):
    # Simlar to the `question_add` view, this view is also managing
    # the permissions at object-level. By querying both `quiz` and
    # `question` we are making sure only the owner of the quiz can
    # change its details and also only questions that belongs to this
    # specific quiz can be changed via this url (in cases where the
    # user might have forged/player with the url params.
    topic = get_object_or_404(Topic, pk=topic_pk, user=request.user)
    question = get_object_or_404(Question, pk=question_pk, topic=topic)

    AnswerFormSet = inlineformset_factory(
        Question,  # parent model
        Answer,  # base model
        formset=BaseAnswerInlineFormSet,
        fields=('text', 'is_correct'),
        min_num=2,
        validate_min=True,
        max_num=10,
        validate_max=True
    )

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, 'Question and answers saved successfully!')
            return redirect('instructors:topic_change', topic.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerFormSet(instance=question)

    return render(request, 'codecat/instructors/question_change_form.html', {
        'topic': topic,
        'question': question,
        'form': form,
        'formset': formset
    })


@method_decorator([login_required, instructor_required], name='dispatch')
class QuestionDeleteView(DeleteView):
    model = Question
    context_object_name = 'question'
    template_name = 'codecat/instructors/question_delete_confirm.html'
    pk_url_kwarg = 'question_pk'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        kwargs['topic'] = question.topic
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        question = self.get_object()
        messages.success(request, 'The question %s was deleted successful!' % question.text)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Question.objects.filter(topic__user=self.request.user)

    def get_success_url(self):
        question = self.get_object()
        return reverse('instructors:topic_change', kwargs={'pk': question.topic_id})
