from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "date_joined",
            "is_active",
            "is_staff",
        ]
        # extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value):
        print(f"Validating password: {value}")
        if not isinstance(value, str):
            raise serializers.ValidationError("Password must be a string.")
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        return value

    def validate_username(self, value):
        print(f"Validating username: {value}")
        if not isinstance(value, str):
            raise serializers.ValidationError("Username must be a string.")
        if value.isdigit():
            raise serializers.ValidationError("Username cannot be purely numeric.")
        return value

    def validate_email(self, value):
        print(f"Validating email: {value}")
        if not isinstance(value, str):
            raise serializers.ValidationError("Email must be a string.")
        if "@" not in value or "." not in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value

    def create(self, validated_data):
        required_fields = ["username", "password"]
        missing_fields = [
            field for field in required_fields if field not in validated_data
        ]

        if missing_fields:
            raise serializers.ValidationError(
                {field: "This field is required." for field in missing_fields}
            )

        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            is_staff=False,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.is_staff = validated_data.get("is_staff", instance.is_staff)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        password = validated_data.get("password", None)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
