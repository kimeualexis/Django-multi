from .views import codecat, students, instructors
from django.urls import include, path


urlpatterns = [
	path('', codecat.index, name='index'),

	path('students/', include(([
		path('', students.TopicListView.as_view(), name='topic_list'),
        path('courses/', students.StudentCourseView.as_view(), name='student_course'),
        path('taken/', students.TakenTopicListView.as_view(), name='taken_topic_list'),
        path('topic/<int:pk>/', students.take_topic, name='take_topic'),
   ], 'codecat'), namespace='students')),

	path('instructors/', include(([
       path('', instructors.TopicListView.as_view(), name='topic_change_list'),
       path('topic/add/', instructors.TopicCreateView.as_view(), name='topic_add'),
       path('topic/<int:pk>/', instructors.TopicUpdateView.as_view(),
           name='topic_change'),
       path('topic/<int:pk>/delete/', instructors.TopicDeleteView.as_view(),
           name='topic_delete'),
       path('topic/<int:pk>/results/', instructors.TopicResultsView.as_view(),
           name='topic_results'),
       path('topic/<int:pk>/question/add/', instructors.question_add,
           name='question_add'),
       path('topic/<int:topic_pk>/question/<int:question_pk>/',
           instructors.question_change, name='question_change'),
       path('topic/<int:topic_pk>/question/<int:question_pk>/delete/',
           instructors.QuestionDeleteView.as_view(), name='question_delete'),
          ], 'codecat'), namespace='instructors')),
]