from django.urls import path
from .views import QuestionAndAnswerCreate, MyQuestion, MyAnswer

urlpatterns = [
    path("question-answer-create/", QuestionAndAnswerCreate.as_view()),
    path("question-list/", MyQuestion.as_view()),
    path("answer-list/", MyAnswer.as_view()),
]
