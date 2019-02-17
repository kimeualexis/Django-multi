"""pycode URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from codecat.views import instructors, students, codecat

urlpatterns = [
	path('admin/', admin.site.urls),
	path('', include('codecat.urls')),
	path('accounts/', include('django.contrib.auth.urls')),
	path('accounts/signup/', codecat.SignUpView.as_view(), name='signup'),
	path('accounts/signup/student/', students.StudentSignUpView.as_view(), name='student_signup'),
	path('accounts/signup/instructor', instructors.InstructorSignUpView.as_view(), name='instructor_signup'),
]
