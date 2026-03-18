from rest_framework import serializers
from django.contrib.auth import get_user_model
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