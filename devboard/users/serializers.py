from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model, authenticate
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "date_joined"]
        read_only_fields = ["date_joined"]

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_username(self, username):
        """Ensure username doesn't contain '@' or email patterns."""
        if re.match(r".+@.+\..+",username): # Pattern: something@something.something
            raise serializers.ValidationError("Username cannot look like an email")
        
        if "@" in username:
            raise serializers.ValidationError("Username cannot contain '@' symbol")
        
        return username.strip()

    def validate_email(self, email):
        """Ensure email is unique."""
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email is already taken")
        
        return email.strip()
    
    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(**validated_data, password=password)

        return user

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data.get("identifier")
        password = data.get("password")

        if not identifier or not password:
            raise serializers.ValidationError("Both credentials are required.")
        
        if "@" in identifier:
            user = User.objects.filter(email=identifier).first()
            if not user:
                raise serializers.ValidationError("Invalid login credentials")
            username = user.username
        else:
            username = identifier

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid login credentials")
        
        data["user"] = user
        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        self.token = data["refresh"]
        return data
    
    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError("Invalid or expired token")