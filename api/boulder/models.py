from django.db import models
from ..spraywall.models import SprayWall
from ..user.models import Person
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from urllib.parse import urlparse
from mypy_boto3_s3 import S3Client
import boto3
import environ
env = environ.Env()
environ.Env.read_env()
s3: S3Client = boto3.client('s3', aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'), region_name='us-west-1')

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
    alt_wall_image_url = models.TextField(blank=True, null=True, help_text='Alternative image of the default spray wall for this particular boulder.')
    alt_wall_thumbnail_url = models.TextField(blank=True, null=True, help_text='Alternative spray wall image thumbnail for boulder.')
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    # foreign keys
    spraywall = models.ForeignKey(SprayWall, on_delete=models.CASCADE)
    setter = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='set_boulders') # when the setter user deletes their account, all their boulders get deleted
    first_ascensionist = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True, related_name='first_ascended_boulders') # when the first ascensionist deletes their account, their first ascensions go to null?

# This is called if the instance of the foreign key with field is deleted. The foreign key within the boulder model must have "on_delete=models.CASCADE" 
# for it to be called since deleting the foreign key holder will cause this boulder instance to be deleted as well.
@receiver(pre_delete, sender=Boulder)
def before_deleting(instance: Boulder, **kwargs):
    print('RECEIVER: deleting.')
    parsed_url = urlparse(instance.image_url)
    s3_key = parsed_url.path.lstrip('/')
    # Delete the object from the S3 bucket
    s3.delete_object(Bucket=env('BUCKET'), Key=s3_key)
    if instance.alt_wall_image_url:
        parsed_url = urlparse(instance.alt_wall_image_url)
        s3_key = parsed_url.path.lstrip('/')
        s3.delete_object(Bucket=env('BUCKET'), Key=s3_key)