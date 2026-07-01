from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterView, ProfileView, ChangePasswordView, LogoutView, ConfigurationEmailView, \
    ForgotPasswordView, VerifyResetCodeView, ResetPasswordView

urlpatterns = [
    path('register/',        RegisterView.as_view(),       name='register'),
    path('login/',           TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/',   TokenRefreshView.as_view(),   name='token_refresh'),
    path('logout/',          LogoutView.as_view(),          name='logout'),
    path('profile/',         ProfileView.as_view(),         name='profile'),
    path('change-password/', ChangePasswordView.as_view(),  name='change_password'),
    path('config-email/', ConfigurationEmailView.as_view()),
    path('forgot-password/',    ForgotPasswordView.as_view()),
    path('verify-reset-code/',  VerifyResetCodeView.as_view()),
    path('reset-password/',     ResetPasswordView.as_view()),
]