from django.db import models

# Create your models here.
class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Quiz(models.Model):
    title = models.TextField()
    subject = models.TextField()
    difficulty = models.TextField()
    total_time = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'quizzes'
        managed = False 

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column='quiz_id')
    question_text = models.TextField()
    answer = models.TextField()
    points = models.IntegerField()

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'questions'
        managed = False

class Room(models.Model):
    room_id = models.AutoField(primary_key=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column='quiz_id')
    room_code = models.TextField(unique=True)
    status = models.CharField(max_length=20, choices=[('waiting', 'Waiting'), ('active', 'Active'), ('finished', 'Finished')], default='waiting')
    current_question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, db_column='current_question_id')
    created_at = models.DateTimeField(auto_now_add=True)
    curr_number = models.IntegerField(default=0, db_column='curr_number')

    def __str__(self):
        return self.room_code
    
    class Meta:
        db_table = 'rooms'
        managed = False

class Group(models.Model):
    group_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, db_column='room_id', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, db_column='group_name')
    curr_score = models.IntegerField(default=0, db_column='curr_score')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'groups'
        managed = False

class GroupResponse(models.Model):
    resp_id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, db_column='group_id')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='question_id')
    submitted_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    response_time = models.IntegerField()

    def __str__(self):
        return f"Response by {self.group.name} for {self.question.question_text}"

    class Meta:
        db_table = 'responses'
        managed = False