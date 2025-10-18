from .models import Folder, File
from rest_framework import serializers
from .models import CustomUser, Role
from django.contrib.auth import authenticate, get_user_model
User = get_user_model()


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = [
            'id',
            'name',
            'token',
            'parent',
            'created_at',
            'updated_at',
        ]


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'id',
            'name',
            'token',
            'file',
            'folder',
            'file_type',
            'size',
            'created_at',
            'updated_at',
        ]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "role_name", "privileges"]


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "password", "role"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Неверный email или пароль")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.role_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "role_name", "created_at", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def update(self, instance, validated_data):
        role_data = validated_data.pop('role', None)

        # если пришел id
        if isinstance(role_data, int):
            instance.role = Role.objects.get(id=role_data)
        # если пришел объект Role (например, при сериализации)
        elif isinstance(role_data, Role):
            instance.role = role_data

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

