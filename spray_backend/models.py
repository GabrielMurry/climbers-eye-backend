from django.db import models

class Movie(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='spray_backend/files/covers')

class Gym(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    type = models.CharField(max_length=20)  # 'commercial' or 'home'
    date_created = models.DateTimeField(auto_now_add=True)

class SprayWall(models.Model):
    name = models.CharField(max_length=100)
    spraywall_image_data = models.TextField()
    spraywall_image_width = models.CharField(max_length=10, default=1000)
    spraywall_image_height = models.CharField(max_length=10, default=1000)
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)

class Person(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    profile_image_data = models.TextField(blank=True)
    profile_image_width = models.CharField(max_length=10, blank=True)
    profile_image_height = models.CharField(max_length=10, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, blank=True, null=True)
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE, blank=True, null=True)

class Boulder(models.Model):
    name = models.CharField(max_length=100)
    grade = models.CharField(max_length=10)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    sends = models.IntegerField()
    boulder_image_data = models.TextField()
    boulder_image_width = models.CharField(max_length=10, default=1000)
    boulder_image_height = models.CharField(max_length=10, default=1000)
    likes_count = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE)
    # setter_person = models.ForeignKey(Person, on_delete=models.CASCADE)
    # first_ascent_person = models.ForeignKey(Person, on_delete=models.CASCADE)

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
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('person', 'boulder')