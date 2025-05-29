from django.urls import path, reverse_lazy
from .views import LoginView, SignUpView, HomeView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', SignUpView.as_view(), name='register'),
    path('home/', HomeView.as_view(), name='home'),

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='password-reset/index.html',
            success_url=reverse_lazy('password_reset_done')
        ),
        name='password_reset'
    ),

    path(
        'password-reset/sent/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password-reset-done/index.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password-reset-confirm/index.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password-reset-complete/index.html'
        ),
        name='password_reset_complete'
    ),
]
