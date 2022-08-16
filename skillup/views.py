from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView
from utils import render_to_pdf
from .forms import TakeQuizForm, StudentSignUpForm
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import auth
from .models import TakenQuiz, Quiz, StudentAnswer, User, Course, Lecture, Notes
from django.db import transaction


def home(request):
    return render(request, 'home.html')


def login_form(request):
    return render(request, 'login.html')


def logoutView(request):
    logout(request)
    return redirect('home')


def loginView(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            if user.is_admin or user.is_superuser:
                return redirect('admin')
            else:
                return redirect('courses')
        else:
            messages.info(request, "Invalid Username or Password")
            return redirect('login_form')


def allCourses(request):
    courses = Course.objects.order_by('id')

    # filter courses by search query
    query = request.GET.get('q')
    if query:
        courses = courses.filter(name__icontains=query)

    paginator = Paginator(courses, 4)
    page = request.GET.get('page')
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        queryset = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        queryset = paginator.page(paginator.num_pages)

    context = {
        "courses": queryset,
    }

    return render(request, "courses.html", context)


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    lectures = Lecture.objects.filter(course_id=pk)

    context = {
        "course": course,
        "lectures": lectures,
    }

    return render(request, "course.html", context)


def lecture_detail(request, course_pk, lecture_pk):
    course = get_object_or_404(Course, pk=course_pk)
    lectures = Lecture.objects.filter(course_id=course_pk)
    lecture = get_object_or_404(Lecture, pk=lecture_pk, course=course)

    context = {
        "course": course,
        "lectures": lectures,
        "lecture": lecture,
    }

    return render(request, "lecture.html", context)


class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'signup.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('home')


class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .order_by('quiz_id')
        return queryset


def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    student = request.user.student

    if student.quizzes.filter(pk=pk).exists():
        return redirect('taken_quiz_list')

    total_questions = quiz.questions.count()
    unanswered_questions = student.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=False)
                student_answer.student = student
                student_answer.save()
                if student.get_unanswered_questions(quiz).exists():
                    return redirect('take_quiz', pk)
                else:
                    correct_answers = student.quiz_answers.filter(answer__question__quiz=quiz,
                                                                  answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(student=student, quiz=quiz, score=score)
                    if score < 80.0:
                        messages.warning(request, 'Better luck next time! Your score for the quiz %s was %s.' % (quiz.name, score))
                    else:
                        messages.success(request, 'Congratulations! Your score for the quiz %s was %s.' % (quiz.name, score))
                    return redirect('taken_quiz_list')
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })


def retake_quiz(request, pk):
    student = request.user.student
    TakenQuiz.objects.get(quiz_id=pk).delete()
    StudentAnswer.objects.filter(student=student).delete()

    return redirect('take_quiz', pk)


class NotesListView(ListView):
    model = Notes
    template_name = 'notes.html'
    context_object_name = 'notes'
    paginate_by = 4

    def get_queryset(self):
        return Notes.objects.filter(user=self.request.user).order_by('-id')


class NoteDeleteView(DeleteView):
    model = Notes
    context_object_name = 'note'
    template_name = 'note_delete_confirm.html'
    success_url = reverse_lazy('notes')

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Notes.objects.filter(user=self.request.user)


def notes_course(request, pk):
    user = request.user
    course = get_object_or_404(Course, pk=pk)
    notes = Notes.objects.filter(course_id=pk, user=user)
    paginator = Paginator(notes, 4)
    page = request.GET.get('page')
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        queryset = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        queryset = paginator.page(paginator.num_pages)
    context = {'notes': queryset, 'course': course}

    return render(request, 'notes-course.html', context)


def add_notes(request):
    courses = Course.objects.only('id', 'name')
    context = {'courses': courses}
    return render(request, 'add-notes.html', context)


def publish_notes(request):
    if request.method == 'POST':
        title = request.POST['title']
        course_id = request.POST['course_id']
        content = request.POST['content']
        current_user = request.user
        user_id = current_user.id

        a = Notes(title=title, user_id=user_id, content=content, course_id=course_id)
        a.save()
        return redirect('notes')
    else:
        messages.error = (request, 'Note Was Not Added Successfully')
        return redirect('add-notes')


def get_certificate(request, pk):
    template = get_template('certificate.html')
    student = request.user.username
    taken = get_object_or_404(TakenQuiz, pk=pk)
    quiz = Quiz.objects.get(id=taken.quiz.id)
    course = Course.objects.get(quiz=quiz)
    context = {"student": student, "course": course.name, "score": taken.score, "date": taken.date, }
    html = template.render(context)
    pdf = render_to_pdf('certificate.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = 'Certificate_%s.pdf' % course.name
        content = "inline; filename=%s" % filename
        download = request.GET.get("download")
        if download:
            content = "attachment; filename='%s'" % filename
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Not found")

