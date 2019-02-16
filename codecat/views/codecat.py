from django.shortcuts import render, redirect
from django.views.generic import TemplateView


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'


def index(request):
	if request.user.is_authenticated:
		if request.user.is_instructor:
			return redirect('instructors:topic_change_list')
		else:
			return redirect('students:topic_list')
	return render(request, 'codecat/index.html')
