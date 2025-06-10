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
from django.db.models import Avg

# Create your views here.

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

def give_questions(request):
    questions = list(Question.objects.all())
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
        'quiz_id': q.id,
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

    # Check if a response already exists for this group and question
    existing_response = GroupResponse.objects.filter(group=group, question=question).first()

    print("existing response: ", existing_response)

    if existing_response:
        # If updating to a correct answer and wasn't correct before, update score
        if is_correct and not existing_response.is_correct:
            group.curr_score += points_earned
            group.save()

        # Overwrite existing response
        existing_response.submitted_answer = answer
        existing_response.is_correct = is_correct
        existing_response.points_earned = points_earned
        existing_response.response_time = 0
        existing_response.save()
    else:
        # New response
        GroupResponse.objects.create(
            group=group,
            question=question,
            submitted_answer=answer,
            is_correct=is_correct,
            points_earned=points_earned,
            response_time=0  # Placeholder for now
        )

        if is_correct:
            group.curr_score += points_earned
            group.save()

    return JsonResponse({
        'correct': is_correct,
        'points_earned': points_earned,
        'total_score': group.curr_score
    })

@api_view(['GET'])
def get_groups_finished_question(request, room_code, question_id):
    """
    API to get all groups that have finished a particular question in a room.
    
    Expected parameters:
    - room_code: The room code
    - question_id: The ID of the question
    
    Returns:
    - List of groups with their names and student names who have submitted answers
    """
    
    if not room_code or not question_id:
        return JsonResponse({
            'error': 'Both room_code and question_id are required'
        }, status=400)
    
    try:
        # Get the room
        room = Room.objects.get(room_code=room_code)
        
        # Get the question
        question = Question.objects.get(id=question_id)
        
        # Verify the question belongs to the room's quiz
        if question.quiz != room.quiz:
            return JsonResponse({
                'error': 'Question does not belong to this room\'s quiz'
            }, status=400)
        
        # Get all groups in this room that have submitted responses to this question
        groups_with_responses = Group.objects.filter(
            room=room,
            groupresponse__question=question
        ).distinct()
        
        # Format the response data
        finished_groups = []
        for group in groups_with_responses:
            # Get the response for additional info
            response = GroupResponse.objects.get(group=group, question=question)
            
            finished_groups.append({
                'group_id': group.group_id,
                'group_name': group.name,
                'student_names': group.student_names,
                'is_correct': response.is_correct,
                'points_earned': response.points_earned,
                'submitted_answer': response.submitted_answer,
                'current_score': group.curr_score
            })
        
        # Get total number of groups in the room for context
        total_groups = Group.objects.filter(room=room).count()
        
        return JsonResponse({
            'room_code': room_code,
            'question_id': question_id,
            'question_text': question.question_text,
            'finished_groups': finished_groups,
            'total_groups': total_groups,
            'finished_count': len(finished_groups)
        }, status=200)
        
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def join_room(request):
    room_code = request.data.get('room_code')
    group_name = request.data.get('group_name')
    student_names = request.data.get('student_names', [])

    if not room_code or not group_name:
        return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
    
    group, created = Group.objects.get_or_create(name=group_name, room=room, student_names=student_names)
    if not created:
        return Response({'error': 'Group already exists for this room'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"group_id": group.group_id,
        "room_code": room.room_code,
        "student_names": group.student_names, 
        'message': 'Group created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def add_room(request):
    room_code = request.data.get('room_code')
    quiz_id = request.data.get('quiz_id') 

    if not quiz_id:
        quiz_id = 1

    if not room_code:
        return Response({"error": "Missing room_code"}, status=status.HTTP_400_BAD_REQUEST)
    
    room, created = Room.objects.get_or_create(room_code=room_code, curr_number=0, quiz= Quiz.objects.get(id=quiz_id)) 
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
    group_list = [{"group_id": group.group_id, "name": group.name, "members": list(group.student_names), "curr_score": group.curr_score} for group in groups]
    return Response(group_list, status=status.HTTP_200_OK)

@api_view(['POST'])
def update_before_rating(request):
    before_rating = request.data.get('before_rating')
    group_id = request.data.get('group_id')

    if not before_rating or not group_id:
        return Response({"error": "Missing before_rating or group_name"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        group = Group.objects.get(group_id=group_id)
    except Group.DoesNotExist:
        return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
    
    group.before_rating = before_rating
    group.save()

    return Response({"group_id": group.group_id, "name": group.name, "before_rating": group.before_rating, "message": "Before rating updated"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def update_after_rating(request):
    after_rating = request.data.get('after_rating')
    group_id = request.data.get('group_id')

    if not after_rating or not group_id:
        return Response({"error": "Missing after_rating or group_name"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        group = Group.objects.get(group_id=group_id)
    except Group.DoesNotExist:
        return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
    
    group.after_rating = after_rating
    group.save()

    return Response({"group_id": group.group_id, "name": group.name, "after_rating": group.after_rating, "message": "After rating updated"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def mark_mission_complete(request):
    room_code = request.data.get('room_code')

    if not room_code:
        return Response({"error": "Missing room_code"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = Room.objects.get(room_code=room_code)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
    
    room.status = 'completed'
    room.save()
    return Response({"room_id": room.room_id, "room_code": room.room_code, "status": room.status, "message": "Mission marked as complete"}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_past_missions(request):
    """
    Get all completed missions (rooms with status 'completed')
    """
    try:
        past_missions = Room.objects.filter(status='completed')
        
        if not past_missions:   
            return JsonResponse({
                'success': False,
                'message': 'No past missions found'
            }, status=404)
        
        missions_data = []
        for room in past_missions:
            # Get additional stats for each mission
            total_groups = Group.objects.filter(room=room).count()
            total_questions = Question.objects.filter(quiz=room.quiz).count()
            
            mission_data = {
                'room_id': room.room_id,
                'room_code': room.room_code,
                'quiz_title': room.quiz.title,
                'quiz_subject': room.quiz.subject,
                'quiz_difficulty': room.quiz.difficulty,
                'total_time': room.quiz.total_time,
                'created_at': room.created_at.isoformat(),
                'total_groups': total_groups,
                'total_questions': total_questions
            }
            # print(f"Mission data for room {room.room_code}: {mission_data}")
            missions_data.append(mission_data)
        
        return JsonResponse({
            'success': True,
            'missions': missions_data,
            'total_count': len(missions_data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

@api_view(["GET"])
def get_mission_report(request, room_id):

    try:
        # Get the room and verify it's completed
        room = Room.objects.get(room_id=room_id, status='completed')

        if not room:
            return JsonResponse({
                'success': False,
                'error': 'Mission not found or not completed'
            }, status=404)
        
        # Get all groups that participated in this room
        groups = Group.objects.filter(room=room).prefetch_related('groupresponse_set')
        
        # Get all questions for this quiz
        questions = Question.objects.filter(quiz=room.quiz)
        
        # Prepare report data
        report_data = {
            'room_info': {
                'room_id': room.room_id,
                'room_code': room.room_code,
                'quiz_title': room.quiz.title,
                'quiz_subject': room.quiz.subject,
                'quiz_difficulty': room.quiz.difficulty,
                'total_time': room.quiz.total_time,
                'created_at': room.created_at.isoformat(),
                'description': room.quiz.description
            },
            'summary_stats': {},
            'group_performance': [],
            'question_analysis': []
        }

        print("after report data setup")
        
        # Calculate summary statistics
        total_groups = groups.count()
        if total_groups > 0:
            avg_score = groups.aggregate(avg_score=Avg('curr_score'))['avg_score'] or 0
            avg_before_rating = groups.aggregate(avg_before=Avg('before_rating'))['avg_before'] or 0
            avg_after_rating = groups.aggregate(avg_after=Avg('after_rating'))['avg_after'] or 0
            
            report_data['summary_stats'] = {
                'total_groups': total_groups,
                'average_score': round(avg_score, 2),
                'average_before_rating': round(avg_before_rating, 2),
                'average_after_rating': round(avg_after_rating, 2),
                'rating_improvement': round(avg_after_rating - avg_before_rating, 2)
            }

        print("after summary stats calc")
        
        # Group performance details
        for group in groups:
            responses = GroupResponse.objects.filter(group=group).select_related('question')

            print("after first line...responses")
            
            # Calculate group-specific stats
            total_responses = responses.count()
            correct_responses = responses.filter(is_correct=True).count()
            accuracy = (correct_responses / total_responses * 100) if total_responses > 0 else 0
            avg_response_time = responses.aggregate(avg_time=Avg('response_time'))['avg_time'] or 0
            
            group_data = {
                'group_id': group.group_id,
                'group_name': group.name,
                'student_names': group.student_names,
                'total_score': group.curr_score,
                'before_rating': group.before_rating,
                'after_rating': group.after_rating,
                'rating_change': group.after_rating - group.before_rating,
                'accuracy_percentage': round(accuracy, 2),
                'total_responses': total_responses,
                'correct_responses': correct_responses,
                'average_response_time': round(avg_response_time, 2),
                'question_responses': []
            }

            print("after group specific stats calc")
            
            # Individual question responses for this group
            for response in responses:
                response_data = {
                    'question_id': response.question.id,
                    'question_text': response.question.question_text[:100] + '...' if len(response.question.question_text) > 100 else response.question.question_text,
                    'submitted_answer': response.submitted_answer,
                    'correct_answer': response.question.answer,
                    'is_correct': response.is_correct,
                    'points_earned': response.points_earned,
                    'max_points': response.question.points,
                    'response_time': response.response_time
                }
                group_data['question_responses'].append(response_data)
            
            report_data['group_performance'].append(group_data)

        print("after group performance calc")
        
        # Question-wise analysis
        for question in questions:
            responses = GroupResponse.objects.filter(question=question, group__room=room)
            
            total_attempts = responses.count()
            correct_attempts = responses.filter(is_correct=True).count()
            accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
            avg_response_time = responses.aggregate(avg_time=Avg('response_time'))['avg_time'] or 0
            avg_points = responses.aggregate(avg_points=Avg('points_earned'))['avg_points'] or 0
            
            question_data = {
                'question_id': question.id,
                'question_text': question.question_text,
                'correct_answer': question.answer,
                'max_points': question.points,
                'total_attempts': total_attempts,
                'correct_attempts': correct_attempts,
                'accuracy_percentage': round(accuracy, 2),
                'average_response_time': round(avg_response_time, 2),
                'average_points_earned': round(avg_points, 2),
                'difficulty_rating': 'Easy' if accuracy > 80 else 'Medium' if accuracy >= 50 else 'Hard'
            }
            
            report_data['question_analysis'].append(question_data)

            print("after question analysis calc")
        
        return JsonResponse({
            'success': True,
            'report': report_data
        })
    
    except Room.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Mission not found or not completed'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(["GET"])
def get_mission_leaderboard(request, room_id):
    """
    Get leaderboard for a specific mission (optional additional endpoint)
    """
    try:
        room = Room.objects.get(room_id=room_id, status='completed')
        
        groups = Group.objects.filter(room=room).order_by('-curr_score', 'name')
        
        leaderboard = []
        for idx, group in enumerate(groups, 1):
            total_responses = GroupResponse.objects.filter(group=group).count()
            correct_responses = GroupResponse.objects.filter(group=group, is_correct=True).count()
            accuracy = (correct_responses / total_responses * 100) if total_responses > 0 else 0
            
            leaderboard.append({
                'rank': idx,
                'group_name': group.name,
                'score': group.curr_score,
                'accuracy': round(accuracy, 2),
                'student_count': len(group.student_names),
                'student_names': list(group.student_names),
                'rating_improvement': group.after_rating - group.before_rating
            })
        
        return JsonResponse({
            'success': True,
            'leaderboard': leaderboard,
            'room_info': {
                'room_code': room.room_code,
                'quiz_title': room.quiz.title
            }
        })
    
    except Room.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Mission not found or not completed'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)