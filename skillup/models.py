from django.contrib.auth.models import AbstractUser
from django.db import models
from embed_video.fields import EmbedVideoField
from django.urls import reverse


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)


class Quiz(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=30)
    thumbnail = models.ImageField(upload_to="course_thumb/", null=True, blank=True)
    num_lectures = models.CharField(max_length=50, null=True, blank=True)
    estimated_time = models.CharField(max_length=50, null=True, blank=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='quiz')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def get_url(self):
        return reverse('course-detail', args=[self.id])


class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default='')
    title = models.CharField(max_length=50)
    content = models.TextField()
    video = EmbedVideoField(blank=True, null=True)
    yt_link = models.URLField(max_length=500, null=True, blank=True)


class Notes(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField(null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Question', max_length=255)

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField('Answer', max_length=255)
    is_correct = models.BooleanField('Correct answer', default=False)

    def __str__(self):
        return self.text


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    quizzes = models.ManyToManyField(Quiz, through='TakenQuiz')

    def get_unanswered_questions(self, quiz):
        answered_questions = self.quiz_answers \
            .filter(answer__question__quiz=quiz) \
            .values_list('answer__question__pk', flat=True)
        questions = quiz.questions.exclude(pk__in=answered_questions).order_by('text')
        return questions

    def __str__(self):
        return self.user.username


class TakenQuiz(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='taken_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='taken_quizzes')
    score = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='+')
