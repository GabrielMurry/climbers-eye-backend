from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class Gym(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    place_id = models.CharField(max_length=255, unique=True, blank=True, null=True) 
    type = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)

class SprayWall(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.TextField() 
    image_width = models.CharField(max_length=10, default=1000)
    image_height = models.CharField(max_length=10, default=1000)
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, blank=True, null=True)

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

class Boulder(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    matching = models.BooleanField(default=True)
    publish = models.BooleanField(default=True)
    feet_follow_hands = models.BooleanField(default=True) 
    kickboard_on = models.BooleanField(default=False) 
    grade = models.PositiveIntegerField(blank=True, null=True)
    quality = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    sends_count = models.PositiveIntegerField(default=0)
    image_url = models.TextField()
    image_width = models.CharField(max_length=10, default=1000)
    image_height = models.CharField(max_length=10, default=1000)
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    # foreign keys
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE)
    setter = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='set_boulders') # when the setter user deletes their account, all their boulders get deleted
    first_ascensionist = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True, related_name='first_ascended_boulders') # when the first ascensionist deletes their account, their first ascensions go to null?

class Circuit(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, blank=True)
    private = models.BooleanField(default=False)
    boulders = models.ManyToManyField(Boulder, related_name='circuits') # Django automatically creates indexes for Many-to-Many fields
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE, db_index=True) # who this circuit belongs to
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE, blank=True, null=True) # which spraywall the circuit belongs to 

class Like(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE)
    # the unique_together attribute in the Meta class ensures that a person can only like a particular boulder once. If they try to like the same boulder again, it will raise a unique constraint violation error.
    class Meta:
        unique_together = ('person', 'boulder')

# tracking person's sends (successful climbs/ascents)
class Send(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    attempts = models.SmallIntegerField(default=1) # attempts are 1 - 100 so we can definitely use smallintegerfield
    suggested_grade = models.PositiveIntegerField(blank=True, null=True) 
    quality = models.SmallIntegerField(default=3)
    notes = models.TextField(blank=True, null=True)
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE, db_index=True)
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['person', 'boulder']),
        ]

class Bookmark(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE)
    # the unique_together attribute in the Meta class ensures that a person can only like a particular boulder once. If they try to like the same boulder again, it will raise a unique constraint violation error.
    class Meta:
        unique_together = ('person', 'boulder')

class Activity(models.Model):
    date_created = models.DateTimeField(auto_now_add=True) # date
    action = models.CharField(max_length=50)
    item = models.CharField(max_length=50, blank=True, null=True)
    other_info = models.CharField(max_length=100, blank=True, null=True)
    # foreign keys
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE, blank=True, null=True) # required
    person = models.ForeignKey(Person, on_delete=models.CASCADE) # required
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE, blank=True, null=True) # optional
    bookmark = models.ForeignKey(Bookmark, on_delete=models.CASCADE, blank=True, null=True) # optional
    like = models.ForeignKey(Like, on_delete=models.CASCADE, blank=True, null=True) # optional
    send = models.ForeignKey(Send, on_delete=models.CASCADE, blank=True, null=True) # optional
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE, blank=True, null=True) # optional