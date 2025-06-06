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
from main.views import simple_json_view, submit_answer, join_room, give_questions, add_room, update_room_status, can_move_to_next_question, get_rooms, give_quizzes, get_room_groups

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/questions/<int:n>/', simple_json_view, name='simple-data-api'),
    path('api/submit/', submit_answer),
    path('api/join-room/', join_room),
    path('api/questions', give_questions, name='give-questions-api'),
    path('api/add-room/', add_room, name='add-room-api'),
    path('api/update-room-status/', update_room_status, name='update-room-status-api'),
    path('api/move-to-next-q/<str:room_code>/<str:curr_status>/', can_move_to_next_question, name='move-to-next-q-api'),
    path('api/get-rooms/', get_rooms, name='get-rooms-api'),
    path('api/quizzes/', give_quizzes, name='give-quizzes-api'),
    path('api/get-room-groups/<str:room_code>/', get_room_groups, name='get-room-groups-api'),
]
