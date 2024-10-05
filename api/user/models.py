from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from ..gym.models import Gym

class PersonManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class Person(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=50, unique=True)
    image_url = models.TextField(blank=True)
    image_width = models.CharField(max_length=10, blank=True)
    image_height = models.CharField(max_length=10, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    # foreign keys
    gym = models.ForeignKey(Gym, on_delete=models.SET_NULL, blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = PersonManager()

    def __str__(self):
        return self.username