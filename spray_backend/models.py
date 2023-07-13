from django.db import models

class Movie(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='spray_backend/files/covers')

class Gym(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=20)  # 'commercial' or 'home'
    date_created = models.DateTimeField(auto_now_add=True)

class SprayWall(models.Model):
    name = models.CharField(max_length=100)
    spraywall_image_url = models.TextField()
    spraywall_image_width = models.CharField(max_length=10, default=1000)
    spraywall_image_height = models.CharField(max_length=10, default=1000)
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, blank=True, null=True)

class Person(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    headshot_image_url = models.TextField(blank=True)
    headshot_image_width = models.CharField(max_length=10, blank=True)
    headshot_image_height = models.CharField(max_length=10, blank=True)
    banner_image_url = models.TextField(blank=True)
    banner_image_width = models.CharField(max_length=10, default=1000, blank=True)
    banner_image_height = models.CharField(max_length=10, default=1000, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, blank=True, null=True)

class Boulder(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    matching = models.BooleanField(default=True)
    publish = models.BooleanField(default=True)
    grade = models.CharField(max_length=10, blank=True, null=True)
    quality = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True) # decimalfield rather than smallintegerfield because we want to find the average quality rating for each boulder
    sends_count = models.IntegerField(default=0)
    boulder_image_url = models.TextField()
    boulder_image_width = models.CharField(max_length=10, default=1000)
    boulder_image_height = models.CharField(max_length=10, default=1000)
    likes_count = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE, blank=True, null=True)
    setter_person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='setter_person')
    first_ascent_person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='first_ascent_person')

class Circuit(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    private = models.BooleanField(default=False)
    boulders = models.ManyToManyField(Boulder, related_name='circuits')
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE) # who this circuit belongs to
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
    grade = models.CharField(max_length=10, blank=True, null=True) 
    quality = models.SmallIntegerField(default=3)
    notes = models.TextField(blank=True, null=True)
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('person', 'boulder')

class Bookmark(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    # foreign keys
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    boulder = models.ForeignKey(Boulder, on_delete=models.CASCADE)
    # the unique_together attribute in the Meta class ensures that a person can only like a particular boulder once. If they try to like the same boulder again, it will raise a unique constraint violation error.
    class Meta:
        unique_together = ('person', 'boulder')


class Cat(models.Model):
    name = models.CharField(max_length=30)
    picture = models.FileField(upload_to='media/')