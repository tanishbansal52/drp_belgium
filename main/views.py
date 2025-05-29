from django.shortcuts import render
from .models import UserProfile  
from django.http import JsonResponse

# Create your views here.
def simple_json_view(request):
    # if not UserProfile.objects.exists():
    #     UserProfile.objects.create(name="Test User", email="test@example.com")

    # data = list(UserProfile.objects.values('name', 'email'))
    return JsonResponse({'question': '5x = 0. What is x = ?'}, safe=False)