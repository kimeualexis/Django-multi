from django.contrib import admin
from .models import Course, Topic, Question, Answer, Student, TakenTopic, StudentAnswer, User

# Register your models here.
admin.site.register(Question)
admin.site.register(Topic)
admin.site.register(TakenTopic)
admin.site.register(Student)
admin.site.register(StudentAnswer)
admin.site.register(Course)
admin.site.register(Answer)
admin.site.register(User)

