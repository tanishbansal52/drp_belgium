from django.shortcuts import render
from .models import UserProfile, Quiz
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Room, Group
import json
from .models import GroupResponse, Group, Question

# Create your views here.
# def simple_json_view(request):
    # if not UserProfile.objects.exists():
    #     UserProfile.objects.create(name="Test User", email="test@example.com")

    # data = list(UserProfile.objects.values('name', 'email'))
    # quizname = Quiz.objects.first().title if Quiz.objects.exists() else "No quizzes available"
    # return JsonResponse({'question': '5x = 0. What is x = ?', 'quiz': quizname}, safe=False)

def simple_json_view(request, n):
    if n is None or n < 0:
        n = 0
    questions = list(Question.objects.all())  # later use current question from room
    question = questions[n] if questions else None
    if not question:
        return JsonResponse({'error': 'No question available'}, status=404)

    return JsonResponse({
        'question_id': question.id,
        'answer': question.answer,
        'question_text': question.question_text,
        'answer': question.answer,
        'points': question.points,
        'quiz': question.quiz.title
    })

def give_questions(request, quiz_id):
    questions = Question.objects.filter(quiz_id=quiz_id)
    if not questions:
        return JsonResponse({'error': 'No questions available'}, status=404)

    data = [{
        'question_id': q.id,
        'question_text': q.question_text,
        'answer': q.answer,
        'points': q.points,
        'quiz': q.quiz.title
    } for q in questions]

    return JsonResponse(data, safe=False)

@api_view(['GET'])
def give_quizzes(request):
    quizzes = list(Quiz.objects.all())
    if not quizzes:
        return JsonResponse({'error': 'No quizzes available'}, status=404)

    data = [{
        'id': q.id,
        'title': q.title,
        'subject': q.subject,
        'difficulty': q.difficulty,
        'total_time': q.total_time,
        'description': q.description
    } for q in quizzes]

    return JsonResponse(data, safe=False)

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
    GroupResponse.objects.create(
        group=group,
        question=question,
        submitted_answer=answer,
        is_correct=is_correct,
        points_earned=points_earned,
        response_time=0  # for now
    )

    # Update score
    if is_correct:
        group.curr_score += points_earned
        group.save()

    return JsonResponse({
        'correct': is_correct,
        'points_earned': points_earned,
        'total_score': group.curr_score
    })

@api_view(['POST'])
def join_room(request):
    room_code = request.data.get('room_code')
    group_name = request.data.get('group_name')

    if not room_code or not group_name:
        return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
    
    group, created = Group.objects.get_or_create(name=group_name, room=room)
    if not created:
        return Response({'error': 'Group already exists for this room'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"group_id": group.group_id,
        "room_code": room.room_code, 'message': 'Group created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def add_room(request):
    room_code = request.data.get('room_code')

    if not room_code:
        return Response({"error": "Missing room_code"}, status=status.HTTP_400_BAD_REQUEST)
    
    room, created = Room.objects.get_or_create(room_code=room_code, curr_number=0)
    if not created:
        return Response({'error': 'Room already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"room_id": room.room_id, "room_code": room.room_code, 'message': 'Room created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def can_move_to_next_question(request, room_code, curr_status):
    if not room_code or curr_status is None:
        return Response({"error": "Missing room_code or status"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
    if room.curr_number > int(curr_status):
        return Response({"can_move": True}, status=status.HTTP_200_OK)
    else:
        return Response({"can_move": False}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_rooms(request):
    rooms = Room.objects.all()
    room_list = [{"room_id": room.room_code, "curr_number": room.curr_number} for room in rooms]
    return Response(room_list, status=status.HTTP_200_OK)

@api_view(['POST'])
def update_room_status(request):
    room_code = request.data.get('room_code')
    new_status = request.data.get('status')

    if not room_code or new_status is None:
        return Response({"error": "Missing room_code or status"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

    room.curr_number = new_status

    room.save()
    return Response({"room_id": room.room_id, "room_code": room.room_code, "status": room.curr_number, "message": "Room status updated"}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_room_groups(request, room_code):
    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
    
    groups = Group.objects.filter(room=room)
    group_list = [{"group_id": group.group_id, "name": group.name, "curr_score": group.curr_score} for group in groups]
    return Response(group_list, status=status.HTTP_200_OK)






