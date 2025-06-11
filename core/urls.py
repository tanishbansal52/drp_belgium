"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main.views import simple_json_view, submit_answer, join_room, give_questions, add_room, update_room_status, can_move_to_next_question, get_rooms, give_quizzes, get_room_groups, update_before_rating, update_after_rating, mark_mission_complete, get_past_missions, get_quiz_id_by_room_code, give_question_type, toggle_spinoff, get_room_spinoff, get_bonus_question, give_favourite_quizzes, toggle_quiz_favourite

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/get-room-quiz-id/<int:room_code>/', get_quiz_id_by_room_code, name='get-quiz-id-by-room-code'),
    path('api/questions/<int:n>/<int:quiz_id>/', simple_json_view, name='simple-data-api'),
    path('api/question-type/<int:n>/<int:quiz_id>/', give_question_type, name='give-question-type-api'),
    path('api/submit/', submit_answer),
    path('api/join-room/', join_room),
    path('api/questions-data/<int:quiz_id>/', give_questions, name='give-questions-api'),
    path('api/bonus-question/<int:quiz_id>/', get_bonus_question, name='give-bonus-api'),
    path('api/add-room/', add_room, name='add-room-api'),
    path('api/update-room-status/', update_room_status, name='update-room-status-api'),
    path('api/move-to-next-q/<str:room_code>/<str:curr_status>/', can_move_to_next_question, name='move-to-next-q-api'),
    path('api/get-rooms/', get_rooms, name='get-rooms-api'),
    path('api/quizzes/', give_quizzes, name='give-quizzes-api'),
    path('api/get-room-groups/<str:room_code>/', get_room_groups, name='get-room-groups-api'),
    path('api/update-before-rating/', update_before_rating, name='update-before-rating-api'),
    path('api/update-after-rating/', update_after_rating, name='update-after-rating-api'),
    path('api/mark-mission-complete/', mark_mission_complete, name='mark-mission-complete-api'),
    path('api/past-missions/', get_past_missions, name='get_past_missions'),
    path('api/toggle-spinoff/<str:room_code>/', toggle_spinoff, name='toggle-spinoff-api'),
    path('api/get-room-spinoff/<str:room_code>/', get_room_spinoff, name='get-room-spinoff-api'),
    path('api/favourite-quizzes/', give_favourite_quizzes, name='give-favourite-quizzes-api'),
    path('api/toggle-quiz-favourite/', toggle_quiz_favourite, name='toggle-quiz-favourite-api'),
]
