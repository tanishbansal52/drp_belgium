from django.shortcuts import render
from .models import UserProfile, Quiz
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import Response, Group, Question

# Create your views here.
# def simple_json_view(request):
    # if not UserProfile.objects.exists():
    #     UserProfile.objects.create(name="Test User", email="test@example.com")

    # data = list(UserProfile.objects.values('name', 'email'))
    # quizname = Quiz.objects.first().title if Quiz.objects.exists() else "No quizzes available"
    # return JsonResponse({'question': '5x = 0. What is x = ?', 'quiz': quizname}, safe=False)

def simple_json_view(request):
    question = Question.objects.first()  # later use current question from room

    if not question:
        return JsonResponse({'error': 'No question available'}, status=404)

    return JsonResponse({
        'question_id': question.id,
        'question_text': question.question_text,
        'answer': question.answer,
        'points': question.points,
        'quiz': question.quiz.title
    })


@csrf_exempt
@require_POST
def submit_answer(request):
    data = json.loads(request.body)
    group_id = data.get('group_id')
    question_id = data.get('question_id')
    answer = data.get('answer')

    try:
        question = Question.objects.get(id=question_id)
        group = Group.objects.get(group_id=group_id)
    except (Group.DoesNotExist, Question.DoesNotExist):
        return JsonResponse({'error': 'Group or Question not found'}, status=404)

    is_correct = answer.strip() == question.answer.strip()
    points_earned = question.points if is_correct else 0

    # Save the response
    Response.objects.create(
        group=group,
        question=question,
        answer=answer,
        is_correct=is_correct,
        points_earned=points_earned,
        response_time=0  # for now
    )

    # Update score
    if is_correct:
        group.current_score += points_earned
        group.save()

    return JsonResponse({
        'correct': is_correct,
        'points_earned': points_earned,
        'total_score': group.current_score
    })