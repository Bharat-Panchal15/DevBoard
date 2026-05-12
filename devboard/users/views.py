from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from users.serializers import UserSerializer, RegisterSerializer, LoginSerializer, LogoutSerializer, OTPVerifySerializer, OTPResendSerializer
from users.permissions import IsAnonymous
from users.services import  register_user, login_user, logout_user, verify_otp, resend_otp
from users.throttles import RegisterRateThrottle, LoginRateThrottle, OTPVerifyRateThrottle, OTPResendRateThrottle

def _auth_response_serializer(name="AuthResponse"):
    return inline_serializer(
        name=name,
        fields={
            "user": UserSerializer(),
            "access": serializers.CharField(),
            "refresh": serializers.CharField(),
        }
    )

class RegisterView(APIView):
    """
    User registration endpoint.

    Methods:
    - POST /api/v1/register/ -> Create a new user account

    Permission: IsAnonymous

    Request body:
    {
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    }

    Response (201):
    {
        "detail": "OTP sent to your email. Please verify."
    }

    Validation:
    - Username cannot contain '@' or look like an email.
    - Email must be unique.
    - Password is hashed before storage.
    - User is inactive until OTP is verified.

    Notes:
    - A 6-digit OTP is generated and emitted upon successful registration.
    - Use api/v1/otp/verify/ to activate the account.
    """
    permission_classes = [IsAnonymous]
    throttle_classes = [RegisterRateThrottle]

    @extend_schema(
            tags=["Users"],
            request=RegisterSerializer,
            responses={
                201: _auth_response_serializer(name="RegisterResponse"),
                400: OpenApiResponse(description="Validation error"),
                403: OpenApiResponse(description="Already authenticated"),
            },
            summary="Register a new user",
            description="Creates a new user account and returns JWT tokens."
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            register_user(data=serializer.validated_data)

            return Response(
                {"detail": "OTP sent to your email. Please verify."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    User login endpoint.

    Methods:
    - POST /api/v1/login/ -> Authenticate user and issue tokens

    Permission: IsAnonymous

    Request body:
    {
        "identifier": "user1",   (can be username or email)
        "password": "password123"
    }

    Response:
    {
        "user": {"id": 1, "username": "user1", "email": "user1@example.com", "date_joined": "..."},
        "access": "<access_token>",
        "refresh": "<refresh_token>"
    }

    Notes:
    - Identifier can be either username or email.
    - Unverified (inactive) users cannot log in.
    - Returns 200 OK with tokens on successful login.
    """
    permission_classes = [IsAnonymous]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
            tags=["Users"],
            request=LoginSerializer,
            responses={
                200: _auth_response_serializer(name="LoginResponse"),
                400: OpenApiResponse(description="Invalid credentials"),
                403: OpenApiResponse(description="Already authenticated"),
            },
            summary="Login with username or email",
            description="Authenticate a user using username or email and returns JWT tokens."
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user, access_token, refresh_token = login_user(identifier=serializer.validated_data["identifier"], password=serializer.validated_data["password"])
            except ValueError as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
            
            user_data = UserSerializer(user, context={"request": request}).data

            return Response(
                {
                "user": user_data,
                "access": access_token,
                "refresh": refresh_token
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """
    User logout endpoint.

    Methods:
    - POST /api/v1/logout/ -> Blacklist refresh token

    Permission: IsAuthenticated

    Request body:
    {
        "refresh": "<refresh_token>"
    }

    Response: 204 No Content on success

    Notes:
    - Requires SimpleJWT token_blacklist app to be enabled in INSTALLED_APPS.
    - Blacklisting prevents token reuse after logout.
    - Access token expires naturally afeter its lifetime (15 minutes).
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
            tags=["Users"],
            request=LogoutSerializer,
            responses={
                204: OpenApiResponse(description="Logged out successfully"),
                400: OpenApiResponse(description="Invalid or expired token"),
                401: OpenApiResponse(description="Authentication required"),
            },
            summary="Logout and blacklist refresh token",
            description="Blacklists the provided refresh token, effectively logging the user out."
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        if serializer.is_valid():
            try:
                logout_user(refresh=serializer.validated_data["refresh"])
            except ValueError as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OTPVerifyView(APIView):
    """
    otp verification endpoint
    
    Methods:
    - POST /api/v1/otp/verify/ -> Verify OTP and activate user account

    Permission: IsAnonymous

    Request body:
    {
        "email": "user1@example.com",
        "code": "123456"
    }

    Response (200):
    {
        "user": {"id": 1, "username": "user1", "email": "user1@example.com", "date_joined": "..."},
        "access": "<access_token>",
        "refresh": "<refresh_token>"
    }

    Errors:
    - 400: Invalid email or code.
    - 400: OTP has expired.

    Notes:
    - OTP is valid for 10 minutes.
    - On success, user is activated and JWT tokens are returned.
    - OTP is deleted after successful verification.
    """
    
    permission_classes = [IsAnonymous]
    throttle_classes = [OTPVerifyRateThrottle]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)

        if serializer.is_valid():
            try:
                user, access, refresh = verify_otp(email=serializer.validated_data["email"], code=serializer.validated_data["code"])
            except ValueError as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
            
            user_data = UserSerializer(user, context={"request": request}).data

            return Response(
                {
                    "user": user_data,
                    "access": access,
                    "refresh": refresh
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OTPResendView(APIView):
    """
    OTP resend endpoint.

    Methods:
    - POST /api/v1/otp/resend/ -> Resend a new OTP to the user's email

    Permission: IsAnonymous

    Request body:
    {
        "email": "user1@example.com"
    }

    Response (200):
    {
        "detail": "New OTP sent to your email"
    }

    Errors:
    - 400: Email not found.
    - 400: User is already verified.

    Notes:
    - Previous OTP is deleted before generating a new one.
    - New OTP is valid for 10 minutes.
    """
    permission_classes = [IsAnonymous]
    throttle_classes = [OTPResendRateThrottle]

    def post(self, request):
        serializer = OTPResendSerializer(data=request.data)

        if serializer.is_valid():
            try:
                resend_otp(email=serializer.validated_data["email"])
            except ValueError as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(
                {"detail": "New OTP sent to your email"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)