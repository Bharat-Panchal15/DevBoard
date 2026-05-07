from django.urls import path
from users.views import RegisterView, LoginView, LogoutView, OTPVerifyView, OTPResendView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("otp/resend/", OTPResendView.as_view(), name="otp-resend"),
]