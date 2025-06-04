from django.shortcuts import render
from .models import UserProfile, Quiz
from django.http import JsonResponse

# Create your views here.
def simple_json_view(request):
    # if not UserProfile.objects.exists():
    #     UserProfile.objects.create(name="Test User", email="test@example.com")

    # data = list(UserProfile.objects.values('name', 'email'))
    quizname = Quiz.objects.first().title if Quiz.objects.exists() else "No quizzes available"
    return JsonResponse({'question': '5x = 0. What is x = ?', 'quiz': quizname}, safe=False)