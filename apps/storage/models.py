import uuid
import secrets
import os
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, username=None, role=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, username=None, role=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, username, role, **extra_fields)


class Role(models.Model):
    ROLE_CHOICES = [
        ('SuperUser', 'Супер Пользователь'),
        ('Admin', 'Админ'),
        ('User', 'Пользователь'),
    ]
    role_name = models.CharField(max_length=255, verbose_name='Название роли', choices=ROLE_CHOICES, default='Waiter')

    privileges = models.JSONField(verbose_name='Привилегии', default=dict, blank=True, null=True)

    def __str__(self):
        return self.role_name

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    username = models.CharField(max_length=255, verbose_name='Имя пользователя', blank=True, null=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Роль",
        default=None
    )
    created_at = models.DateTimeField(verbose_name="Дата создания аккаунта", auto_now_add=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


def generate_secure_token(length=32):
    """Генерация криптографически стойкого токена"""
    return secrets.token_urlsafe(length)


class Folder(models.Model):
    """
    Модель папки (иерархическая структура)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    token = models.CharField(max_length=128, unique=True, default=generate_secure_token, db_index=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subfolders',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class File(models.Model):
    """
    Модель файла (аудио, видео, документы и т.д.)
    """
    FILE_TYPES = (
        ('audio', 'audio'),
        ('video', 'video'),
        ('document', 'document'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    token = models.CharField(max_length=128, unique=True, default=generate_secure_token, db_index=True)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='files',
        null=True,
        blank=True
    )
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    size = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Автоматически вычисляем размер файла при сохранении"""
        if self.file and not self.size:
            try:
                self.size = self.file.size
            except Exception:
                pass

        # если имя пустое — используем имя файла
        if not self.name and self.file:
            self.name = os.path.basename(self.file.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.file_type})"


class FileUploadSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True)
    upload_id = models.CharField(max_length=100, unique=True, db_index=True)
    total_chunks = models.IntegerField()
    received_chunks = models.IntegerField(default=0)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.file_name or 'unnamed'} ({self.received_chunks}/{self.total_chunks})"


