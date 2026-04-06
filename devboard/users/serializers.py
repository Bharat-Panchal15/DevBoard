from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "date_joined"]
        read_only_fields = ["date_joined"]

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

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
            raise serializers.ValidationError("User already exists")
        
        return email.strip()

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()