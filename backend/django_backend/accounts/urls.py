from django.urls import path
from .views import LoginView, SignUpView, HomeView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', SignUpView.as_view(), name='register'),
    path('home/', HomeView.as_view(), name='home'),
]