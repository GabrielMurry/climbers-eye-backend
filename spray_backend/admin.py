from django.contrib import admin
from .models import Gym

class GymAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)

admin.site.register(Gym, GymAdmin)