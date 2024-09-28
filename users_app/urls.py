from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterAPIView, LoginAPIView,
    ProfileAPIView, LogoutView,
    NotesAPIView, CustomUsersAPIView,
    VerifyAPIView, TabAPIView,
    FirebaseSocialAuthAPIView,
)

urlpatterns = [
    path('all/', CustomUsersAPIView.as_view()),
    path('register/', RegisterAPIView.as_view()),
    path('verify/', VerifyAPIView.as_view()),
    path('login/', LoginAPIView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('profile/', ProfileAPIView.as_view()),
    path('tabs/', TabAPIView.as_view()),
    path('notes/', NotesAPIView.as_view()),
    path('notes/tab/', TabAPIView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('firebase-auth/', FirebaseSocialAuthAPIView.as_view()),
]
