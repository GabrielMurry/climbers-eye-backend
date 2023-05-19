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
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)

# class Person(models.Model):
#     useranme = models.CharField(max_length=100)
#     email = models.EmailField(max_length=100)
#     # password


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
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE)
    # setter_person = models.ForeignKey(Person, on_delete=models.CASCADE)
    # first_ascent_person = models.ForeignKey(Person, on_delete=models.CASCADE)