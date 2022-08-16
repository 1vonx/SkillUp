"""skillup_courses_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path, include
from skillup import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.StudentSignUpView.as_view(), name='signup'),
    path('login_form/', views.login_form, name='login_form'),
    path('login/', views.loginView, name='login'),
    path('logout/', views.logoutView, name='logout'),
    path('courses/', views.allCourses, name='courses'),
    path('courses/<int:pk>', views.course_detail, name='course-detail'),
    path('courses/<int:course_pk>/lecture/<int:lecture_pk>', views.lecture_detail, name='lecture-detail'),
    path('listnotes/', views.NotesListView.as_view(), name='notes'),
    path('courses/<int:pk>/notes', views.notes_course, name='notes-course'),
    path('add_notes/', views.add_notes, name='add-notes'),
    path('publish_notes/', views.publish_notes, name='publish_notes'),
    path('note/<int:pk>/delete/', views.NoteDeleteView.as_view(), name='note_delete'),
    path('quiz/<int:pk>', views.take_quiz, name='take_quiz'),
    path('taken/', views.TakenQuizListView.as_view(), name='taken_quiz_list'),
    path('quiz/<int:pk>/retake/', views.retake_quiz, name='retake_quiz'),
    path('certificate/<int:pk>', views.get_certificate, name='get_certificate'),
]
